# SEO-optimized GitHub Pages package

This package is ready to upload to the root of:

`Bhagyesh-Chokhawala/bhagyesh-chokhawala.github.io`

## High-impact improvements included

- Unique titles and meta descriptions for core pages
- Canonical URLs
- Open Graph and Twitter social preview tags
- `ProfilePage`, `CollectionPage`, `ItemList`, `ScholarlyArticle`,
  `BreadcrumbList`, and `ContactPage` JSON-LD
- Google Scholar `citation_*` metadata on publication pages
- Searchable publication landing page for the CSCI 2025 PDF
- Correct Digital Transformation DOI: `10.5281/zenodo.21478254`
- Lowercase canonical Digital Transformation folder and a legacy redirect page
- Complete sitemap with publication landing pages and `lastmod`
- Clean robots.txt with sitemap declaration
- Favicon, web manifest, social preview image, RSS feed, and 404 page
- Stronger internal linking between home, publications, blogs, and contact
- Dynamic copyright year

## Upload instructions

Upload all files and folders from this package to the repository root.

For the Digital Transformation paper, the package introduces the canonical folder:

`/publications/digital-transformation-digitization-modernization-roi-framework/`

The old uppercase folder is retained only as a noindex redirect page.

## Keep existing PDFs

The package copies the PDFs that were available in the working environment.
If a PDF is missing from the package, keep the existing repository PDF in place.

In particular, preserve:

`/publications/CSCI-2025/Cognitive_BPM_Integration_Framework_CSCI_2025.pdf`

## Google Search Console

1. Add the URL-prefix property:
   `https://bhagyesh-chokhawala.github.io/`
2. Verify ownership with an HTML tag or verification file.
3. Submit:
   `https://bhagyesh-chokhawala.github.io/sitemap.xml`
4. Inspect and request indexing for:
   - `/`
   - `/publications.html`
   - each new publication landing page
5. Review the Page indexing, Core Web Vitals, and Enhancements reports.

## Validation

After deployment, test:

- Google Rich Results Test
- Schema.org Validator
- Google Search Console URL Inspection
- PageSpeed Insights
- Open Graph preview tools

Structured data improves machine understanding but does not guarantee a rich result.

## External metadata consistency

For best scholarly indexing, keep the title, author, year, DOI, and abstract
identical across the PDF, Zenodo, Google Scholar, ORCID, and the publication page.

Items to review:

- The Zenodo BAR-framework title currently displays `Human- Centered`; update it
  to `Human-Centered`.
- The Zenodo Target Architecture record uses a shortened title while the PDF and
  website use the full framework title.
- Confirm the Spec-Grounded Modernization publication date and title on Zenodo.
