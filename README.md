# Take a Hike Utah

A welcoming static website helping people, especially youth, grow from their first hike into confident, thoughtful hikers. Four stages guide that journey: **First Steps**, **Find Your Stride**, **Reach New Heights**, and **Beyond the Trail**.

Plain HTML, CSS, and JavaScript. No runtime dependencies, databases, accounts, paid services, credentials, or external assets are needed. Python 3 is used only to maintain generated pages and optionally serve them locally.

## Review locally

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000` on the same machine. Stop with Ctrl+C.

## Maintain and add hikes

The single source for hike content is `data/hikes.json`. The shared vocabulary for experience stages, landscapes, seasons, and terrain is `data/taxonomy.json`. Page framing and editorial pages live in `templates/`; the dependency-free generator is `scripts/build.py`.

1. Copy a hike record in `data/hikes.json` and give it a unique lowercase hyphenated `slug`. Its URL will be `<slug>.html`. Keep existing slugs stable so links continue working.
2. Supply title, subtitle, description, preparation, and an illustration style (`foothill`, `canyon`, or `lake`). Illustrations are never represented as trail photographs.
3. Use `status: "concept"` for fictional route ideas, `"pending"` for requested real routes awaiting research, `"reviewed"` for source-reviewed routes with explicitly disclosed gaps, and `"verified"` only when all required route fields are confirmed. `experience` can be a taxonomy stage ID or `null`; a concept stage describes editorial intent, not a verified route rating.
4. Use taxonomy IDs for `landscapes`, `seasons`, and `terrain` arrays. Leave unknown arrays empty. Set unknown numeric and text fields to `null`; never use `0` to mean unknown. Distance is total outing miles and elevation gain is cumulative feet; state any route variant in the description.
5. Record official sources as `{"title": "Official trail information", "url": "https://..."}` and `verified_on` as `YYYY-MM-DD`. Verify the route, statistics, terrain, seasonal suitability, trailhead, difficulty, access, parking, fees, permits, accessibility, pet rules, facilities, and hazards with the land manager. Explain limitations in the description and preparation fields. A season is general suitability, never live conditions.
6. Use `reviewed` after reading and citing official sources, even if a source omits statistics. Document gaps in `verification_notes`; never fill them from memory. `verified` retains the stricter requirement for complete route attributes. Both reviewed statuses require citations and a review date. Numeric fields require matching `field_sources` entries. Validation checks structure, not factual accuracy; the editor must verify facts.
7. Run from the repository root:

   ```sh
   python3 scripts/build.py
   ```

8. Review the generated HTML and commit the data, template, and generated-page changes together. All generated pages are committed so hosting needs no build. Do not directly edit generated HTML; regeneration will overwrite it.

Current generated pages are `index.html`, `hikes.html`, `journey.html`, `about.html`, `getting-started.html`, `contact.html`, and each hike detail page. Edit CSS and JavaScript directly in `assets/`. To remove a hike, remove its record and explicitly delete its old generated page or provide a redirect; the generator deliberately does not delete unrelated HTML files.

## Filters

Find a Hike supports experience, landscape, season, terrain, distance, and elevation gain. Filters combine with AND; a route must match every selection. Numeric ranges use miles and feet and have explicit boundaries. Missing values never match a specific filter. The eight real routes and three original concepts are classified First Steps. All eight routes have official-source reviews with missing attributes disclosed. Bridal Veil Falls has landscape/terrain tags but no planning-season tags and still requires manual construction/access verification. Unknown attributes never match a specific filter. The hike listing displays only real routes; original concept pages are retained at their existing URLs.

Filter selections are stored in URL query parameters (`experience`, `landscape`, `season`, `terrain`, `distance`, `elevation`) so links can be shared. Unknown parameter values are ignored. All hike cards and detail content are rendered in HTML and remain available without JavaScript. Empty stages explain that the collection is growing. The beginner checklist is temporary and resets on reload.

## Deploy to Cloudflare Pages (free tier)

1. Push the committed files, including generated HTML, to GitHub.
2. In Cloudflare **Workers & Pages**, create a **Pages** project with Git integration and select this repository.
3. Set production branch to `main`, framework preset to **None**, build command `python3 scripts/build.py`, output directory to `.`, and root directory to the repository root. No secrets or environment variables are needed.
4. Deploy and review the supplied HTTPS `pages.dev` address or your configured domain. Future pushes to `main` trigger production deployments; use another branch for review previews.
5. Check the homepage, direct hike URLs, journey anchors, and filtered links on mobile and desktop. If an old stylesheet is cached, hard-refresh or test a private window.

Keep the build command enabled so each deployment regenerates SEO files from the deployed pages. The committed files also support hosts without a build step; the sitemap GitHub Action refreshes them on pushes to `main` (requires Actions write permission and branch rules permitting the bot commit). Direct Upload also works with `index.html` at the upload root; exclude `.git` and local artifacts.

## Editorial status

Eight real First Steps entries now have individual pages and links from the journey guide and hike listing. All eight have source-reviewed facts, with missing fields disclosed. Bridal Veil Falls retains its manual construction/access warning. The three original fictional concepts retain their URLs. No unverified statistic or current-access claim is supplied. `docs/first-steps-sources.md` records source scope and unresolved checks. Approximate walking times are official where published; Ladyfinger Point and Capitol Reef Sunset Point use clearly labeled editorial estimates. Higher experience levels currently provide learning guidance rather than populated hike catalogs. Stage labels are not certifications, safety ratings, or promises of accessibility.

The homepage uses the supplied `assets/BryceCanyon.webp`. Other landscape imagery is original illustrative SVG, not location-specific trail photography. Bridal Veil Falls has a prominent manual access verification warning because the project owner reported construction; its extent and current access remain unverified. All trail imagery is clearly labeled illustrative placeholder content. The contact page remains a placeholder and collects no messages. Add an approved public email before launch. General learning guidance does not replace appropriate training, current forecasts, or official land-manager information.

## Validation

Run `python3 scripts/check.py` for generation repeatability, data validation, internal links, and structural checks. Run `node --check assets/site.js` for JavaScript syntax. Also review filtering (including empty results, reset, and shared URLs), keyboard navigation, mobile layouts, and no-JavaScript behavior in a browser.

## Extended route fields

Real-route records support `location`, `duration` (include whether sourced or editorial estimate), `route_type`, `surface`, `fees`, `access_restrictions`, `season_notes`, `weather_notes`, `access_status`, `access_note`, `verification_notes`, `official_links`, and `field_sources`. Unknown values remain `null` or empty lists, never invented statistics. `field_sources` maps a field name to a listed source URL, a supporting note, and `kind` (`official`, `derived`, or `editorial`). `official_links` are unreviewed research destinations, not evidence that a route fact was verified; reviewed citations go in `sources`.

`access_status` is deliberately separate from factual review: `not-checked` or `manual-check`. Neither asserts that a route is open. Bridal Veil Falls must retain `manual-check` until construction and route access have been checked directly with the relevant authority.

The shared detail layout is `templates/hike.html`. The First Steps section in `journey.html` links all eight named routes. The homepage features the first three source-reviewed routes rather than expanding into an eleven-card catalog. The original concept URLs remain functional and labeled as concepts.

A source’s **elevation change** is not silently converted to **cumulative elevation gain**. For Sand Dune Arch and Capitol Reef Sunset Point, the official wording is shown in `elevation_display` while numeric gain stays unknown and does not match gain filters. Missing published numbers are not zeros. All seasonal labels are planning aids; editorial selections are identified in each route’s season notes. No page asserts that a trail is currently open.

## Photos and copyright

See [the photo workflow](docs/photos.md) for local WebP preparation, owner approval, license records, attribution, and image-size limits. Each hike has an optional `photo` record; `null` keeps its existing illustration. The build generates `photo-credits.html` and links it from every footer. Run `python3 scripts/test_photos.py` when changing photo handling. Pillow is optional editing tooling only; production and the site generator remain dependency-free.

## XML sitemap and robots

`scripts/build.py` regenerates root-level `sitemap.xml` and `robots.txt` using Python's standard library. The sitemap discovers public HTML files recursively, including new hike pages, and uses `https://takeahikeutah.org` with Cloudflare Pages' extensionless HTML URLs (`/` for `index.html`). Deploy the repository root as documented above so both SEO files are served at the domain root.

Concept/pending hikes and the placeholder contact page receive `noindex, follow` without changing their appearance or availability. Remove the contact exclusion in `scripts/build.py` when a real contact method is published. For other unpublished pages, add `<meta name="robots" content="noindex, follow">` to their source template or static HTML. Templates, documentation, tooling, assets, hidden directories, error pages, meta-refresh redirects, and pages canonicalized elsewhere are excluded. Keep draft/placeholder pages marked noindex; do not store them as unmarked public HTML. Only publish redirects using Cloudflare's canonical extensionless routes; remove obsolete HTML when replacing a page with a redirect.

Dates are omitted unless an editor supplies `<meta name="date-modified" content="YYYY-MM-DD">` in a page's source. Update this only when that page's content changes. Trail source-review dates, filesystem timestamps, and build times are not modification dates.

Run `python3 scripts/check.py` to validate XML, unique canonical URLs, file targets, exclusions, dates, and repeatable generation. After deployment, run `python3 scripts/verify_live_sitemap.py` to request every sitemap URL plus the root SEO files, rejecting redirects and non-200 responses. This requires network access to the canonical domain.
