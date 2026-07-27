# Build-Time Validation Standards

Every API release must produce evidence for outcome alignment, specification, lean design,
security, NoSQL integrity, observability, testing, health, AI governance, and lifecycle controls.

## Mandatory release gates

1. Approved API specification and owner.
2. Standard error and compatibility policy.
3. Object-level authorization and actor/subject policy.
4. Idempotency and integrity controls for commands.
5. Outbox/inbox, projection freshness, and reconciliation for distributed NoSQL entities.
6. Trace, correlation, business-transaction, audit, and data-version evidence.
7. Contract, authorization, and failure-path tests.
8. Health endpoints for liveness, readiness, dependencies, capabilities, and business impact.
9. MCP and A2A controls when enabled.
10. Minimum risk-tier score and no blocking findings.

## Integrity states

`CONSISTENT`, `CONVERGING`, `DRIFT_DETECTED`, `REPAIRING`, `MANUAL_REVIEW_REQUIRED`.
