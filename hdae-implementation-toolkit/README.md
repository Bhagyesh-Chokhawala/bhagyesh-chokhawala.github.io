# BAR-Governed HDAE Implementation Toolkit

This proof of concept operationalizes the revised **BAR-HDAE dual-loop model** from the journal manuscript. BAR governs whether, where, and to what extent an AI-enabled capability should be adopted and scaled. HDAE governs how one authorized human outcome episode is planned, mediated, executed, verified, and recovered.

The manuscript is conceptual and has **not been empirically validated**. This POC is a design-science-oriented implementation artifact for demonstrating the method; it is not evidence that the theory or its measures have been validated, and it does not provision enterprise infrastructure or connect live systems by itself.

## Two governance loops

- **Outer BAR lifecycle:** Business Value and Purpose (BAR-B), Architecture Readiness and Integration (BAR-A), and Responsible Adoption and Realization (BAR-R) govern experiment, pilot, scale, remediation, hold, and stop decisions.
- **Inner HDAE outcome episode:** Human intent is translated to a bounded agent plan, mediated through identity, authority, policy, contracts, tools, transactions, evidence, and intervention, then verified against success criteria.
- **Evidence bridge:** Each episode links intent, plan, policy decision, tool call, transaction, intervention, outcome, and benefit to BAR-R realization decisions.

## BAR evidence gates

1. `G0 Business legitimacy`: problem, owner, baseline, target benefit, affected parties, and rationale for AI versus alternatives.
2. `G1 Architecture readiness`: authoritative data, capabilities, contracts, identity, integration, NFRs, resilience, observability, and lifecycle cost.
3. `G2 Controlled pilot`: restricted authority, policy compliance, trace completeness, tested recovery, adoption, and KPI evidence.
4. `G3 Enterprise scale`: sustained value, readiness, responsible adoption, reusable controls, and continuous assurance.

These are minimum evidence gates, not compensatory weighted scores. Critical architecture or responsibility failures cannot be offset by a high business-value score.

## Seven HDAE implementation phases

1. Scope outcome episode.
2. Model Intent Envelope.
3. Map capabilities and contracts.
4. Design delegation and autonomy.
5. Assemble agent toolchain.
6. Engineer integrity and evidence.
7. Validate, learn, and scale.

## Twelve toolkit artifacts

Outcome Charter; Enterprise Intent Canvas; Intent Envelope Schema; Capability-Readiness Map; Outcome Contract Template; Agent Authority Profile; Autonomy-Risk Matrix; Tool and Action Registry; Policy and Control Pack; Transaction and Recovery Map; Traceability and Evaluation Schema; Governance, Incident, and Realization Playbook.

## Run the POC

```bash
. .venv/bin/activate
PORT=8097 python wsgi.py
```

Open `http://127.0.0.1:8097`. Demo authentication is for local demonstration only. Load either sample, inspect its 12 populated artifact records, review G0/G1 design evidence, and use the workbench to record actual G2/G3 evidence after a pilot. The demo intentionally does not claim pilot or scale evidence.

## Cloudflare Workers deployment (Free plan)

The hosted toolkit runs as a Python Worker using Cloudflare's Flask WSGI adapter,
with D1 storing each session's wizard state. Containers and Docker are not needed
for this deployment. Free-tier request, CPU, and database quotas still apply.

Prerequisites: Node.js 22 or newer, `uv`, and a Cloudflare login (`npx wrangler login`).
From this directory:

```bash
npm ci
npx wrangler d1 execute hdae-toolkit-state --remote --file schema.sql
uv run pywrangler deploy
```

The existing database binding is in `wrangler.jsonc`. For another account, create
a D1 database and replace its database ID before deploying. `prepare_worker.py`
stages application code and runbooks, excluding local environments and tooling.
Python dependencies are declared in `pyproject.toml`; `requirements-container.txt`
is retained only for the optional Docker deployment.

Check `/health` after deployment. Sign in with the demo credentials shown on the
login page, load a sample, and verify `/api/wizard` and the ZIP download. This
remains a public demonstration with demo authentication.

## Evaluation

The metric catalog separates BAR-B value, BAR-A readiness, HDAE episode controls and operations, and BAR-R responsible realization. The L0-L4 maturity model measures institutional capability, not model sophistication. Metric definitions and targets must be baselined and tailored before production use.

Run tests with `.venv/bin/python -m unittest -v`.

See [the reference architecture](14_Architecture/HDAE_Reference_Architecture.md), [evidence gates](11_Evaluation/Validation_Gates.md), [metrics](11_Evaluation/Metrics_Catalog.csv), [maturity model](12_Maturity/HDAE_Maturity_Model.csv), and [process builder guide](13_Implementation/Process_Builder_Guide.md).
