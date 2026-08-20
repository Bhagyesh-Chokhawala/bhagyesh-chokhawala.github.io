# Enterprise AI Standards & Governance Portal

A deployable static portal for operationalizing the **Balanced Enterprise Architecture Framework for Secure and Ethical AI Adoption** as implementation standards, deployment standards, guidelines, checkpoints, policy artifacts, and evidence templates.

## What is included

- Searchable standards catalog with traffic-light indicators
- Implementation and deployment checkpoint console
- Risk-tier-aware control filtering
- Evidence pack builder and release manifest template
- Downloadable Markdown standards and YAML policies
- Definition-of-Done, Definition-of-Ready, and post-deployment checklists
- GitHub Pages deployment workflow
- No backend and no build step required

## Run locally

From the project root:

```bash
python3 -m http.server 8080
```

Open `http://localhost:8080`.

## Deploy to GitHub Pages

### Option A — GitHub Actions

1. Create or use a GitHub repository.
2. Copy this project into the repository root.
3. Push to the `main` branch.
4. In **Settings → Pages**, choose **GitHub Actions** as the source.
5. The included `.github/workflows/pages.yml` workflow publishes the portal.

### Option B — `/docs` folder

If your repository already uses GitHub Pages from `/docs`, copy the portal contents into that folder and configure **Settings → Pages → Deploy from a branch → main /docs**.

## Repository structure

```text
enterprise-ai-standards-portal/
├── index.html
├── assets/
│   ├── styles.css
│   └── app.js
├── data/
│   ├── artifacts.js
│   └── artifacts.json
├── artifacts/
│   ├── architecture/
│   ├── data/
│   ├── ai-engineering/
│   ├── security/
│   ├── ethics/
│   ├── devex/
│   ├── evaluation/
│   ├── deployment/
│   ├── operations/
│   ├── governance/
│   ├── checklists/
│   ├── policies/
│   ├── templates/
│   └── samples/
└── .github/workflows/pages.yml
```

## Governance model

The portal maps controls to the framework dimensions:

- Business Value
- Technology Readiness
- Developer Enablement
- User Trust & Completeness
- Security
- Ethics
- Governance
- Operating Model

Controls use normative terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY**. Mandatory failed checkpoints are treated as production blockers.

## Customize

Edit `data/artifacts.js` and `data/artifacts.json` to add or modify controls. The UI reads from `artifacts.js` so it works on GitHub Pages without an API.

## Policy validation tools

Validate the standards repository itself:

```bash
python tools/lint_repository.py
```

Validate a full checkpoint assessment exported from the portal:

```bash
python tools/validate_assessment.py ai-readiness-r3-2026-08-20.json
```

A failed mandatory control returns a non-zero exit code so the command can be used as a CI/CD production gate.
