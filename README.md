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
3. Use `status: "concept"` until a real route is verified. `experience` can be a taxonomy stage ID or `null`; a concept stage describes editorial intent, not a verified route rating.
4. Use taxonomy IDs for `landscapes`, `seasons`, and `terrain` arrays. Leave unknown arrays empty. Set unknown numeric and text fields to `null`; never use `0` to mean unknown. Distance is total outing miles and elevation gain is cumulative feet; state any route variant in the description.
5. Record official sources as `{"title": "Official trail information", "url": "https://..."}` and `verified_on` as `YYYY-MM-DD`. Verify the route, statistics, terrain, seasonal suitability, trailhead, difficulty, access, parking, fees, permits, accessibility, pet rules, facilities, and hazards with the land manager. Explain limitations in the description and preparation fields. A season is general suitability, never live conditions.
6. Change status to `verified` only after editorial verification. The generator requires populated route attributes, official source links, hazards, and a review date. Its validation checks structure, not factual accuracy; the editor must verify facts.
7. Run from the repository root:

   ```sh
   python3 scripts/build.py
   ```

8. Review the generated HTML and commit the data, template, and generated-page changes together. All generated pages are committed so hosting needs no build. Do not directly edit generated HTML; regeneration will overwrite it.

Current generated pages are `index.html`, `hikes.html`, `journey.html`, `about.html`, `getting-started.html`, `contact.html`, and each hike detail page. Edit CSS and JavaScript directly in `assets/`. To remove a hike, remove its record and explicitly delete its old generated page or provide a redirect; the generator deliberately does not delete unrelated HTML files.

## Filters

Find a Hike supports experience, landscape, season, terrain, distance, and elevation gain. Filters combine with AND; a route must match every selection. Numeric ranges use miles and feet and have explicit boundaries. Missing values never match a specific filter. Current sample records therefore match First Steps but not landscape, season, terrain, distance, or elevation filters.

Filter selections are stored in URL query parameters (`experience`, `landscape`, `season`, `terrain`, `distance`, `elevation`) so links can be shared. Unknown parameter values are ignored. All hike cards and detail content are rendered in HTML and remain available without JavaScript. Empty stages explain that the collection is growing. The beginner checklist is temporary and resets on reload.

## Deploy to Cloudflare Pages (free tier)

1. Push the committed files, including generated HTML, to GitHub.
2. In Cloudflare **Workers & Pages**, create a **Pages** project with Git integration and select this repository.
3. Set production branch to `main`, framework preset to **None**, build command empty (or `exit 0` if required), output directory to `.`, and root directory to the repository root. No secrets or environment variables are needed.
4. Deploy and review the supplied HTTPS `pages.dev` address or your configured domain. Future pushes to `main` trigger production deployments; use another branch for review previews.
5. Check the homepage, direct hike URLs, journey anchors, and filtered links on mobile and desktop. If an old stylesheet is cached, hard-refresh or test a private window.

You may optionally set the build command to `python3 scripts/build.py` if Python 3 is available in your Cloudflare build image, but this is not required: the committed files are already deployable. Direct Upload also works with `index.html` at the upload root; exclude `.git` and local artifacts.

## Editorial status

The three existing hikes are fictional route concepts, not verified recommendations. No route distances, elevation gains, terrain, trailheads, or seasonal conditions have been invented. Higher experience levels currently provide learning guidance rather than populated hike catalogs. Stage labels are not certifications, safety ratings, or promises of accessibility.

The homepage uses the supplied `assets/BryceCanyon.webp`. Other landscape imagery is original illustrative SVG, not location-specific trail photography. The contact page remains a placeholder and collects no messages. Add an approved public email before launch. General learning guidance does not replace appropriate training, current forecasts, or official land-manager information.

## Validation

Run `python3 scripts/check.py` for generation repeatability, data validation, internal links, and structural checks. Run `node --check assets/site.js` for JavaScript syntax. Also review filtering (including empty results, reset, and shared URLs), keyboard navigation, mobile layouts, and no-JavaScript behavior in a browser.
