# ADR-002: Redis for Distributed Session Persistence

**Status:** ACTIVE  
**Date:** 2026-05-15  
**Author:** @senior-dev  
**Merged in PR:** #89  

## Context
Our application previously evaluated in-memory local caching vs PostgreSQL session tables vs Redis.

## Decision
We choose **Redis Cluster** for session persistence and fast distributed caching.

## Rationale
1. **Pod Resilience:** In Kubernetes, application pods are frequently rescheduled or autoscaled. Local in-memory caching causes immediate session drop upon container restart.
2. **Performance:** Under load testing with 10k concurrent active sessions, Postgres experienced connection pool exhaustion, while Redis maintained sub-2ms response latency.

## Invariant
- **Rule:** Session state and token blacklists MUST never be stored in process memory. They MUST be stored in the shared Redis cache layer.
