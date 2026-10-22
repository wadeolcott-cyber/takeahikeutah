#!/usr/bin/env python3
"""Generate committed static pages. Run from any directory with Python 3."""
import json
import math
import re
import struct
from urllib.parse import urlsplit
from datetime import date
from html import escape
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
TAX = json.loads((ROOT / 'data/taxonomy.json').read_text())
HIKES = json.loads((ROOT / 'data/hikes.json').read_text())
LABELS = {key: {item['id']: item['title'] for item in values} for key, values in TAX.items()}

def e(value):
    return escape(str(value), quote=True)

def validate():
    slugs = set()
    for hike in HIKES:
        assert isinstance(hike.get('additional_photos', []), list), 'Additional photos must be a list'
        assert not hike.get('additional_photos') or hike.get('photo'), 'Gallery requires a primary photo'
        for photo in hike_photos(hike):
            validate_photo(photo)
        slug = hike['slug']
        assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug), 'Invalid slug'
        assert slug not in slugs, 'Duplicate slug'
        assert slug not in {'index', 'hikes', 'journey', 'about', 'contact', 'getting-started', 'photo-credits'}, 'Reserved slug'
        slugs.add(slug)
        assert hike['status'] in {'concept', 'pending', 'reviewed', 'verified'}
        assert hike['experience'] is None or hike['experience'] in LABELS['stages']
        assert hike['art'] in {'foothill', 'canyon', 'lake'}
        for field in ['landscapes', 'seasons', 'terrain']:
            assert isinstance(hike[field], list)
            assert all(value in LABELS[field] for value in hike[field]), field
        for field in ['distance_miles', 'elevation_gain_feet']:
            value = hike[field]
            assert value is None or (type(value) in (int, float) and math.isfinite(value) and value >= 0), field
        assert hike.get('access_status', 'not-checked') in {'not-checked', 'manual-check'}
        for source in hike['sources'] + hike.get('official_links', []):
            assert source['url'].startswith('https://') and source['title'], 'Official HTTPS source required'
        if hike['verified_on'] is not None:
            assert date.fromisoformat(hike['verified_on']) <= date.today()
        if hike['status'] in {'reviewed', 'verified'}:
            assert hike['sources'] and hike['verified_on'], 'Reviewed routes need sources and a review date'
            assert hike.get('verification_notes'), 'Reviewed routes must disclose review scope'
            source_urls = {source['url'] for source in hike['sources']}
            for field, citation in hike.get('field_sources', {}).items():
                assert citation['url'] in source_urls, f'{slug}: unlisted source for {field}'
                assert citation['kind'] in {'official', 'derived', 'editorial'} and citation['note']
            for field in ('distance_miles', 'elevation_gain_feet'):
                if hike[field] is not None:
                    assert field in hike.get('field_sources', {}), f'{slug}: missing statistic citation'

        if hike['status'] == 'verified':
            assert hike['sources'] and hike['verified_on'], 'Verified routes need sources and a review date'
            assert all(hike[x] is not None for x in ['experience', 'distance_miles', 'elevation_gain_feet', 'difficulty', 'trailhead', 'hazards'])
            assert all(hike[x] for x in ['landscapes', 'seasons', 'terrain'])


def webp_size(path):
    raw = path.read_bytes()
    assert raw[:4] == b'RIFF' and raw[8:12] == b'WEBP', 'Expected a WebP file'
    offset = 12
    while offset + 8 <= len(raw):
        kind = raw[offset:offset + 4]
        size = int.from_bytes(raw[offset + 4:offset + 8], 'little')
        body = raw[offset + 8:offset + 8 + size]
        if kind == b'VP8X':
            assert not body[0] & 2, 'Animated photos are not supported'
            return 1 + int.from_bytes(body[4:7], 'little'), 1 + int.from_bytes(body[7:10], 'little')
        if kind == b'VP8 ':
            assert body[3:6] == b'\x9d\x01\x2a', 'Invalid WebP frame'
            return struct.unpack('<H', body[6:8])[0] & 16383, struct.unpack('<H', body[8:10])[0] & 16383
        if kind == b'VP8L':
            assert body[0] == 47, 'Invalid lossless WebP'
            bits = int.from_bytes(body[1:5], 'little')
            return (bits & 16383) + 1, ((bits >> 14) & 16383) + 1
        offset += 8 + size + size % 2
    raise AssertionError('WebP dimensions missing')


def validate_photo(photo):
    for field in ('src', 'alt', 'title', 'photographer', 'source_url', 'license', 'license_url', 'modifications', 'rights_evidence'):
        assert isinstance(photo.get(field), str) and photo[field].strip(), f'Photo needs {field}'
    assert photo.get('approved') is True, 'Photo needs explicit owner approval after rights review'
    for field in ('source_url', 'license_url'):
        url = urlsplit(photo[field])
        assert url.scheme == 'https' and url.netloc, f'Photo needs HTTPS {field}'
    path = Path(photo['src'])
    assert not path.is_absolute() and '..' not in path.parts and path.suffix == '.webp', 'Photo must be local WebP'
    assert path.parts[:2] == ('assets', 'photos'), 'Store hike photos in assets/photos/'
    full = (ROOT / path).resolve()
    assert full.is_relative_to((ROOT / 'assets/photos').resolve()) and full.is_file(), 'Missing local photo'
    width, height = webp_size(full)
    assert 0 < width <= 1600 and 0 < height <= 1600, 'Photo dimensions must be at most 1600px'
    assert full.stat().st_size <= 400_000, 'Photo must be at most 400KB; optimize it first'
    return width, height


def photo_credit(photo):
    return (f'<span>“{e(photo["title"])}” — Photo by {e(photo["photographer"])}. '
            f'<a href="{e(photo["source_url"])}">Source</a> · '
            f'<a href="{e(photo["license_url"])}">{e(photo["license"])}</a>. '
            f'Modifications: {e(photo["modifications"])}.</span>')


def credit_id(photo):
    return 'photo-' + Path(photo['src']).stem


def compact_photo_credit(photo):
    target = 'photo-credits.html#' + credit_id(photo)
    credit = f'Photo: {e(photo["photographer"])}'
    if photo['license'].startswith('CC BY-SA '):
        license_label = photo['license'].split(' —')[0]
        credit = (f'“{e(photo["title"])}” · Photo: <a href="{e(photo["source_url"])}">{e(photo["photographer"])}</a>'
                  f' · <a href="{e(photo["license_url"])}">{e(license_label)}</a> · WebP conversion')
    return f'<span>{credit} · <a href="{e(target)}">Photo credits</a></span>'


def hike_photos(hike):
    return ([hike['photo']] if hike.get('photo') else []) + hike.get('additional_photos', [])


def photo_figure(photo):
    width, height = validate_photo(photo)
    caption = f'<p>{e(photo["caption"])}</p>' if photo.get('caption') else ''
    return (f'<figure class="hike-photo"><img src="{e(photo["src"])}" alt="{e(photo["alt"])}" '
            f'width="{width}" height="{height}" loading="lazy" decoding="async">'
            f'<figcaption>{caption}{compact_photo_credit(photo)}</figcaption></figure>')


def hike_photo(hike):
    photo = hike.get('photo')
    if not photo:
        return f'<div class="detail-art {e(hike["art"])}" role="img" aria-label="Image placeholder: illustration, not a photograph of this trail"><span class="image-placeholder-label">Illustration · trail photograph coming later</span></div>'
    return ''.join(photo_figure(photo) for photo in hike_photos(hike))


def photo_credits():
    entries = ''.join(f'<article id="{e(credit_id(photo))}"><h2><a href="{e(h["slug"])}.html">{e(h["title"])}</a></h2><p>{photo_credit(photo)}</p></article>' for h in HIKES for photo in hike_photos(h))
    return ('<section class="wrap section"><h1 class="page-title">Photo Credits</h1>'
            '<p class="lede">Thank you to the photographers whose work helps us explore Utah.</p>'
            '<div class="reading"><h2>Homepage: Bryce Canyon</h2>'
            '<p>Photo by the Take a Hike Utah site owner, who confirmed personally taking this photograph and authorized its use on this website. Copyright remains with the photographer; no public reuse license is granted. Source: owner-supplied WebP. Display modifications: responsive sizing and cropping for the homepage layout. Earlier editing history has not been recorded. Contact the site owner for reuse permission.</p>'
            '<h2 id="clouds-rest">Clouds Rest: our 100th summit</h2><p>The founder’s family photograph, supplied in the existing site repository and approved for the About page. Photographer not recorded. No public reuse license is granted here; contact the site owner about permission. Displayed with its existing framing; no image edits made for this update.</p><h2 id="owner-photos">Owner-supplied photographs</h2><p>Personal photos credited to the Take a Hike Utah site owner are used with the photographer’s permission. Copyright remains with the photographer; all rights reserved. No public reuse license is granted. Contact the site owner for reuse permission.</p><h2>Trail photographs</h2>' + (entries or '<p>No trail photographs have been added yet. Hike pages currently use illustrations, clearly labeled as placeholders.</p>') +
            '<h2>Illustrations</h2><p>The landscape illustration and site icon were created for this website. They are not photographs of individual trails. No public reuse license is granted here.</p>'
            '<p>A credit is not permission to reuse an image. Consult the linked license and original source, and obtain any additional permissions required for your use.</p></div></section>')


def labels(hike, key):
    return ', '.join(LABELS[key][value] for value in hike[key]) or 'To be verified'


def stats(hike):
    stage = LABELS['stages'].get(hike['experience'], 'To be assessed')
    if hike['status'] == 'concept':
        stage += ' (concept only)'
    rows = [('Location', hike.get('location') or 'To be confirmed'), ('Experience', stage), ('Landscape', labels(hike, 'landscapes')),
            ('Planning seasons', labels(hike, 'seasons')),
            ('Distance', 'Not published in reviewed official sources' if hike['distance_miles'] is None and hike['status'] == 'reviewed' else 'Awaiting source review' if hike['distance_miles'] is None else f"{hike['distance_miles']:g} miles"),
            ('Elevation gain', (hike.get('elevation_display') or ('Cumulative gain not published in reviewed official sources' if hike['status'] == 'reviewed' else 'Awaiting source review')) if hike['elevation_gain_feet'] is None else f"{hike['elevation_gain_feet']:g} feet"),
            ('Approximate duration', hike.get('duration') or 'Not confirmed by official source'), ('Route type', hike.get('route_type') or 'To be verified'), ('Trail surface', hike.get('surface') or 'Not confirmed by official source'), ('Terrain', labels(hike, 'terrain')), ('Estimated difficulty', hike['difficulty'] or 'To be assessed'),
            ('Trailhead', hike['trailhead'] or 'To be confirmed')]
    return '<dl class="stats">' + ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in rows) + '</dl>'


def card(hike, index):
    attrs = {'experience': hike['experience'] or '', 'landscape': ' '.join(hike['landscapes']),
             'season': ' '.join(hike['seasons']), 'terrain': ' '.join(hike['terrain']),
             'distance': '' if hike['distance_miles'] is None else hike['distance_miles'],
             'elevation': '' if hike['elevation_gain_feet'] is None else hike['elevation_gain_feet']}
    data = ' '.join(f'data-{key}="{e(value)}"' for key, value in attrs.items())
    badge = {'concept': 'SAMPLE ROUTE', 'pending': 'RESEARCH PENDING', 'reviewed': 'SOURCE-REVIEWED', 'verified': 'TRAIL GUIDE'}[hike['status']]
    stage = LABELS['stages'].get(hike['experience'], 'Experience to be assessed')
    photo = hike.get('photo')
    thumbnail = ''
    if photo:
        width, height = validate_photo(photo)
        thumbnail = f'<img class="card-photo" src="{e(photo["src"])}" alt="" width="{width}" height="{height}" loading="lazy" decoding="async">'
    art_class = 'has-photo' if photo else e(hike['art'])
    image_note = e(photo.get('card_note', 'Photo · credits in guide')) if photo else 'Illustration · photo placeholder'
    return f'''<article class="card hike-card" {data}>
<a class="card-art {art_class}" href="{e(hike['slug'])}.html" aria-label="Explore {e(hike['title'])}">{thumbnail}<span class="pill">{badge}</span><span class="art-number">{index:02}</span><span class="card-image-note">{image_note}</span></a>
<div class="card-body"><p class="eyebrow">{e(hike['subtitle'])}</p><h3><a href="{e(hike['slug'])}.html">{e(hike['title'])}</a></h3><p>{e(hike['description'])}</p>{access_warning(hike)}<p class="card-meta">{e(stage)}{' · concept only' if hike['status'] == 'concept' else ''}</p><div class="card-bottom"><span>{'View route details' if hike['status'] in {'reviewed', 'verified'} else 'Trail details unverified'}</span><a href="{e(hike['slug'])}.html" aria-label="View {e(hike['title'])}">↗</a></div></div></article>'''


def access_warning(hike):
    if hike.get('access_status') == 'manual-check':
        return '<p class="access-warning">Manual access verification required · construction</p>'
    return ''


def stage_hikes(stage):
    entries = [h for h in HIKES if h['experience'] == stage and h['status'] != 'concept']
    if not entries:
        return ''
    return '<h3>Explore First Steps routes</h3><p>Explore Utah’s landscapes through these First Steps selections. Some guides have source-reviewed facts; others still need research or manual access verification. Read each entry’s notices before planning.</p><ul class="stage-hike-links">' + ''.join(f'<li><a href="{e(h["slug"])}.html">{e(h["title"])}</a> — {e(h.get("location", ""))}' + (' · <strong>Manual access verification required</strong>' if h.get('access_status') == 'manual-check' else '') + '</li>' for h in entries) + '</ul>'


def journey_cards():
    return '<div class="journey-grid">' + ''.join(f'''<article class="journey-card"><p class="eyebrow">STAGE {i:02}</p><h3><a href="journey.html#{e(s['id'])}">{e(s['title'])}</a></h3><p>{e(s['summary'])}</p><a class="underlined" href="hikes.html?experience={e(s['id'])}">Explore this stage ↗</a></article>''' for i, s in enumerate(TAX['stages'], 1)) + '</div>'


SEASONS = [('spring', 'Spring', 'Changing weather, muddy trails, and lingering snow can affect access. Check conditions at your route’s elevation; lower ground is not automatically clear or safe.'),
           ('summer', 'Summer', 'Plan around heat and thunderstorms. Higher elevations may still hold snow. Check forecasts and water needs, and have a conservative turnaround plan.'),
           ('fall', 'Fall', 'Shorter days and colder nights change your margin for error. Pack layers and lighting, and check for early snow and access restrictions.'),
           ('winter', 'Winter', 'Snow, ice, and avalanche terrain require specialized assessment and skills. A summer trail rating does not describe winter difficulty. Seek appropriate training and official forecasts.')]


def options(key):
    return ''.join(f'<option value="{e(item["id"])}">{e(item["title"])}</option>' for item in TAX[key])


def build():
    validate()
    hero = ROOT / "assets/BryceCanyon.webp"
    assert max(webp_size(hero)) <= 2048 and hero.stat().st_size <= 600_000, "Optimize homepage WebP"
    shell = Template((ROOT / 'templates/page.html').read_text())
    def page(filename, title, body):
        (ROOT / filename).write_text(shell.substitute(title=e(title), body=body) + '\n')
    page('photo-credits.html', 'Photo Credits', photo_credits())
    cards = '<div class="cards">' + ''.join(card(h, i) for i, h in enumerate([h for h in HIKES if h['status'] in {'reviewed', 'verified'}][:3], 1)) + '</div>'
    journey_home = '<section class="wrap section"><p class="eyebrow">GROW AT YOUR OWN PACE</p><h2>Your Hiking Journey</h2><p class="section-intro">From a first walk to thoughtful, self-reliant adventures. Pick the stage that fits today. There’s no race, and harder isn’t always better.</p>' + journey_cards() + '</section>'
    explore_home = '<section class="explore-band"><div class="wrap"><p class="eyebrow">MANY LANDSCAPES. EVERY SEASON.</p><h2>Discover more of Utah.</h2><p>Explore foothills, canyons, desert, mountain forests, and waterways. Learn how the seasons change your planning.</p><div class="explore-links">' + ''.join(f'<a href="journey.html#landscape-{x["id"]}">{e(x["title"])} ↗</a>' for x in TAX['landscapes']) + '</div><a class="underlined" href="journey.html#seasons">Explore seasonal planning →</a></div></section>'
    page('index.html', 'Your first step starts here', Template((ROOT / 'templates/home.html').read_text()).substitute(journey_home=journey_home, explore_home=explore_home, cards=cards))
    for name, title in [('about', 'Our mission'), ('contact', 'Contact'), ('getting-started', 'Getting started')]:
        page(name + '.html', title, (ROOT / f'templates/{name}.html').read_text())
    stage_sections = ''.join(f'''<article id="{s['id']}" class="journey-detail"><p class="eyebrow">STAGE {i:02}</p><h2>{e(s['title'])}</h2><p class="lede">{e(s['summary'])}</p><p>{e(s['advice'])}</p><a class="underlined" href="hikes.html?experience={s['id']}">Browse this stage →</a>{stage_hikes(s["id"])}</article>''' for i, s in enumerate(TAX['stages'], 1))
    landscape_notes = ['Build familiarity with navigation and pacing close to town. Check heat, exposure, and access.', 'Terrain varies widely. Research flood risk, route-finding, and any technical obstacles before choosing a route.', 'Plan carefully for heat, sun exposure, water, fragile soils, and remote access.', 'Elevation, weather, snow, and steep terrain can change the demands of an outing.', 'Check shoreline access, changing water levels, and crossing hazards. Do not assume water is safe to drink.']
    landscape_sections = ''.join(f'<article id="landscape-{x["id"]}"><h3>{e(x["title"])}</h3><p>{e(note)}</p><a class="underlined" href="hikes.html?landscape={x["id"]}">Browse this landscape →</a></article>' for x, note in zip(TAX['landscapes'], landscape_notes))
    seasonal_sections = ''.join(f'<article><h3>{title}</h3><p>{e(note)}</p><a class="underlined" href="hikes.html?season={key}">Browse {title.lower()} guides →</a></article>' for key, title, note in SEASONS)
    page('journey.html', 'Your Hiking Journey', f'''<section class="wrap section"><p class="eyebrow">A LIFETIME OF SMALL STEPS</p><h1 class="page-title">Your Hiking Journey</h1><p class="lede">Grow in confidence, judgment, and care for the outdoors. Start where you are and revisit the basics whenever you need.</p><aside class="notice">Stages are a guide to learning, not certifications or fixed difficulty ratings. Choose routes for your whole group, current conditions, and relevant skills. Mentoring means supporting others’ choices, not pushing their limits.</aside>{stage_sections}<section id="landscapes" class="journey-detail"><p class="eyebrow">EXPLORE UTAH</p><h2>A landscape for your curiosity.</h2><p>These are general planning considerations, not route recommendations. Landscape alone does not determine difficulty.</p><div class="advice-grid">{landscape_sections}</div></section><section id="seasons" class="journey-detail"><p class="eyebrow">PLAN FOR THE DAY YOU GO</p><h2>Every season changes the journey.</h2><p>A seasonal label is a planning starting point, never a report of current conditions. Check official forecasts, closures, and land-manager guidance before every trip.</p><div class="advice-grid">{seasonal_sections}</div></section><a class="button dark" href="getting-started.html">Revisit the essentials ↗</a></section>''')
    entries = [h for h in HIKES if h['status'] != 'concept']
    listing_groups = '<section class="result-group"><h2>First Steps routes</h2><div class="cards">' + ''.join(card(h, i) for i, h in enumerate(entries, 1)) + '</div></section>'
    fields = ''.join(f'<label>{label}<select name="{name}"><option value="">Any {label.lower()}</option>{options(key)}</select></label>' for name, label, key in [('experience', 'Experience stage', 'stages'), ('landscape', 'Landscape', 'landscapes'), ('season', 'Season', 'seasons'), ('terrain', 'Terrain', 'terrain')])
    fields += '<label>Distance<select name="distance"><option value="">Any distance</option><option value="short">Up to 3 miles</option><option value="medium">Over 3 to 8 miles</option><option value="long">Over 8 miles</option></select></label><label>Elevation gain<select name="elevation"><option value="">Any elevation gain</option><option value="low">Up to 500 feet</option><option value="moderate">Over 500 to 1,500 feet</option><option value="high">Over 1,500 feet</option></select></label>'
    page('hikes.html', 'Find a hike', f'''<section class="wrap section"><p class="eyebrow">FIND THE OUTING THAT FITS TODAY</p><h1 class="page-title">Find your kind of outside.</h1><p class="lede">Explore by experience, landscape, season, and the demands of the route.</p><aside class="notice"><strong>Trail collection in progress.</strong> Explore eight First Steps routes. Source-reviewed guides cite official information and disclose missing statistics. Bridal Veil Falls has a source review with missing statistics and still requires manual construction/access verification. Unknown attributes do not match specific filters. Seasonal labels guide planning, not current access or safety.</aside><form id="hike-filters" class="filter-panel" hidden><h2>Find a Hike</h2><div class="filter-grid">{fields}</div><div class="filter-actions"><button type="reset" class="button dark">Reset filters</button><p id="result-count" role="status" aria-live="polite"></p></div><p class="filter-note">Filters combine: results must match every selection. Season is not current trail status, and experience stage is not a safety rating.</p></form><noscript><p>The complete collection is shown below. Enable JavaScript to filter it.</p></noscript><div id="hike-results">{listing_groups}</div><div id="no-results" class="notice" hidden><h2>No matching guides yet.</h2><p>We’re building this part of the collection. Try fewer filters or explore the learning guide while verified routes are prepared.</p><a class="underlined" href="journey.html">Explore your hiking journey →</a></div><div class="bottom-callout"><h2>Choose for the whole group.</h2><p>Distance and climbing are only part of the picture. Consider terrain, exposure, daylight, weather, relevant skills, and everyone’s energy. Check the official land manager’s current information before every outing.</p><a class="underlined" href="journey.html">Build skills for your next step →</a></div></section>''')
    detail_template = Template((ROOT / 'templates/hike.html').read_text())
    for hike in HIKES:
        concept = hike['status'] == 'concept'
        pending = hike['status'] == 'pending'
        notice = ('<strong>Planning placeholder — not a verified trail guide.</strong> No real route or trailhead has been selected for this concept.' if concept else
                  '<strong>Research pending — not a verified trail guide.</strong> This is a requested real route, but official-source verification has not been completed. Do not rely on this draft to plan or navigate an outing.' if pending else
                  '<strong>Plan for current conditions.</strong> Available official route information has been reviewed; missing statistics are disclosed below. Current access is not guaranteed. Check official closures, forecasts, and route information before every outing.')
        sources = ''.join(f'<li><a href="{e(source["url"])}">{e(source["title"])}</a></li>' for source in hike['sources'])
        official = ''.join(f'<li><a href="{e(source["url"])}">{e(source["title"])}</a></li>' for source in hike.get('official_links', []))
        source_section = '<h2>Official information and verification</h2>'
        if sources:
            source_section += f'<ul>{sources}</ul><p>Last source review: {e(hike["verified_on"] or "Incomplete")}</p>'
        else:
            source_section += '<p>Official route verification has not been completed. No verification date is claimed.</p>'
        if official:
            source_section += f'<h3>Official websites to consult</h3><ul>{official}</ul><p>These links are research starting points, not citations for unverified statistics.</p>'
        source_section += '<p>' + e(hike.get('verification_notes') or 'Official route sources and route-specific details still need review.') + '</p>'
        access_notice = ''
        if hike.get('access_note'):
            access_notice = '<aside class="notice access-notice"><strong>' + ('Manual access verification required' if hike.get('access_status') == 'manual-check' else 'Access not verified') + '</strong>' + e(hike['access_note']) + '</aside>'
        body = detail_template.substitute(
            photo=hike_photo(hike),
            badge={'concept': 'SAMPLE ROUTE CONCEPT', 'pending': 'RESEARCH PENDING', 'reviewed': 'SOURCE-REVIEWED', 'verified': 'TRAIL GUIDE'}[hike['status']],
            title=e(hike['title']), subtitle=e(hike['subtitle']), description=e(hike['description']), art=e(hike['art']),
            notice=notice, access_notice=access_notice, stats=stats(hike), about_heading='The kind of outing we have in mind' if concept else 'Why this hike is worthwhile',
            preparation=e(hike['preparation']), hazards=e(hike['hazards'] or 'Route-specific hazards have not been verified. Check the land manager’s advice before choosing this outing.'),
            season_notes=e(hike.get('season_notes') or 'Seasonal suitability has not been confirmed. No season is recommended by this draft.'),
            weather_notes=e(hike.get('weather_notes') or 'Check official forecasts and alerts. Heat, cold, storms, snow, and ice can change the demands of an outing.'),
            fees=e(hike.get('fees') or 'Fees and pass requirements have not been verified. Check the official land-manager website; do not assume free entry.'),
            access_restrictions=e(hike.get('access_restrictions') or 'Confirm trail and parking access, closures, permits, pet rules, operating hours, and any construction restrictions with the land manager.'),
            source_section=source_section)
        page(hike['slug'] + '.html', hike['title'], body)
    print(f'Generated {7 + len(HIKES)} static pages from {len(HIKES)} hike records.')


if __name__ == '__main__':
    build()
