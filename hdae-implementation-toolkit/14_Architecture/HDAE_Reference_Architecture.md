# HDAE Reference Architecture

```mermaid
flowchart TB
 H[Humans: Why What Who When Where Which] --> I[Intent Envelope]
 I --> A[AI Agent: Delegated Operational How]
 A --> G[Runtime Control Gateway]
 G <--> P[Identity / Authority / Policy / Approval]
 G --> C[Business Capabilities]
 C --> O[Outcome Contracts]
 O --> D[Domain APIs / Applications / Systems of Record]
 K[Data & Knowledge] --> A
 G --> E[Evidence / Observability]
 D --> E
 D --> R[Recovery / Compensation / Intervention]
 R --> E
 R --> H
```

Cross-cutting technology enablement: identity, authorization, policy, integration,
security, observability, evidence, recovery, data governance, agent/model lifecycle.
## BAR-Governed HDAE Reference Architecture

This reference architecture implements the revised BAR-HDAE dual-loop model. BAR governs whether, where, and to what extent an AI capability should be adopted and scaled. HDAE governs how one authorized human outcome episode is planned and executed. Runtime evidence flows back to BAR lifecycle decisions.

```mermaid
flowchart LR
	subgraph BAR["Outer loop: BAR capability lifecycle"]
		direction TB
		B["BAR-B: Business Value and Purpose"] --> G0["G0: Business legitimacy"]
		A["BAR-A: Architecture Readiness and Integration"] --> G1["G1: Architecture readiness"]
		R["BAR-R: Responsible Adoption and Realization"] --> G2["G2: Controlled pilot"] --> G3["G3: Enterprise scale"]
		G0 --> G1 --> G2 --> G3
	end

	subgraph HDAE["Inner loop: HDAE outcome episode"]
		direction LR
		H["Human enterprise intent"] --> I["Intent Envelope"] --> P["Bounded agent plan"]
		P --> M["Technology mediation"] --> D["Domain systems of record"]
		M --> E["Evidence and provenance"]
		D --> E --> V["Verify outcome and success criteria"]
		D --> X["Recover, reconcile, pause, or intervene"] --> E
	end

	G0 --> H
	G1 --> M
	M -. "episode evidence: intent, plan, policy, tool, transaction, intervention, outcome, benefit" .-> R
	G2 -. "pilot evidence" .-> R
```

## Responsibility allocation

- **Human enterprise intent:** defines why, what, who, when, where, which, authority, constraints, and success evidence.
- **Delegated operational agency:** determines the operational how inside explicit permission, prohibition, threshold, expiry, and revocation boundaries.
- **Technology mediation:** authenticates principal, workload, and tool; validates intent and contracts; independently evaluates policy; obtains required human approval; orchestrates durable actions; records evidence; verifies postconditions.
- **Domain execution:** authoritative applications and systems of record preserve business invariants and transaction correctness.
- **Evidence bridge:** episode evidence informs BAR-R adoption, remediation, autonomy, scale, and retirement decisions.

## BAR evidence gates

| Gate | Decision | Minimum evidence |
| --- | --- | --- |
| G0 | Business legitimacy | Problem, accountable owner, baseline, target benefit, affected parties, AI-versus-alternative rationale |
| G1 | Architecture readiness | Authoritative data, capabilities, contracts, identity, integration, NFRs, resilience, observability, lifecycle cost |
| G2 | Controlled pilot | Restricted authority, policy compliance, trace completeness, tested recovery, adoption, KPI evidence |
| G3 | Enterprise scale | Sustained value, readiness, responsible adoption, reusable controls, continuous assurance |

## Seven HDAE implementation phases

1. Scope outcome episode.
2. Model Intent Envelope.
3. Map capabilities and contracts.
4. Design delegation and autonomy.
5. Assemble agent toolchain.
6. Engineer integrity and evidence.
7. Validate, learn, and scale.

The 12 toolkit artifacts map to these phases in the process builder. The framework is conceptual and has not been empirically validated; organizations must tailor thresholds and evidence to their context.
