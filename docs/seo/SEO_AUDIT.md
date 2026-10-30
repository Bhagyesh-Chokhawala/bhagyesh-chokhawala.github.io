# SEO and Indexing Audit — October 29, 2026

## Status and scope

The cached public GitHub source for `sitemap.xml` listed only the homepage, `publications.html`, and `publications/capability-centric-enterprise-architecture/`. Public live content visible through the search crawler includes additional pages and three portals. `robots.txt` allows all user agents and points to `sitemap.xml`.

The live XML sitemap could not be directly parsed by the browsing tool because its content type was not supported, so compare this package against the **current deployed** XML before overwriting it. This package does **not** establish whether any page is indexed in Google, nor does it submit anything to Search Console.

## Priority 1: Discovery and canonical URL hygiene

1. Run `generate_sitemap.py` from the actual repository to include all canonical indexable HTML pages, including new publication directories. Review its CSV before committing.
2. Check that each page resolves with HTTP 200; a crawler returning no data is not evidence of a 404. Case-sensitive variants merit attention: the public publications index links to lowercase `/publications/csci-2025/` and `/publications/digital-transformation-digitization-modernization-roi-framework/`, whereas an older GitHub directory listing displayed title-cased folders. Resolve based on the current deployed URLs and explicit canonical tags.
3. Check `contact.html` and `upcomingpublications.html`, and include only if useful, canonical, indexable, accessible pages.
4. Test the three portals for `noindex` and self-referencing canonicals, since they are separate deployable projects.
5. Avoid putting 404, verification, helper, demo, redirected or duplicate/canonical-alias pages in the sitemap.

## Priority 2: Content and metadata

- Preserve the homepage's present descriptive title, meta description, canonical, Open Graph/Twitter metadata, and JSON-LD `Person`, `ProfilePage` and `WebSite` objects.
- Validate that the homepage's `ProfilePage.dateModified` accurately reflects a meaningful substantive update. The historical source showed `2026-07-22T00:00:00Z`; do not bump it just for SEO.
- Give each publication detail page a unique title, clear abstract (already generally present), author, publication year, DOI, canonical, and descriptive meta description. Where applicable, add valid `ScholarlyArticle`/`Article` JSON-LD using **verified** dates and publication information.
- Ensure `publications.html` connects to every detail page with ordinary `<a href>` links. Include links among related papers and from the homepage to major research areas.
- Ensure any featured portals have a standalone landing description explaining purpose, code/demo links, and primary paper relationship; avoid indexing thin generated reports as separate landing pages.
- For PDFs, provide searchable text, accurate metadata, a stable URL, and accessible links from paper landing pages.

## Priority 3: Search Console and measurement

1. Confirm the URL-prefix property and your owner permissions in https://search.google.com/search-console.
2. After deploying the sitemap file, submit `sitemap.xml` under Indexing → Sitemaps.
3. Use URL Inspection for the homepage, publications index, both 2026 RAIS pages, and highest-priority missing papers; request indexing for owned URLs as needed.
4. Examine Indexing → Pages for 'Discovered - currently not indexed', 'Crawled - currently not indexed', `noindex`, canonical conflicts, redirects and 404s.
5. After discovery, check Performance by query/page. Research-target keywords can include *active inference explainable recommender*, *expected free energy decomposition*, *enterprise AI governance framework*, *cognitive AI BPM*, and *transaction-safe autoscaling* where those terms accurately match page contents.
6. Separately monitor Google Scholar visibility of individual papers; Google Search sitemap submission does not automatically create Scholar records.

## What remains unverified

- Live current contents of `sitemap.xml` (the main browser does not display application/xml)
- Current HTTP status, canonical and robots directives on every page
- Search Console indexed/not-indexed outcomes, crawl counts, ranking and impressions
- Whether root pages `contact.html`, `upcomingpublications.html`, two older paper slugs and all separately maintained portal pages meet inclusion requirements
- Deployment of the package to GitHub (not performed)
