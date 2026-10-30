# BAR-HDAE Demo Runbook: Governed Customer Onboarding

## Research boundary

The revised paper presents a conceptual framework and has not been empirically validated. This runbook demonstrates the operational artifact model; prefilled sample values are illustrative, not pilot or production evidence.

## Scenario

A financial-services operations team wants an agent to collect and validate onboarding documents, create a draft case, and escalate exceptions. The agent may not approve customers, activate accounts, change risk ratings, or override screening results.

## Load the sample

1. Start the app with `PORT=8097 python wsgi.py` and sign in using the local demo account.
2. Open the BAR-HDAE implementation workbench and load **Customer onboarding**.
3. Review the 12 prefilled artifacts. Replace sample values with organization-approved information.
4. Use **Save and continue** to move through the seven HDAE phases.
5. Inspect the generated outcome charter, intent canvas/envelope, readiness map, contract, authority/autonomy, tool registry, policy pack, transaction recovery, trace/evaluation, and realization playbook.
6. Review G0 and G1 sample design evidence. Treat these as illustrative only; replace with approval references and readiness assessments.
7. Build the implementation baseline only after reviewing G0/G1. This build does not mean the capability is piloted, scaled, or production-ready.
8. In a real deployment, perform development/test validation, run a restricted pilot, then record actual evidence for G2 and G3.

## Twelve artifacts in seven phases

1. **Scope outcome episode:** Outcome Charter — problem, owner, baseline, benefit target, affected parties, risk class, and AI rationale.
2. **Model Intent Envelope:** Enterprise Intent Canvas — why, what, who, when, where, which; Intent Envelope Schema — version, constraints, success evidence, expiry, autonomy ceiling, recovery criteria.
3. **Map capabilities and contracts:** Capability-Readiness Map — capability owners, authoritative data, systems, dependencies, NFRs and gaps; Outcome Contract — preconditions, policies, state model, completion and failure semantics.
4. **Design delegation and autonomy:** Agent Authority Profile — principal/workload, scopes, tools, prohibitions, thresholds, expiry/revocation; Autonomy-Risk Matrix — impact, uncertainty, reversibility, sensitivity, observability, recovery strength.
5. **Assemble agent toolchain:** Tool and Action Registry — schemas, side effects, owner, version, risk; Policy and Control Pack — independent decisions, tests, approvals, exceptions, logs.
6. **Engineer integrity and evidence:** Transaction and Recovery Map — state transitions, idempotency, retries, compensation and reconciliation; Traceability and Evaluation Schema — episode provenance and BAR/HDAE metrics.
7. **Validate, learn, and scale:** Governance, Incident, and Realization Playbook — release, monitoring, pause/kill, incident roles, rollback, benefit review, scale/hold/remediate/stop, retirement.

## BAR gates

- **G0 Business legitimacy:** approve the problem, value owner, baseline, target benefit, affected parties, and rationale for AI.
- **G1 Architecture readiness:** evidence readiness of data, capabilities, contracts, identity, integration, NFRs, resilience, observability, and lifecycle cost.
- **G2 Controlled pilot:** after implementation build and deployment, record restricted authority, policy compliance, complete traces, recovery tests, adoption, and KPI evidence.
- **G3 Enterprise scale:** require sustained value, readiness, responsible adoption, reusable controls, and continuous assurance.

Gates are sequential, non-compensatory evidence decisions. Do not mark G2 or G3 complete with placeholder text.

## Runtime episode to demonstrate

The episode trace should show versioned intent; authenticated human, workload, and tool identities; approved context; constrained plan; schema/precondition validation; independent policy decision; human approval wait state where required; workflow handoff; domain result; postcondition/success verification; and recovery or closure. This local POC produces a hash-linked in-process trace; it does not persist to an enterprise durable workflow/evidence service.

## Output and limitations

The package contains 12 structured stage artifacts, the process definition, BAR gate state, architecture/implementation reports, C4 diagrams, executive brief, generated guides, and event history. It is a design baseline. Production needs durable workflow/state storage, enterprise identity and policy integration, domain authorization, evidence retention, tested recovery, and organizational approval. The paper's propositions and measures are hypotheses for later empirical evaluation, not validated findings.
