# Take a Hike Utah

A welcoming static website encouraging people, especially youth and first-time hikers, to experience Utah's outdoors. Built with plain HTML, CSS, and JavaScript. No build, dependencies, database, analytics, credentials, external fonts, or paid services are required.

## Local review

From this repository, run:

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000` in your browser. Stop the server with Ctrl+C. Python is only a local convenience; hosting needs no Python runtime.

## Pages

- `index.html`: homepage
- `hikes.html`: beginner hike collection
- `foothill-loop.html`, `canyon-walk.html`, `lakeside-stroll.html`: sample hike descriptions
- `getting-started.html`: beginner guidance and a temporary packing checklist
- `about.html`: mission
- `contact.html`: contact placeholder; no form or message delivery
- `assets/`: shared styles, progressive-enhancement JavaScript, favicon, and original landscape artwork

All pages work without JavaScript; checklist counts and navigation highlighting are enhancements. The checklist is not stored. Links use relative paths.

## Deploy to Cloudflare Pages (free tier)

1. Commit and push these files to the GitHub repository.
2. In Cloudflare's dashboard, open **Workers & Pages**, choose **Create application**, then **Pages**, and connect your GitHub repository. Interface labels may vary; choose the Pages Git integration rather than a Worker deployment.
3. Select this repository and production branch `main`.
4. Select framework preset **None**. Leave the build command empty (use `exit 0` if the interface requires a command). Set the build output directory to `.` and leave the root directory at the repository root.
5. No environment variables or secrets are needed. Save and deploy. Cloudflare provides a `pages.dev` address with HTTPS; a custom domain is optional.
6. Review every page on the deployment, including direct visits to the individual hike HTML files and a narrow mobile viewport. Subsequent pushes to `main` trigger production deployments through the Git integration. Other branches can be used for preview deployments.

Alternatively, use Cloudflare Pages **Direct Upload** to upload the site files with `index.html` at the upload root. Exclude `.git` and local development artifacts. Git integration is preferable for automatic updates; switching an existing Direct Upload project to Git integration may require a new Pages project.

## Editorial review before public launch

This version is ready for design and content review, not verified trail navigation.

- All three hike entries are **fictional route concepts**, clearly labeled on the collection and detail pages. Replace them with verified Utah routes before presenting them as recommendations.
- Verify distances, elevation gain, estimated difficulty, exact trailhead, official source URL, access, parking, fees, permits, pet rules, facilities, accessibility, and seasonal hazards with the relevant land manager. Record the verification date. Do not invent trail statistics or map pins.
- The landscape is an original SVG illustration inspired by Utah, not a photograph of any trail. Replace or supplement it only with appropriately licensed, location-verified photographs and provide accurate alt text and credits.
- Replace the contact placeholder with an approved public email address. No messages are currently collected or sent. Avoid publishing personal contact information for minors.
- Review safety advice with appropriate local expertise. Recheck official closures, forecasts, and hazards for every outing.

## Maintenance

Edit HTML for content, `assets/styles.css` for presentation, and `assets/site.js` for optional interactions. Header and footer markup is repeated across pages; update each copy when changing navigation. No compilation step is needed. Keep assets local to preserve the dependency-free setup.
