# Policy Repository Model

The repository follows a policy-as-data model:

- `policy-index.yaml` controls policy version, shared settings, risk tiers, and overall traffic lights.
- Each dimension YAML controls its weight, owner, gates, severity, evidence, and local thresholds.
- Evaluator functions execute gate types but do not contain enterprise policy decisions.
- Markdown and JSON outputs expose dimension-level traffic lights and failed gate IDs.

A policy change is reviewed through CODEOWNERS and versioned as a repository release. API builds
should pin a tag or commit SHA to ensure reproducible validation.
