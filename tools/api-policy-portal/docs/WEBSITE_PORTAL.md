# Policy Guidance Website and Validation Reports Portal

## Purpose

The portal converts the centralized policy repository into a browsable guidance site and a durable evidence dashboard. It serves two audiences:

- **API teams:** understand policies, prepare evidence, and resolve failed gates.
- **Architecture, security, platform, and audit users:** review traffic lights, testing logs, gate findings, and historical reports without downloading CI artifacts.

## Website sections

| Section | Purpose |
|---|---|
| Home | Framework summary, run counts, dimension cards, and latest results |
| Policies | Complete dimension-level catalog with gate IDs, severity, owners, and evidence paths |
| Reports | Searchable history of API validation runs |
| Run detail | Score, dimension traffic lights, findings, logs, JUnit/XML, JSON, and Markdown evidence |
| Test any API | Target-repository setup and execution guidance |
| Adoption | Cap & Grow transition guidance |
| Security | Log redaction and evidence-publication controls |

## Validation run bundle

The portal consumes one folder per validation run:

```text
validation-results/<run-id>/
├── metadata.json
├── tests.log
├── test-results.xml
├── policy-validation.log
├── policy-report.json
├── policy-report.md
├── coverage/                 # optional
└── reports/                  # optional
```

Required report fields are produced by `api-standards validate`. `metadata.json` identifies the source:

```json
{
  "run_id": "20260727T140000Z-order-api-42",
  "repository": "enterprise/order-api",
  "ref": "feature/spec-driven-contract",
  "commit": "d26e9b8...",
  "timestamp": "2026-07-27T14:00:00+00:00",
  "workflow_url": "https://github.com/.../actions/runs/..."
}
```

## Local website workflow

```bash
pip install -e ".[dev]"
make portal
api-standards portal serve --directory public --port 8000
```

The generated website is static and can be hosted on GitHub Pages, GitHub Enterprise Pages, an internal web server, S3-compatible object storage, or a corporate developer portal.

## GitHub Pages workflow

`publish-portal.yml` performs the following sequence:

1. Run policy-engine tests and capture `tests.log` and JUnit XML.
2. Validate an API and capture JSON, Markdown, and console logs.
3. Write repository/ref/commit metadata.
4. Restore previously published report history from `gh-pages`.
5. Generate the static portal.
6. Upload the run bundle as a GitHub Actions artifact.
7. Publish the website to the `gh-pages` branch.
8. Fail the workflow after publishing evidence when testing or policy gates fail.

Publishing evidence before failing the workflow ensures RED and AMBER runs remain visible to users.

## Central validation of API repositories

`validate-external-api.yml` is a manually dispatched aggregation workflow. Supply:

- target repository;
- branch, tag, or commit;
- path containing `api.yaml`;
- test command.

The workflow executes the tests, retains logs and reports, runs every policy dimension, and updates the central website.

For private repositories, configure `API_REPO_TOKEN` with the minimum read permissions needed to check out the target repository.

## Retention

The portal retains the most recent 200 runs by default. Change `retain_runs` in:

```text
website/portal-config.yaml
```

The complete run bundle is also uploaded as a GitHub Actions artifact. Adjust artifact retention in the workflow based on audit requirements.

## Log security

The site generator sanitizes common tokens, API keys, passwords, and secrets in text files before publication. Configure patterns under `redaction_patterns` in `website/portal-config.yaml`.

Redaction is a defense-in-depth feature, not a replacement for safe logging. Do not emit:

- bearer tokens;
- passwords or API keys;
- production customer payloads;
- private certificates;
- regulated data;
- unmasked production traces.

Binary artifacts are copied without content inspection and must be reviewed by the producing team.
