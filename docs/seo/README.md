> **Integration notes (this repository):** `generate_sitemap.py`, `seo-extra-urls.txt`, `robots.txt` and `sitemap.xml` live at the repo root; these docs live in `docs/seo/`.
> The generator was adapted: it no longer skips `dist/` (the Elastic Scaling Planner is served from there), skips `tools/`, `static/`, preview and PDF-viewer pages, and writes git-derived `<lastmod>` (use `--no-lastmod` to disable). All portals are in this repo, so `seo-extra-urls.txt` is empty.
> Regenerate with `python3 generate_sitemap.py`; it also writes a review file, `seo-validation.csv` (not committed).
> The package's static 12-URL `sitemap.xml` was not used as-is, since the generator output (39 URLs) supersedes it. `seo-pending-review.csv` is resolved: `contact.html` and `publications/csci-2025/` are included (the latter after fixing its canonical casing); `upcomingpublications.html` is excluded because it canonicalizes to `publications.html`.

# SEO Indexing Package for bhagyesh-chokhawala.github.io

Prepared October 29, 2026 from publicly visible site pages and GitHub repository contents.

## What this package does

- `sitemap.xml`: 12 publicly discoverable URLs, replacing a repository-cached sitemap that contained only 3. This is a **reviewable starting point**, not a certified inventory of every page.
- `robots.txt`: preserves current permissive crawl instructions and references the sitemap.
- `generate_sitemap.py`: discovers indexable HTML pages in your **local main website repository**, checks title, meta description, H1, canonical and `noindex`, and rebuilds sitemap.xml. It does not invent `<lastmod>` timestamps.
- `seo-extra-urls.txt`: three known same-host portals maintained separately from the main repository. Verify their indexability and canonical URLs.
- `seo-pending-review.csv`: site URLs whose HTTP status and canonical path need verification before inclusion.
- `SEO_AUDIT.md`: precise audit and indexing steps.

## Deployment

1. Open your GitHub Pages repository: `Bhagyesh-Chokhawala/bhagyesh-chokhawala.github.io`.
2. Copy `generate_sitemap.py` and `seo-extra-urls.txt` into the repository root.
3. In a local clone at the website repository root, run:
   `python3 generate_sitemap.py`
4. Review `seo-validation.csv` and all URLs in the generated `sitemap.xml`. Ensure pages are published, return HTTP 200, are indexable, and use a self-referencing canonical.
5. Resolve the case-sensitive-path questions in `seo-pending-review.csv`, then regenerate.
6. Commit `sitemap.xml`, `robots.txt`, and any metadata fixes; push to the publishing branch.
7. Visit `https://bhagyesh-chokhawala.github.io/sitemap.xml` and confirm it shows the new URLs.
8. In Google Search Console, select URL-prefix property `https://bhagyesh-chokhawala.github.io/`, go to Sitemaps, add `sitemap.xml`, and submit. Inspect key URLs and select Request indexing where available.
9. Monitor Pages / Page Indexing and sitemap status, including excluded and discovered-not-indexed URLs.

**Do not simply submit the file in this zip to Google:** the sitemap must first be hosted by your website. Do not submit GitHub blob/raw URLs as the site's sitemap.

### Notes

- Root-level `sitemap.xml` can list pages on same host under other project directories, but coordinate any canonical/noindex settings in those separately deployed projects.
- Your site's `robots.txt` is already correct based on the visible repository copy.
- Google does not guarantee indexing; crawling may take days/weeks and Google Search Console permissions are required for submissions/request indexing.
- Do not add canonicalized duplicates, redirects, 404s, development pages or `noindex` pages to the sitemap.
- Google Search and Google Scholar indexing are separate workflows. Academic PDFs should remain accessible and linked with clean, unique abstracts and bibliographic metadata.

## Sources and reference guidance

- Sitemap and robots repository files: https://github.com/Bhagyesh-Chokhawala/bhagyesh-chokhawala.github.io
- Sitemap submission: https://support.google.com/webmasters/answer/7451001
- Crawling requests: https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl
- Sitemap XML guidance: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
