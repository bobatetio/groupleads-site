# GroupLeads — self-contained HTML mirror

Exact mirror of https://groupleads.framer.website/ (all 23 published pages),
with every image, font, stylesheet, and the complete Framer runtime JS stored
locally. All animations, scroll effects, hovers, accordions, toggles, and
marquees work because the site runs the same Framer runtime, just served from
this folder.

## Pages (23)

- `/` (home), `/pricing`, `/features`, `/integrations`, `/compare`,
  `/resellers`, `/affiliates`, `/testimonials`, `/contact`,
  `/termsofuse`, `/privacypolicy`
- 12 comparison pages: `/vs-group-convert`, `/vs-group-funnels`,
  `/vs-group-boss`, `/vs-group-collector`, `/vs-group-kit`, `/vs-groupx`,
  `/vs-group-doorman`, `/vs-group-pro`, `/vs-social-tribes`,
  `/vs-group-buddy`, `/vs-group-answer-collector`, `/vs-group-track`

Each page is `<slug>/index.html`; the homepage is `index.html`.
All assets live under `assets/`.

## How to run

The site MUST be served over HTTP from this folder as the web root
(ES modules and `/assets/...` paths don't work from `file://` or a subfolder):

    cd groupleads-site
    python3 -m http.server 8000
    # open http://localhost:8000/

Any static host works (Netlify, Vercel, S3+CloudFront, nginx) as long as this
folder is the site root.

## Notes

- **Responsive image variants**: the original CDN served resized variants via
  `?scale-down-to=...` query params. Locally every variant resolves to the
  full-resolution original — visually identical, slightly larger downloads.
- **Analytics**: Framer's events script is included locally
  (`assets/events.framer.com/script.js`) so behavior matches the original;
  its beacons to events.framer.com fail silently offline.
- **`<link rel="preconnect">` hints** to fonts.gstatic.com remain in the HTML
  (harmless; no files are actually fetched from there).
- **External links** (YouTube embed, docs.groupleads.net, blog, Chrome Web
  Store, social profiles) intentionally still point to their live URLs,
  exactly like the original site.
- `_work/` contains the raw downloaded page HTML and `mirror.py` (the script
  that built this mirror). Safe to delete once you're happy.

## Verification performed

- All 23 pages loaded in headless Chrome against a local server:
  1,361 requests, **0 missing files** (zero 404s).
- Pixel comparison of local vs live homepage screenshots: identical.
- Interaction tests via DevTools protocol: pricing Monthly→Yearly toggle
  switches $27/$37/$57 → $97/$127/$247; FAQ accordion expands on click.
