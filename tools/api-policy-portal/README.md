# Outcome-Centric API Policy Repository

A centralized, developer-ready policy repository that applies dimension-level API release gates, publishes guidance as a static website, and exposes traffic-light reports, test logs, and validation evidence through a searchable portal.

The repository is designed to be maintained centrally by architecture, security, platform, data, observability, testing, and AI-governance teams. Individual API repositories consume a tagged version of this policy repository and validate their design and build evidence during pull requests and release pipelines.

## Policy model

All policies and gates live under `policy-repository/`; Python supplies reusable evaluator functions and report generation. Each dimension file declares its owner, weight, gate IDs, severity, blocking behavior, evidence expectations, and GREEN/AMBER/RED thresholds.

| Light | Meaning | Pipeline behavior |
|---|---|---|
| 🟢 **GREEN** | Required gates pass and the API meets its risk-tier score | Release eligible; CLI exits `0` |
| 🟠 **AMBER** | No blocking gate failed, but remediation or formal risk acceptance is required | Build fails by default; CLI exits `1` |
| 🔴 **RED** | A blocking gate failed, a dimension is RED, or the score is below the minimum | Release blocked; CLI exits `1` |

A validator configuration or execution error exits with code `2`.

## Policy dimensions

1. Business outcome and capability alignment
2. Specification and data-contract quality
3. Lean API and resource design
4. Security and role-aware authorization
5. NoSQL transactional and data integrity
6. Cross-layer observability and auditability
7. Testing automation and mock coverage
8. Health and business-impact exposure
9. AI, MCP, and Agent-to-Agent governance
10. Lifecycle, versioning, and reuse

## Repository structure

```text
.
├── policy-repository/
│   ├── policy-index.yaml                 # Overall thresholds and shared settings
│   └── dimensions/                       # Policies and gates by dimension
├── schemas/
│   └── api-metadata.schema.json          # Schema for each API's api.yaml manifest
├── src/api_build_standards/              # Validator engine, CLI, and reporting
├── examples/
│   ├── compliant-api/                    # GREEN reference API
│   ├── amber-api/                        # AMBER reference API
│   └── noncompliant-api/                 # RED reference API
├── docs/                                 # Adoption, testing, and portal guidance
├── website/                              # Portal templates, styles, and redaction config
├── validation-results/                   # Local/CI run bundles used by the portal
├── public/                               # Generated static website (not committed)
├── tests/                                # Policy-engine and portal tests
└── .github/workflows/                    # Validation and website-publishing workflows
```

## Policy guidance website and validation portal

The repository includes a self-contained static website generator. The portal publishes:

- architecture and policy guidance for development teams;
- the complete dimension-level policy catalog and gate definitions;
- GREEN, AMBER, and RED status across every dimension;
- test-console logs and JUnit/XML reports;
- policy-validation logs;
- Markdown and JSON compliance reports;
- run metadata, repository, branch/ref, commit, and GitHub Actions link;
- historical validation runs retained across deployments.

### Build and view the website locally

```bash
make portal
api-standards portal serve --directory public --port 8000
```

Open `http://localhost:8000`. The `make portal` command generates three demonstration runs and builds the website into `public/`.

To build the portal from real validation bundles:

```bash
api-standards portal build \
  --results validation-results \
  --output public
```

Each run directory should contain the following files when available:

```text
validation-results/<run-id>/
├── metadata.json
├── tests.log
├── test-results.xml
├── policy-validation.log
├── policy-report.json
└── policy-report.md
```

Text-based artifacts are sanitized with the configurable patterns in `website/portal-config.yaml` before they are published. Teams must still prevent credentials, production payloads, and private customer data from entering build logs.

### Publish with GitHub Pages

The workflow `.github/workflows/publish-portal.yml` runs the validator, captures logs, restores previously published report history, builds the portal, and deploys the result to the `gh-pages` branch.

After pushing the repository to GitHub:

1. Open **Settings → Pages**.
2. Select **Deploy from a branch**.
3. Select the `gh-pages` branch and `/ (root)`.
4. Run **Publish API Policy Portal** from the Actions tab.

The workflow retains published run pages by loading the previous `gh-pages` content before building the new portal.

### Validate another API from the central repository

Use the manual workflow `.github/workflows/validate-external-api.yml`. It checks out a target API repository, executes the supplied test command, captures the complete test and policy logs, publishes the traffic-light report, and updates the central portal.

For private target repositories, create the repository secret `API_REPO_TOKEN` using a fine-grained token or GitHub App credential with read access to the target repositories.

See [`docs/WEBSITE_PORTAL.md`](docs/WEBSITE_PORTAL.md) for the publishing model, retention approach, report format, and security controls.

# How to Test Any API

The validator can test any API repository as long as that repository provides:

1. an `api.yaml` policy-evidence manifest at its root;
2. an OpenAPI specification referenced by the manifest;
3. test-evidence directories containing at least one file;
4. a mock-scenario file;
5. the required health paths, security declarations, observability headers, and policy metadata.

The paths declared in `api.yaml` are resolved **relative to the API repository being validated**, not relative to this policy repository.

## 1. Install the policy validator

From the root of this policy repository:

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Confirm the installation:

```bash
api-standards --help
api-standards catalog
```

## 2. Prepare the target API repository

A target API repository should contain this minimum evidence structure:

```text
my-api/
├── api.yaml
├── openapi.yaml
├── mocks/
│   └── scenarios.yaml
└── tests/
    ├── contract/
    │   └── contract-evidence.md
    ├── security/
    │   └── authorization-evidence.md
    └── failure/
        └── failure-path-evidence.md
```

The evidence files may initially be Markdown records, test specifications, test-result files, or executable tests. The current validator confirms that the required evidence locations exist and are non-empty. The API's own build pipeline should separately execute its unit, contract, integration, security, and failure-path tests.

## 3. Add `api.yaml` to the target API repository

Copy the GREEN reference manifest as a starting point:

```bash
cp examples/compliant-api/api.yaml /path/to/my-api/api.yaml
```

Then update it for the target API. The following template shows all currently evaluated dimensions:

```yaml
api:
  name: order-management-api
  version: 1.0.0
  layer: domain
  business_outcome: Manage the lifecycle of enterprise service orders.
  capability: Order Management
  risk_tier: high                    # critical | high | medium | low
  owners:
    business: Order Operations
    technical: Order Engineering
  consumers:
    - customer-web
    - agent-desktop
    - fulfillment-platform

contracts:
  openapi: openapi.yaml              # Relative to the target API repository
  backward_compatibility: true
  error_model: true

lean:
  resource_oriented: true
  screen_specific: false
  collection_detail_separated: true
  payload_right_sized: true
  reusable: true

security:
  authentication: OAuth2/OIDC
  actor_subject_model: true
  object_level_authorization: true
  policy_as_code: true
  acting_modes:
    - self_service
    - delegated
    - operational_override
    - system_initiated

integrity:
  nosql: true
  aggregate_owner: order-domain
  single_writer: true
  concurrency_control: version-etag
  idempotency: true
  outbox_inbox: true
  projection_freshness: true
  reconciliation: true
  saga_or_compensation: true

observability:
  traceparent: true
  correlation_id: true
  business_transaction_id: true
  structured_logs: true
  audit: true

health:
  live: /health/live
  ready: /health/ready
  dependencies: /health/dependencies
  capabilities: /health/capabilities
  impact: /health/impact

ai:
  mcp:
    enabled: false
  a2a:
    enabled: false

# When MCP is enabled, also declare:
#   mcp:
#     enabled: true
#     scoped_tools: true
#     object_level_authorization: true
#     audit: true
#     approval_for_high_risk: true
#
# When A2A is enabled, also declare:
#   a2a:
#     enabled: true
#     agent_identity: true
#     delegation_chain: true
#     task_status: true
#     audit: true

testing:
  contract_tests: tests/contract
  authorization_tests: tests/security
  failure_path_tests: tests/failure
  mock_scenarios: mocks/scenarios.yaml

lifecycle:
  versioning: semantic-versioning
  deprecation: minimum-180-day-notice
  compatibility: backward-compatible-by-default
  reuse_target: true
```

## 4. Prepare the target OpenAPI specification

The target `openapi.yaml` must, at minimum:

- use OpenAPI `3.x`;
- contain `info` and `paths` sections;
- define a security scheme under `components.securitySchemes`;
- apply security at the document level;
- declare the required observability headers somewhere in the specification;
- expose all required health paths;
- avoid prohibited path terms such as `screen`, `page`, `button`, `table`, `procedure`, and `storedproc`.

Required observability headers:

```text
traceparent
X-Correlation-ID
X-Business-Transaction-ID
```

Required health paths:

```text
/health/live
/health/ready
/health/dependencies
/health/capabilities
/health/impact
```

A minimal reusable header definition looks like this:

```yaml
components:
  parameters:
    Traceparent:
      name: traceparent
      in: header
      required: true
      schema:
        type: string
    CorrelationId:
      name: X-Correlation-ID
      in: header
      required: true
      schema:
        type: string
    BusinessTransactionId:
      name: X-Business-Transaction-ID
      in: header
      required: true
      schema:
        type: string
```

See `examples/compliant-api/openapi.yaml` for a complete passing example.

## 5. Add test and mock evidence

The validator expects all paths declared under `testing` to exist.

Create the directories and initial evidence files:

```bash
mkdir -p /path/to/my-api/tests/{contract,security,failure}
mkdir -p /path/to/my-api/mocks

touch /path/to/my-api/tests/contract/contract-evidence.md
touch /path/to/my-api/tests/security/authorization-evidence.md
touch /path/to/my-api/tests/failure/failure-path-evidence.md
```

Add scenario-based mock data to `mocks/scenarios.yaml`, for example:

```yaml
scenarios:
  - name: valid request
    expectedStatus: ACCEPTED
  - name: unauthorized object access
    expectedStatus: FORBIDDEN
  - name: stale aggregate version
    expectedStatus: CONFLICT
  - name: dependency timeout
    expectedStatus: ACTION_REQUIRED
  - name: duplicate idempotency key
    expectedBehavior: return-original-transaction
  - name: projection lag exceeds SLA
    expectedIntegrityStatus: CONVERGING
```

## 6. Validate the target API locally

Assume the policy repository and target API are sibling directories:

```text
workspace/
├── outcome-centric-api-policy-repository/
└── my-api/
```

From the **policy repository root**, run:

```bash
mkdir -p reports

api-standards validate ../my-api \
  --policy-index policy-repository/policy-index.yaml \
  --schema schemas/api-metadata.schema.json \
  --json-report reports/my-api.json \
  --markdown-report reports/my-api.md
```

You can also use an absolute target path:

```bash
api-standards validate /absolute/path/to/my-api \
  --policy-index "$PWD/policy-repository/policy-index.yaml" \
  --schema "$PWD/schemas/api-metadata.schema.json" \
  --json-report "$PWD/reports/my-api.json" \
  --markdown-report "$PWD/reports/my-api.md"
```

## 7. Interpret the result

The terminal and generated reports show:

- overall GREEN, AMBER, or RED status;
- weighted framework score;
- required score for the API risk tier;
- traffic light for every policy dimension;
- policy owner for each dimension;
- passed and failed gate counts;
- failed gate IDs;
- blocking findings and remediation needs.

Example results:

```text
🟢 GREEN — APPROVED
Weighted score: 100.0/100
```

```text
🟠 AMBER — REMEDIATION OR RISK ACCEPTANCE REQUIRED
Failed gate: LEAN-004
```

```text
🔴 RED — REJECTED — RELEASE BLOCKED
Blocking gates: SPEC-001, SEC-002, INT-001
```

Exit codes:

| Exit code | Meaning |
|---:|---|
| `0` | GREEN; validation passed |
| `1` | AMBER or RED; policy remediation or risk handling required |
| `2` | Validator configuration, file, schema, or execution error |

## 8. Review the generated reports

The command creates both machine-readable and human-readable evidence:

```text
reports/
├── my-api.json
└── my-api.md
```

Use the JSON report for dashboards, policy analytics, and automated release decisions. Use the Markdown report for pull-request summaries, architecture reviews, and remediation tracking.

## 9. Test the included reference APIs

Run the policy-engine tests:

```bash
pytest
```

Validate the GREEN example:

```bash
api-standards validate examples/compliant-api \
  --json-report reports/compliant.json \
  --markdown-report reports/compliant.md
```

Validate the AMBER example:

```bash
api-standards validate examples/amber-api \
  --json-report reports/amber.json \
  --markdown-report reports/amber.md
```

Validate the RED example:

```bash
api-standards validate examples/noncompliant-api \
  --json-report reports/noncompliant.json \
  --markdown-report reports/noncompliant.md
```

AMBER and RED intentionally return exit code `1`.

## 10. Validate an API in GitHub Actions

The recommended model is to keep this repository central and versioned, then consume it from each API repository.

Add the following workflow to the target API repository as `.github/workflows/api-policy-validation.yml`:

```yaml
name: API Policy Validation

on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  validate-api-policy:
    runs-on: ubuntu-latest

    steps:
      - name: Check out API repository
        uses: actions/checkout@v4

      - name: Check out central policy repository
        uses: actions/checkout@v4
        with:
          repository: YOUR-ORG/outcome-centric-api-policy-repository
          ref: v2.0.0
          path: .api-policy
          # For a private policy repository, configure an approved token:
          # token: ${{ secrets.API_POLICY_REPO_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install policy validator
        run: pip install -e ".api-policy[dev]"

      - name: Run API policy gates
        run: |
          mkdir -p reports
          set +e
          api-standards validate . \
            --policy-index .api-policy/policy-repository/policy-index.yaml \
            --schema .api-policy/schemas/api-metadata.schema.json \
            --json-report reports/api-policy-result.json \
            --markdown-report reports/api-policy-result.md
          exit_code=$?
          cat reports/api-policy-result.md >> "$GITHUB_STEP_SUMMARY"
          exit $exit_code

      - name: Upload policy evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: api-policy-reports
          path: reports/
```

Use a tagged policy version, such as `v2.0.0`, rather than an unpinned branch so that policy changes are deliberate and reproducible.

## 11. Run the API's executable tests in the same pipeline

This policy validator verifies declared evidence and selected OpenAPI controls. It does **not** replace the target API's executable test suite or call a deployed API.

A complete API pipeline should run both:

```text
API unit, integration, contract, security, and failure-path tests
                         +
Central policy-repository validation and traffic-light gates
```

For example:

```yaml
- name: Run API tests
  run: pytest

- name: Run central policy validation
  run: |
    api-standards validate . \
      --policy-index .api-policy/policy-repository/policy-index.yaml \
      --schema .api-policy/schemas/api-metadata.schema.json
```

## 12. Common validation failures

### `Missing API manifest`

Ensure `api.yaml` is at the root of the target repository passed to `api-standards validate`.

### OpenAPI file not found

The value of `contracts.openapi` is relative to the target API repository:

```yaml
contracts:
  openapi: openapi.yaml
```

### OpenAPI security gate fails

Define `components.securitySchemes` and apply a document-level `security` requirement.

### Observability-header gate fails

Ensure all three required header names appear in the OpenAPI document:

```text
traceparent
X-Correlation-ID
X-Business-Transaction-ID
```

### Health gate fails

All five required health paths must be declared in the OpenAPI `paths` section.

### Testing-evidence gate fails

Each configured test directory must exist and contain at least one file. The mock-scenario file must also exist.

### NoSQL integrity gate fails

When `integrity.nosql: true`, declare aggregate ownership, single-writer control, concurrency control, idempotency, outbox/inbox, projection freshness, reconciliation, and saga or compensation behavior.

### AI-governance gate fails

When MCP or A2A is enabled, all corresponding governance controls must be set to `true`. When an API does not expose MCP or A2A capabilities, set `enabled: false`.

### AMBER fails the pipeline

AMBER intentionally exits with code `1`. Remediate the failed gate or route the result through your organization's documented risk-acceptance workflow.

## 13. View and customize the policy catalog

List all dimensions and gate counts:

```bash
api-standards catalog
```

Central policy configuration:

```text
policy-repository/policy-index.yaml
```

Dimension-level policy files:

```text
policy-repository/dimensions/
```

Policy teams can adjust weights, owners, severity, blocking behavior, thresholds, evaluators, and required evidence without placing policy intent inside individual API repositories.

## Publish to a development team

Publish this repository as the central policy source and create immutable release tags. API teams should consume a tagged version and run `api-standards validate` in pull requests and release pipelines. The generated traffic-light scorecard can be added to the GitHub job summary and retained as JSON/Markdown release evidence.

## License

Apache License 2.0.
