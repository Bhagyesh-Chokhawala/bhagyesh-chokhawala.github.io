# Elastic Scaling Planner source code

Standalone source for the web-based capacity, readiness-delay and transaction-safe scaling calculator. The application files are unchanged from the delivered web version. Hosting identity, repository metadata and credentials are excluded.

## Run locally

Use Python 3 to serve the static files from this directory:

```bash
python3 -m http.server 8080 --bind 127.0.0.1 --directory dist
```

Open http://localhost:8080 in your browser. On Windows, `py -m http.server 8080 --bind 127.0.0.1 --directory dist` is an alternative. Stop the server with Ctrl+C.

Do not open index.html by double-clicking: browser security restrictions can prevent JavaScript module imports over file:// URLs. No npm install, build step, database, API key or backend service is required.

## Source files

| File | Purpose |
|---|---|
| dist/index.html | Page structure and calculation notes |
| dist/style.css | Responsive design, typography and print styling |
| dist/app.mjs | Guided input forms, validation, SVG chart, results, JSON download and print controls |
| dist/model.mjs | Pure capacity, timing, deficit, queue, resilience and latency calculations |
| test.mjs | 20 calculation assertions |

The dist directory contains editable source files, not minified build output. Edit the files directly and refresh your browser.

## Tests

With a modern Node.js installation:

```bash
node test.mjs
```

Expected output: `20 calculator assertions passed`. Tests cover the worked example, flat demand, initial overload, queue bounds, replica constraints, pinned sessions, dependency limits and invalid inputs.

## Deploy elsewhere

Publish the contents of dist to a static web host. Serve .mjs files with a JavaScript MIME type. No original hosting configuration is necessary. This export does not include an authentication layer: configure your hosting access controls if the calculator should be private.

## Customize

- Change field labels, helper text, defaults and the worked example in app.mjs.
- Change formulas and validation in model.mjs; add corresponding assertions to test.mjs.
- Change visual styling in style.css.
- Add explanatory content in index.html.

## Model and privacy notes

Calculations run in the browser; entered parameters are not transmitted by the application or saved automatically. The stylesheet requests Google Fonts; remove its initial @import rule to eliminate that external font request. Local font fallbacks remain available.

The calculator assumes homogeneous replica capacity, linear nonnegative demand growth and stepwise arrival of new capacity. Readiness delay is a user-provided end-to-end estimate or quantile, not a measured value supplied by the app. The temporary deficit ends at the entered readiness delay; a persistent dependency bottleneck may remain afterward.

The paper example uses 2,500 RPS plus 8 RPS/s growth over a 130-second planning horizon, yielding 3,540 forecast RPS and an 11-replica target. Its pre-arrival deficit at 110 seconds is 21,025 operations. This consistently applies the growth model rather than mixing it with a separate 3,500-RPS forecast.

Results are planning estimates, not guarantees of latency, quorum, availability, safe termination or exactly-once effects. The calculator does not control live infrastructure.
