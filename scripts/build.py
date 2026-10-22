#!/usr/bin/env python3
"""Generate committed static pages. Run from any directory with Python 3."""
import json
import re
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
        slug = hike['slug']
        assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug), 'Invalid slug'
        assert slug not in slugs, 'Duplicate slug'
        assert slug not in {'index', 'hikes', 'journey', 'about', 'contact', 'getting-started'}, 'Reserved slug'
        slugs.add(slug)
        assert hike['status'] in {'concept', 'verified'}
        assert hike['experience'] is None or hike['experience'] in LABELS['stages']
        assert hike['art'] in {'foothill', 'canyon', 'lake'}
        for field in ['landscapes', 'seasons', 'terrain']:
            assert isinstance(hike[field], list)
            assert all(value in LABELS[field] for value in hike[field]), field
        for field in ['distance_miles', 'elevation_gain_feet']:
            value = hike[field]
            assert value is None or (type(value) in (int, float) and value >= 0), field
        for source in hike['sources']:
            assert source['url'].startswith('https://') and source['title'], 'Official HTTPS source required'
        if hike['verified_on'] is not None:
            assert date.fromisoformat(hike['verified_on']) <= date.today()
        if hike['status'] == 'verified':
            assert hike['sources'] and hike['verified_on'], 'Verified routes need sources and a review date'
            assert all(hike[x] is not None for x in ['experience', 'distance_miles', 'elevation_gain_feet', 'difficulty', 'trailhead', 'hazards'])
            assert all(hike[x] for x in ['landscapes', 'seasons', 'terrain'])


def labels(hike, key):
    return ', '.join(LABELS[key][value] for value in hike[key]) or 'To be verified'


def stats(hike):
    stage = LABELS['stages'].get(hike['experience'], 'To be assessed')
    if hike['status'] == 'concept':
        stage += ' (concept only)'
    rows = [('Experience', stage), ('Landscape', labels(hike, 'landscapes')),
            ('Season', labels(hike, 'seasons')),
            ('Distance', 'To be verified' if hike['distance_miles'] is None else f"{hike['distance_miles']:g} miles"),
            ('Elevation gain', 'To be verified' if hike['elevation_gain_feet'] is None else f"{hike['elevation_gain_feet']:g} feet"),
            ('Terrain', labels(hike, 'terrain')), ('Estimated difficulty', hike['difficulty'] or 'To be assessed'),
            ('Trailhead', hike['trailhead'] or 'To be confirmed')]
    return '<dl class="stats">' + ''.join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in rows) + '</dl>'


def card(hike, index):
    attrs = {'experience': hike['experience'] or '', 'landscape': ' '.join(hike['landscapes']),
             'season': ' '.join(hike['seasons']), 'terrain': ' '.join(hike['terrain']),
             'distance': '' if hike['distance_miles'] is None else hike['distance_miles'],
             'elevation': '' if hike['elevation_gain_feet'] is None else hike['elevation_gain_feet']}
    data = ' '.join(f'data-{key}="{e(value)}"' for key, value in attrs.items())
    badge = 'SAMPLE ROUTE' if hike['status'] == 'concept' else 'TRAIL GUIDE'
    stage = LABELS['stages'].get(hike['experience'], 'Experience to be assessed')
    return f'''<article class="card hike-card" {data}>
<a class="card-art {e(hike['art'])}" href="{e(hike['slug'])}.html" aria-label="Explore {e(hike['title'])}"><span class="pill">{badge}</span><span class="art-number">{index:02}</span></a>
<div class="card-body"><p class="eyebrow">{e(hike['subtitle'])}</p><h3><a href="{e(hike['slug'])}.html">{e(hike['title'])}</a></h3><p>{e(hike['description'])}</p><p class="card-meta">{e(stage)}{' · concept only' if hike['status'] == 'concept' else ''}</p><div class="card-bottom"><span>{'Trail details unverified' if hike['status'] == 'concept' else 'View route details'}</span><a href="{e(hike['slug'])}.html" aria-label="View {e(hike['title'])}">↗</a></div></div></article>'''


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
    shell = Template((ROOT / 'templates/page.html').read_text())
    def page(filename, title, body):
        (ROOT / filename).write_text(shell.substitute(title=e(title), body=body) + '\n')
    cards = '<div class="cards">' + ''.join(card(h, i) for i, h in enumerate(HIKES, 1)) + '</div>'
    journey_home = '<section class="wrap section"><p class="eyebrow">GROW AT YOUR OWN PACE</p><h2>Your Hiking Journey</h2><p class="section-intro">From a first walk to thoughtful, self-reliant adventures. Pick the stage that fits today. There’s no race, and harder isn’t always better.</p>' + journey_cards() + '</section>'
    explore_home = '<section class="explore-band"><div class="wrap"><p class="eyebrow">MANY LANDSCAPES. EVERY SEASON.</p><h2>Discover more of Utah.</h2><p>Explore foothills, canyons, desert, mountain forests, and waterways. Learn how the seasons change your planning.</p><div class="explore-links">' + ''.join(f'<a href="journey.html#landscape-{x["id"]}">{e(x["title"])} ↗</a>' for x in TAX['landscapes']) + '</div><a class="underlined" href="journey.html#seasons">Explore seasonal planning →</a></div></section>'
    page('index.html', 'Your first step starts here', Template((ROOT / 'templates/home.html').read_text()).substitute(journey_home=journey_home, explore_home=explore_home, cards=cards))
    for name, title in [('about', 'Our mission'), ('contact', 'Contact'), ('getting-started', 'Getting started')]:
        page(name + '.html', title, (ROOT / f'templates/{name}.html').read_text())
    stage_sections = ''.join(f'''<article id="{s['id']}" class="journey-detail"><p class="eyebrow">STAGE {i:02}</p><h2>{e(s['title'])}</h2><p class="lede">{e(s['summary'])}</p><p>{e(s['advice'])}</p><a class="underlined" href="hikes.html?experience={s['id']}">Browse this stage →</a></article>''' for i, s in enumerate(TAX['stages'], 1))
    landscape_notes = ['Build familiarity with navigation and pacing close to town. Check heat, exposure, and access.', 'Terrain varies widely. Research flood risk, route-finding, and any technical obstacles before choosing a route.', 'Plan carefully for heat, sun exposure, water, fragile soils, and remote access.', 'Elevation, weather, snow, and steep terrain can change the demands of an outing.', 'Check shoreline access, changing water levels, and crossing hazards. Do not assume water is safe to drink.']
    landscape_sections = ''.join(f'<article id="landscape-{x["id"]}"><h3>{e(x["title"])}</h3><p>{e(note)}</p><a class="underlined" href="hikes.html?landscape={x["id"]}">Browse this landscape →</a></article>' for x, note in zip(TAX['landscapes'], landscape_notes))
    seasonal_sections = ''.join(f'<article><h3>{title}</h3><p>{e(note)}</p><a class="underlined" href="hikes.html?season={key}">Browse {title.lower()} guides →</a></article>' for key, title, note in SEASONS)
    page('journey.html', 'Your Hiking Journey', f'''<section class="wrap section"><p class="eyebrow">A LIFETIME OF SMALL STEPS</p><h1 class="page-title">Your Hiking Journey</h1><p class="lede">Grow in confidence, judgment, and care for the outdoors. Start where you are and revisit the basics whenever you need.</p><aside class="notice">Stages are a guide to learning, not certifications or fixed difficulty ratings. Choose routes for your whole group, current conditions, and relevant skills. Mentoring means supporting others’ choices, not pushing their limits.</aside>{stage_sections}<section id="landscapes" class="journey-detail"><p class="eyebrow">EXPLORE UTAH</p><h2>A landscape for your curiosity.</h2><p>These are general planning considerations, not route recommendations. Landscape alone does not determine difficulty.</p><div class="advice-grid">{landscape_sections}</div></section><section id="seasons" class="journey-detail"><p class="eyebrow">PLAN FOR THE DAY YOU GO</p><h2>Every season changes the journey.</h2><p>A seasonal label is a planning starting point, never a report of current conditions. Check official forecasts, closures, and land-manager guidance before every trip.</p><div class="advice-grid">{seasonal_sections}</div></section><a class="button dark" href="getting-started.html">Revisit the essentials ↗</a></section>''')
    fields = ''.join(f'<label>{label}<select name="{name}"><option value="">Any {label.lower()}</option>{options(key)}</select></label>' for name, label, key in [('experience', 'Experience stage', 'stages'), ('landscape', 'Landscape', 'landscapes'), ('season', 'Season', 'seasons'), ('terrain', 'Terrain', 'terrain')])
    fields += '<label>Distance<select name="distance"><option value="">Any distance</option><option value="short">Up to 3 miles</option><option value="medium">Over 3 to 8 miles</option><option value="long">Over 8 miles</option></select></label><label>Elevation gain<select name="elevation"><option value="">Any elevation gain</option><option value="low">Up to 500 feet</option><option value="moderate">Over 500 to 1,500 feet</option><option value="high">Over 1,500 feet</option></select></label>'
    page('hikes.html', 'Find a hike', f'''<section class="wrap section"><p class="eyebrow">FIND THE OUTING THAT FITS TODAY</p><h1 class="page-title">Find your kind of outside.</h1><p class="lede">Explore by experience, landscape, season, and the demands of the route.</p><aside class="notice"><strong>Trail collection in progress.</strong> All current entries are illustrative First Steps concepts, not verified Utah routes. Other stages will grow as guides are verified. Landscape, season, distance, elevation, and terrain remain unknown; concepts do not match filters for those attributes. Do not use these pages for navigation.</aside><form id="hike-filters" class="filter-panel" hidden><h2>Find a Hike</h2><div class="filter-grid">{fields}</div><div class="filter-actions"><button type="reset" class="button dark">Reset filters</button><p id="result-count" role="status" aria-live="polite"></p></div><p class="filter-note">Filters combine: results must match every selection. Season is not current trail status, and experience stage is not a safety rating.</p></form><noscript><p>The complete collection is shown below. Enable JavaScript to filter it.</p></noscript><div class="cards" id="hike-results">{''.join(card(h, i) for i, h in enumerate(HIKES, 1))}</div><div id="no-results" class="notice" hidden><h2>No matching guides yet.</h2><p>We’re building this part of the collection. Try fewer filters or explore the learning guide while verified routes are prepared.</p><a class="underlined" href="journey.html">Explore your hiking journey →</a></div><div class="bottom-callout"><h2>Choose for the whole group.</h2><p>Distance and climbing are only part of the picture. Consider terrain, exposure, daylight, weather, relevant skills, and everyone’s energy. Check the official land manager’s current information before every outing.</p><a class="underlined" href="journey.html">Build skills for your next step →</a></div></section>''')
    for hike in HIKES:
        concept = hike['status'] == 'concept'
        notice = '<strong>Planning placeholder — not a verified trail guide.</strong> No real route or trailhead has been selected for this concept. The illustration does not depict a specific location.' if concept else '<strong>Plan for current conditions.</strong> This guide is not a live conditions report. Check official closures, forecasts, and route information before heading out. The illustration is not a trail photograph.'
        sources = ''.join(f'<li><a href="{e(s["url"])}">{e(s["title"])}</a></li>' for s in hike['sources'])
        source_section = f'<h2>Sources and review</h2><ul>{sources}</ul><p>Last editorial verification: {e(hike["verified_on"])}</p>' if sources else '<h2>Verification still needed</h2><p>No official route sources have been recorded. Distance, terrain, seasonal suitability, trailhead access, parking, fees, permits, accessibility, pet rules, facilities, and hazards must be checked before publishing a real recommendation.</p>'
        page(hike['slug'] + '.html', hike['title'], f'''<section class="wrap section"><a class="breadcrumb" href="hikes.html">← All hikes and concepts</a><p class="eyebrow">{'SAMPLE ROUTE CONCEPT' if concept else 'TRAIL GUIDE'} · {e(hike['subtitle'])}</p><h1 class="page-title">{e(hike['title'])}.</h1><p class="lede">{e(hike['description'])}</p><div class="detail-art {e(hike['art'])}" role="img" aria-label="Stylized landscape illustration, not a photograph of this trail"></div><aside class="notice">{notice}</aside>{stats(hike)}<div class="reading"><h2>{'The kind of outing we have in mind' if concept else 'About the route'}</h2><p>{e(hike['description'])}</p><h2>Preparation</h2><p>{e(hike['preparation'])}</p><h2>Hazards and conditions</h2><p>{e(hike['hazards'] or 'Route-specific hazards have not been assessed. Do not assume this concept describes a safe, accessible, or currently open trail.')}</p>{source_section}<a class="button dark" href="journey.html">Build your trail confidence ↗</a></div></section>''')
    print(f'Generated {6 + len(HIKES)} static pages from {len(HIKES)} hike records.')


if __name__ == '__main__':
    build()
