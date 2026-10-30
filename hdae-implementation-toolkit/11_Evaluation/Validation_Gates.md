# HDAE Validation Gates

1. Intent Readiness — intent complete, owner assigned, success/failure semantics defined.
2. Architecture Readiness — capability, contract, systems of record, recovery defined.
3. Delegation Readiness — autonomy level, authority profile, prohibited actions, revocation tested.
4. Control Readiness — identity, policy, approval, evidence, intervention, fail-closed behavior tested.
5. Evaluation Readiness — metrics baselined, negative tests, failure injection, trace completeness verified.
6. Production Readiness — business, architecture, security, risk, domain, and operations approvals obtained.
## BAR-HDAE Evidence Gates

The BAR lifecycle gates govern capability progression. They are evidence gates, not weighted scores: failure in a critical readiness or responsibility condition cannot be offset by a high business-value score.

## G0 — Business Legitimacy (BAR-B)

- Problem and affected parties are documented.
- Accountable value owner is named.
- Baseline and target benefit are measurable.
- AI is justified against simpler alternatives.
- Outcome scope and initial risk class are approved.

## G1 — Architecture Readiness (BAR-A)

- Capabilities, owners, authoritative data, systems of record, and dependencies are mapped.
- Outcome contracts, domain boundaries, and state invariants are defined.
- Identity, policy, integration, NFR, resilience, observability, and lifecycle cost readiness are assessed.
- Gaps have owners and dispositions; critical gaps block pilot.

## G2 — Controlled Pilot (BAR-R)

- Production authority is restricted to a bounded population and reversible action set.
- Policy mediation, human approval, trace completeness, pause/kill, and recovery are tested.
- Business KPIs, adoption, trust, override, intervention, incidents, and cost are observed against a baseline.
- A named review group records scale, hold, remediate, or stop with rationale.

## G3 — Enterprise Scale (BAR-B/A/R)

- Pilot demonstrates sustained value, reliability, trust, adoption, and acceptable residual risk.
- Reusable capabilities, contracts, policies, and evaluation patterns are versioned and owned.
- Support, incident response, continuous assurance, revocation, and retirement are operational.
- Scope or autonomy expansion has explicit evidence and accountable approval.

## HDAE episode acceptance

Every outcome episode must link human intent, plan, identity and authority, independent policy decision, tool invocation, domain transaction, human intervention, postcondition verification, and final outcome evidence. State-changing actions must have idempotency and tested retry, compensation, reconciliation, pause, or escalation semantics.
