# Issue #45: Proposal to replace Redis session store with local dict cache

**Proposer:** @contributor-dev  
**Type:** Architectural Proposal / Refactor  

## Description
Currently, our session store calls out to `redis-cluster.internal`. Under high load or local development, configuring Redis adds extra deployment overhead.

I propose replacing `src/cache/session.py` with an in-process Python `dict` guarded by a thread lock. This reduces sub-2ms network latencies down to sub-0.01ms and simplifies local developer setup.

## Impacted Modules
- `src/cache/session.py`
- `src/api/auth.py`
