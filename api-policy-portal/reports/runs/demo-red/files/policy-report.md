# API Policy Validation: disconnect-screen-api

> 🔴 **RED — REJECTED - RELEASE BLOCKED**

- **Policy repository version:** 3.0.0
- **Risk tier:** high
- **Weighted score:** 8.5/100
- **Required score:** 90.0

## Dimension traffic lights

| Light | Dimension | Owner | Score | Weight | Gates | Failed gates |
|---|---|---|---:|---:|---:|---|
| 🔴 RED | Business outcome and capability alignment | Enterprise Architecture | 60.0% | 10.0 | 3/5 | OUT-003, OUT-005 |
| 🔴 RED | Specification and data-contract quality | API Platform | 0.0% | 15.0 | 0/5 | SPEC-001, SPEC-002, SPEC-003, SPEC-004, SPEC-005 |
| 🔴 RED | Lean API and resource design | API Design Council | 0.0% | 10.0 | 0/6 | LEAN-001, LEAN-002, LEAN-003, LEAN-004, LEAN-005, LEAN-006 |
| 🔴 RED | Security and role-aware authorization | Security Architecture | 0.0% | 15.0 | 0/6 | SEC-001, SEC-002, SEC-003, SEC-004, SEC-005, SEC-006 |
| 🔴 RED | NoSQL transactional and data integrity | Data and Domain Architecture | 0.0% | 15.0 | 0/9 | INT-001, INT-002, INT-003, INT-004, INT-005, INT-006, INT-007, INT-008, INT-009 |
| 🔴 RED | Cross-layer observability and auditability | SRE and Observability | 0.0% | 10.0 | 0/6 | OBS-001, OBS-002, OBS-003, OBS-004, OBS-005, OBS-006 |
| 🔴 RED | Testing automation and mock coverage | Quality Engineering | 0.0% | 10.0 | 0/4 | TEST-001, TEST-002, TEST-003, TEST-004 |
| 🔴 RED | Health and business-impact exposure | SRE and Operations | 0.0% | 5.0 | 0/6 | HLTH-001, HLTH-002, HLTH-003, HLTH-004, HLTH-005, HLTH-006 |
| 🔴 RED | AI, MCP, and Agent-to-Agent governance | AI Platform Governance | 50.0% | 5.0 | 1/2 | AI-001 |
| 🔴 RED | Lifecycle, versioning, and reuse | API Product Management | 0.0% | 5.0 | 0/4 | LIFE-001, LIFE-002, LIFE-003, LIFE-004 |

## Gate findings

| Rule | Dimension | Severity | Blocking | Finding |
|---|---|---|---|---|
| OUT-003 | outcome_capability | HIGH | No | Business owner is defined |
| OUT-005 | outcome_capability | HIGH | No | At least one consumer is identified |
| SPEC-001 | specification_contract | CRITICAL | Yes | OpenAPI file exists |
| SPEC-002 | specification_contract | CRITICAL | Yes | OpenAPI structure is valid |
| SPEC-003 | specification_contract | HIGH | No | Backward compatibility is declared |
| SPEC-004 | specification_contract | HIGH | No | Standard error model is declared |
| SPEC-005 | specification_contract | CRITICAL | Yes | Security scheme is declared |
| LEAN-001 | lean_resource_design | HIGH | No | API is resource-oriented |
| LEAN-002 | lean_resource_design | HIGH | No | API is not screen-specific |
| LEAN-003 | lean_resource_design | HIGH | No | Collection and detail access are separated |
| LEAN-004 | lean_resource_design | HIGH | No | Payload is right-sized |
| LEAN-005 | lean_resource_design | HIGH | No | API is reusable |
| LEAN-006 | lean_resource_design | HIGH | No | Paths avoid UI and database implementation terms |
| SEC-001 | security_authorization | CRITICAL | Yes | Authentication is configured |
| SEC-002 | security_authorization | CRITICAL | Yes | Object-level authorization is required |
| SEC-003 | security_authorization | HIGH | No | Actor/subject model is defined |
| SEC-004 | security_authorization | HIGH | No | Policy-as-code is enabled |
| SEC-005 | security_authorization | HIGH | No | Acting modes are declared |
| SEC-006 | security_authorization | CRITICAL | Yes | OpenAPI declares security requirements |
| INT-001 | nosql_integrity | CRITICAL | Yes | NoSQL integrity control set is complete |
| INT-002 | nosql_integrity | CRITICAL | Yes | Idempotency is enabled |
| INT-003 | nosql_integrity | HIGH | No | Aggregate owner is declared |
| INT-004 | nosql_integrity | HIGH | No | Single-writer rule is declared |
| INT-005 | nosql_integrity | HIGH | No | Concurrency-control mechanism is declared |
| INT-006 | nosql_integrity | HIGH | No | Outbox/inbox reliability is enabled |
| INT-007 | nosql_integrity | HIGH | No | Projection freshness is measured |
| INT-008 | nosql_integrity | HIGH | No | Reconciliation is defined |
| INT-009 | nosql_integrity | HIGH | No | Saga or compensation is defined |
| OBS-001 | observability_audit | HIGH | No | Trace propagation is enabled |
| OBS-002 | observability_audit | HIGH | No | Correlation ID is enabled |
| OBS-003 | observability_audit | HIGH | No | Business transaction ID is enabled |
| OBS-004 | observability_audit | HIGH | No | Structured logging is enabled |
| OBS-005 | observability_audit | CRITICAL | Yes | Audit events are enabled |
| OBS-006 | observability_audit | HIGH | No | Required observability headers exist in OpenAPI |
| TEST-001 | testing_mocking | CRITICAL | Yes | Contract tests exist |
| TEST-002 | testing_mocking | CRITICAL | Yes | Authorization tests exist |
| TEST-003 | testing_mocking | HIGH | No | Failure-path tests exist |
| TEST-004 | testing_mocking | HIGH | No | Scenario-based mock data exists |
| HLTH-001 | health_impact | HIGH | No | Liveness endpoint is declared |
| HLTH-002 | health_impact | HIGH | No | Readiness endpoint is declared |
| HLTH-003 | health_impact | HIGH | No | Dependency health endpoint is declared |
| HLTH-004 | health_impact | HIGH | No | Capability health endpoint is declared |
| HLTH-005 | health_impact | HIGH | No | Business-impact endpoint is declared |
| HLTH-006 | health_impact | HIGH | No | Required health paths exist in OpenAPI |
| AI-001 | ai_mcp_a2a | CRITICAL | Yes | MCP exposure is governed |
| LIFE-001 | lifecycle_reuse | HIGH | No | Versioning strategy is declared |
| LIFE-002 | lifecycle_reuse | HIGH | No | Deprecation policy is declared |
| LIFE-003 | lifecycle_reuse | HIGH | No | Compatibility policy is declared |
| LIFE-004 | lifecycle_reuse | HIGH | No | Reuse target is declared |
