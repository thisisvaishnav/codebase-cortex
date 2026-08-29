# ADR-003: Asynchronous Event Bus for Billing & Notifications

**Status:** ACTIVE  
**Date:** 2026-06-20  
**Author:** @lead-maintainer  
**Merged in PR:** #112  

## Context
Synchronous HTTP webhooks caused cascade timeouts when payment providers experienced degraded response times.

## Decision
Use an asynchronous message queue (Event Bus) with retry exponential backoff for billing events and email notifications.

## Rationale
Decouples user-facing request cycles from slow third-party webhook APIs, preventing 504 Gateway Timeouts.

## Invariant
- **Rule:** Billing and notification side-effects MUST be emitted as events and processed asynchronously.
