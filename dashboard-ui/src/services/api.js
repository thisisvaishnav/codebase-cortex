/**
 * API service communicating with TrueForge daemon (:8790) and Cortex Vector MCP (:9001).
 */

const VECTOR_BASE = 'http://localhost:9001';
const TRUEFORGE_BASE = 'http://localhost:8790/api/v1';

export async function checkTrueForgeHealth() {
  try {
    const res = await fetch(`${TRUEFORGE_BASE}/capabilities`, { method: 'GET' });
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` };
    const data = await res.json();
    return { ok: true, data };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

export async function checkVectorHealth() {
  try {
    const res = await fetch(`${VECTOR_BASE}/api/health`, { method: 'GET' });
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` };
    const data = await res.json();
    return { ok: true, data };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

export async function explainQuery(question, paths = null) {
  try {
    const res = await fetch(`${VECTOR_BASE}/api/explain`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ question, paths }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return {
      answer: `**Error connecting to Cortex server:** ${err.message}`,
      lineage: [],
      candidates: [],
      error: err.message,
    };
  }
}

export async function fetchListDecisions(includeSuperseded = true) {
  try {
    const res = await fetch(`${VECTOR_BASE}/api/decisions?include_superseded=${includeSuperseded}`, {
      method: 'GET',
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('fetchListDecisions error:', err);
    return [];
  }
}

export async function traceLineage(adrId) {
  try {
    const res = await fetch(`${VECTOR_BASE}/api/lineage/${encodeURIComponent(adrId)}`, {
      method: 'GET',
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('traceLineage error:', err);
    return { chain: [] };
  }
}

export async function createSession(agentName = 'codebase-cortex') {
  const res = await fetch(`${TRUEFORGE_BASE}/sessions`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ agent: { name: agentName } }),
  });
  if (!res.ok) throw new Error(`POST /sessions -> HTTP ${res.status}`);
  return await res.json();
}

export async function postTurn(sessionId, userMessage) {
  const res = await fetch(`${TRUEFORGE_BASE}/sessions/${sessionId}/turns`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      input: [{ type: 'user.message', content: userMessage }],
      stream: false,
    }),
  });
  if (!res.ok) throw new Error(`POST /turns -> HTTP ${res.status}`);
  return await res.json();
}
