# Central API Policy Repository

This directory is the single source of truth for API build-time policies and release gates.
Policies are separated by architecture dimension so each control has an owner, weight, gate ID,
severity, evaluator, evidence expectation, and traffic-light threshold.

## Traffic lights

| Indicator | Meaning | Default action |
|---|---|---|
| 🟢 GREEN | Dimension score is 90 or higher and no blocking gate failed | Release eligible |
| 🟠 AMBER | Dimension score is 70–89.99 and no blocking gate failed | Remediate or approve documented risk |
| 🔴 RED | Score is below 70 or any blocking gate failed | Build/release blocked |

The overall result is RED when any dimension is RED due to a blocking gate. Otherwise the
weighted portfolio score determines GREEN, AMBER, or RED using `policy-index.yaml`.

## Structure

```text
policy-repository/
├── policy-index.yaml
└── dimensions/
    ├── 01-outcome-capability.yaml
    ├── 02-specification-contract.yaml
    ├── 03-lean-resource-design.yaml
    ├── 04-security-authorization.yaml
    ├── 05-nosql-integrity.yaml
    ├── 06-observability-audit.yaml
    ├── 07-testing-mocking.yaml
    ├── 08-health-impact.yaml
    ├── 09-ai-mcp-a2a.yaml
    └── 10-lifecycle-reuse.yaml
```

Python contains evaluator implementations only; policy intent and release-gate configuration
remain in this repository.
