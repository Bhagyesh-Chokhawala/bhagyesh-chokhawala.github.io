# API Policy Portal Website Enhancement

This package is designed to be merged into the root of:

```text
Bhagyesh-Chokhawala/bhagyesh-chokhawala.github.io
```

It adds:

- a homepage feature section and navigation link;
- `/api-policy-portal/` with ten policy dimensions;
- executed GREEN, AMBER, and RED validation demonstrations;
- complete policy-validation console logs;
- pytest/JUnit reports;
- downloadable JSON and Markdown compliance evidence;
- the policy engine and portal generator under `tools/api-policy-portal/`;
- a GitHub Pages workflow that regenerates evidence and deploys the complete site.

## Deploy

1. Copy all files from this package into the root of the website repository.
2. Commit and push to `main`.
3. Open **Settings → Pages**.
4. Set **Source** to **GitHub Actions**.
5. Run **Build Research Site and API Policy Portal** from the Actions tab.
6. Open `https://bhagyesh-chokhawala.github.io/api-policy-portal/`.

## What is real versus illustrative

The included results are actual executions of the supplied validator and pytest suite against three reference API repositories. They are demonstration datasets rather than claims about a production API portfolio. Each workflow run regenerates the logs and reports and stamps the current GitHub repository, branch, commit, and workflow URL into the run metadata.

## Local preview

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e "tools/api-policy-portal[dev]"

cd tools/api-policy-portal
bash scripts/generate-demo-runs.sh
python -m api_build_standards.cli portal build \
  --results validation-results \
  --output ../../api-policy-portal
cd ../..

python3 -m http.server 8000
```

Open:

```text
http://localhost:8000/
http://localhost:8000/api-policy-portal/
```
