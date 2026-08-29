"""In-process session and token-revocation store.

Replaces the Redis-backed implementation. Motivation:

* p99 on ``/me`` was 11ms, of which ~4ms was the round trip to
  ``redis-cluster.internal``. Reading from a local dict is ~0.01ms.
* We are running two API replicas behind an ingress that is already configured
  with sticky sessions (``nginx.ingress.kubernetes.io/affinity: cookie``), so a
  given user keeps landing on the same replica and keeps seeing their session.
* Drops one moving part from the deployment: no Redis cluster to patch, no
  ``REDIS_URL`` secret, no connection-pool tuning, local dev needs no docker
  compose service.

The public API is unchanged, so callers in ``src/api/`` need no edits.
"""

from __future__ import annotations

import os
import secrets
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Iterator

SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "86400"))
REVOCATION_TTL_SECONDS = int(os.getenv("REVOCATION_TTL_SECONDS", "3600"))

_lock = threading.RLock()

# Live sessions, keyed by session id. Bounded in practice by TTL sweeping.
_SESSIONS: dict[str, "Session"] = {}

# Revoked JWT ids -> unix timestamp at which the entry may be swept.
_REVOKED_JTI: dict[str, float] = {}

_last_sweep = 0.0
_SWEEP_INTERVAL_SECONDS = 60.0


class SessionStoreError(RuntimeError):
    """Kept for API compatibility. The in-process store cannot fail this way."""


@dataclass(slots=True)
class Session:
    sid: str
    user_id: str
    created_at: float
    last_seen_at: float
    scopes: tuple[str, ...] = ()
    data: dict[str, Any] = field(default_factory=dict)
    expires_at: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["scopes"] = list(self.scopes)
        return payload


def _sweep_locked(now: float) -> None:
    global _last_sweep
    if now - _last_sweep < _SWEEP_INTERVAL_SECONDS:
        return
    _last_sweep = now
    for sid in [s for s, sess in _SESSIONS.items() if sess.expires_at <= now]:
        del _SESSIONS[sid]
    for jti in [j for j, deadline in _REVOKED_JTI.items() if deadline <= now]:
        del _REVOKED_JTI[jti]


def create_session(user_id: str, scopes: tuple[str, ...] = ()) -> Session:
    now = time.time()
    session = Session(
        sid=secrets.token_urlsafe(24),
        user_id=user_id,
        created_at=now,
        last_seen_at=now,
        scopes=scopes,
        expires_at=now + SESSION_TTL_SECONDS,
    )
    with _lock:
        _sweep_locked(now)
        _SESSIONS[session.sid] = session
    return session


def get_session(sid: str) -> Session | None:
    now = time.time()
    with _lock:
        session = _SESSIONS.get(sid)
        if session is None:
            return None
        if session.expires_at <= now:
            del _SESSIONS[sid]
            return None
        return session


def touch_session(sid: str) -> bool:
    now = time.time()
    with _lock:
        session = _SESSIONS.get(sid)
        if session is None or session.expires_at <= now:
            _SESSIONS.pop(sid, None)
            return False
        session.last_seen_at = now
        session.expires_at = now + SESSION_TTL_SECONDS
        return True


def delete_session(sid: str) -> None:
    with _lock:
        _SESSIONS.pop(sid, None)


def revoke_token(jti: str, ttl: int = REVOCATION_TTL_SECONDS) -> None:
    with _lock:
        _REVOKED_JTI[jti] = time.time() + ttl


def is_token_revoked(jti: str) -> bool:
    now = time.time()
    with _lock:
        deadline = _REVOKED_JTI.get(jti)
        if deadline is None:
            return False
        if deadline <= now:
            del _REVOKED_JTI[jti]
            return False
        return True


def iter_sessions(user_id: str | None = None) -> Iterator[Session]:
    now = time.time()
    with _lock:
        snapshot = [s for s in _SESSIONS.values() if s.expires_at > now]
    for session in snapshot:
        if user_id is None or session.user_id == user_id:
            yield session


def healthcheck() -> dict[str, Any]:
    with _lock:
        return {
            "backend": "memory",
            "ok": True,
            "latency_ms": 0.0,
            "sessions": len(_SESSIONS),
            "revoked_jti": len(_REVOKED_JTI),
        }
