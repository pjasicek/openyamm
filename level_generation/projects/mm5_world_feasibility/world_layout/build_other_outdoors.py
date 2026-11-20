#!/usr/bin/env python3
"""Complete the 16-map overview with source schematics for sky and elemental layers."""

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

from build_world_layout import HERE, ROOT, LAYOUT, svgHeader, svgText, writeSvg
from concept_sheets import conceptsReady, viewportPreviews, renderConceptSheets


SOURCE = ROOT / 'reference/mm4_5_world_of_xeen/unpacked/maps/dark_initial_state'
INVENTORY = json.loads((HERE.parent / 'inventory.json').read_text())
SKY_ACCESS = {
    'nw': ['Alamar upper entrance', 'Fire-plane gateway'],
    'nc': ['Olympus; Northern Tower', 'Great Pyramid summit'],
    'ne': ['Blackfang upper entrance', 'Air-plane gateway'],
    'sw': ['Western Tower; Ellinger; Kalindra', 'Dark Grove rope; Water gateway'],
    'sc': ['Southern Tower upper entrance'],
    'se': ['Eastern Tower; sky merchants', 'Boatman; Earth-plane gateway'],
}
PLANE_INFO = [
    (25, 'Fire', 'nw', 'Sky A1', 'Lava / obsidian; hostile heat'),
    (26, 'Air', 'ne', 'Sky F1', 'Clouds / exposed platforms'),
    (27, 'Earth', 'se', 'Sky F4', 'Dirt / rock; elemental landmarks'),
    (28, 'Water', 'sw', 'Sky A4', 'Water; traversal must be designed'),
]
COLORS = {0: '#367fa0', 1: '#846844', 5: '#d45121', 10: '#253d5b', 11: '#b9a385',
          13: '#cdd8df', 15: '#111820'}


def block(number, scale):
    stem = f'maze{"x" if number >= 100 else "0"}{number:03}.dat.json'
    data = json.loads((SOURCE / stem).read_text())
    image = Image.new('RGB', (16*scale, 16*scale))
    draw = ImageDraw.Draw(image)
    for y, row in enumerate(data['cells']):
        for x, cell in enumerate(row):
            ground = data['surfaceTypes'][cell['layers'][0]]
            color = COLORS[ground]
            xx, yy = x*scale, (15-y)*scale
            draw.rectangle((xx, yy, xx+scale-1, yy+scale-1), fill=color)
    for site in INVENTORY['sites']:
        if site['map'] != number or not site['spatial']:
            continue
        x, y = (site['x']+.5)*scale, (15-site['y']+.5)*scale
        color = '#fff099' if site['npcTitles'] else '#72e5da' if site['transfers'] else None
        if color:
            draw.ellipse((x-2, y-2, x+2, y+2), fill=color, outline='#101820')
    return image


def build():
    conceptsReady()
    manifest = []
    sky = Image.new('RGB', (1152, 768))
    for region in LAYOUT['regions']:
        source = next(r for r in INVENTORY['regions'] if r['id'] == region['id'])
        for number in source['skyMaps']:
            surface = number-88
            sky.paste(block(number, 12), (((surface-1)//4)*192, ((surface-1)%4)*192))
        manifest.append(dict(id='surface_'+region['id'], layer='surface', sourceMaps=source['sourceMaps'],
                             name=region['title'], preview='regions/'+region['id']+'.png'))
    sky.save(HERE / 'sky_terrain.png')
    for region in LAYOUT['regions']:
        x, y = region['column']*384, region['row']*384
        preview='regions/sky_'+region['id']+'.png'
        sky.crop((x, y, x+384, y+384)).save(HERE / preview)
        source = next(r for r in INVENTORY['regions'] if r['id'] == region['id'])
        manifest.append(dict(id='sky_'+region['id'], layer='sky', name='Sky '+region['id'].upper(),
                             sourceMaps=source['skyMaps'], preview=preview, access=SKY_ACCESS[region['id']]))
    for number, name, region, square, treatment in PLANE_INFO:
        preview='regions/plane_'+name.lower()+'.png'
        block(number, 18).save(HERE / preview)
        manifest.append(dict(id='plane_'+name.lower(), layer='plane', name=name, sourceMaps=[number],
                             preview=preview, entranceRegion='sky_'+region, entranceSquare=square,
                             treatment=treatment))

    parts = svgHeader(1232, 960)
    parts += [svgText(40, 40, 'MM5 — THE SIX SKYROAD REGIONS', 25),
              svgText(40, 70, 'Same geographic alignment as the surface; sparse routes above it', 16, '#b9c4c8'),
              '<g transform="translate(40 95)">',
              '<image xlink:href="sky_terrain.png" width="1152" height="768"/>']
    for region in LAYOUT['regions']:
        x, y = region['column']*384, region['row']*384
        parts += [f'<rect x="{x}" y="{y}" width="384" height="384" fill="none" stroke="#dfc785" stroke-width="2"/>',
                  f'<rect x="{x+8}" y="{y+8}" width="368" height="73" fill="#111820" opacity=".88"/>',
                  svgText(x+18, y+30, 'SKY '+region['id'].upper(), 18)]
        for i, text in enumerate(SKY_ACCESS[region['id']]):
            parts.append(svgText(x+18, y+50+i*18, text, 12, '#b9c4c8'))
    parts += ['</g>', svgText(40, 898, 'Tan: source skyroads   Pale: cloud terrain   Blue: open sky   Cyan dots: scripted transfers   Yellow: NPC sites', 13),
              svgText(40, 925, 'Source schematic, not a passability map. Cloud traversal, falls, flight and event gates require a dedicated prototype.', 13, '#b9c4c8')]
    writeSvg('sky_source_map', parts, 1232, 960)

    parts = svgHeader(1320, 570)
    parts += [svgText(40, 40, 'MM5 — FOUR SEPARATE ELEMENTAL PLANES', 25),
              svgText(40, 70, 'Original 16 × 16 source areas; final occupied footprint is not fixed', 16, '#b9c4c8')]
    for index, info in enumerate(PLANE_INFO):
        number, name, region, square, treatment = info
        x = 35+index*320
        parts += [svgText(x, 108, name.upper(), 20),
                  f'<image x="{x}" y="125" width="288" height="288" xlink:href="regions/plane_{name.lower()}.png"/>',
                  svgText(x, 442, 'Entry: '+square+' / '+region.upper(), 14),
                  svgText(x, 468, treatment, 12, '#b9c4c8')]
    parts += [svgText(35, 515, 'Source terrain and NPC/transfer markers only; objects, encounters and final elemental scenery are not depicted.', 13, '#b9c4c8'),
              svgText(35, 540, 'Gateway entries and return/fall routes are separate directed records. See OUTDOOR_LAYERS.md for the Water return discrepancy.', 13, '#b9c4c8')]
    writeSvg('elemental_source_planes', parts, 1320, 570)

    manifest = viewportPreviews(manifest)
    renderConceptSheets()

    parts = svgHeader(1232, 1510)
    parts += [svgText(40, 42, 'MM5 — ALL 16 PROPOSED OUTDOOR MAPS', 25),
              svgText(40, 73, '6 surface + 6 sky + 4 elemental · three distinct layers of geography', 16, '#b9c4c8')]
    for layer, title, top in [('surface', 'SURFACE — 6 regional landscapes', 115),
                              ('sky', 'SKYROADS — 6 corresponding regions', 640)]:
        parts.append(svgText(40, top, title, 21))
        for region in LAYOUT['regions']:
            item = next(m for m in manifest if m['id'] == layer+'_'+region['id'])
            x, y = 40+region['column']*400, top+25+region['row']*225
            parts += [f'<rect x="{x}" y="{y}" width="380" height="205" fill="#223039"/>',
                      f'<image x="{x+8}" y="{y+8}" width="185" height="185" xlink:href="{item["preview"]}"/>',
                      svgText(x+205, y+30, region['id'].upper(), 19)]
            lines = region['title'].split(' / ') if layer=='surface' else SKY_ACCESS[region['id']]
            # Access details are provided on the dedicated sky sheet; use short names on the full index.
            if layer=='sky':
                lines = ['Above '+region['id'].upper(), region['title'].split(' / ')[0]]
            for i, line in enumerate(lines):
                parts.append(svgText(x+205, y+60+i*22, line, 12, '#d0dbd6'))
    parts.append(svgText(40, 1142, 'ELEMENTAL PLANES — 4 independent destinations, entered from the sky layer', 21))
    for index, info in enumerate(PLANE_INFO):
        _, name, region, square, _ = info
        x, y = 40+index*300, 1170
        parts += [f'<image x="{x}" y="{y}" width="190" height="190" xlink:href="concepts/plane_{name.lower()}.png"/>',
                  svgText(x, y+215, name, 18), svgText(x, y+238, 'Entry: '+square, 13, '#b9c4c8')]
    parts += [svgText(40, 1460, 'Surface: source-derived textured relief. Sky/planes: minimap concepts using MM8 Air and MM7 Celeste visual references.', 13, '#b9c4c8'),
              svgText(40, 1487, 'These are map-planning groups, not 16 completed ODMs; occupied area, sky movement and plane mechanics remain to be designed.', 13, '#b9c4c8')]
    writeSvg('all_outdoors', parts, 1232, 1510)
    assert len(manifest) == 16
    ids = [number for item in manifest for number in item['sourceMaps']]
    assert sorted(ids) == list(range(1,29))+list(range(89,113))
    routes = [t for t in INVENTORY['transfers'] if t['spatial'] and
              (25 <= t['source'] <= 28 or 25 <= t.get('destination',0) <= 28)]
    result = dict(total=16, counts={'surface':6, 'sky':6, 'plane':4}, maps=manifest,
                  sourceOutdoorMapsCoveredExactlyOnce=len(ids), elementalDirectedEvents=routes,
                  inventorySha256=hashlib.sha256((HERE.parent/'inventory.json').read_bytes()).hexdigest())
    (HERE/'outdoor_manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    (HERE/'other_outdoors.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>All 16 MM5 outdoor maps</title>
<style>body{background:#111820;color:#eee5cd;font:16px system-ui;margin:25px}a{color:#a8d7ec}
img{display:block;width:100%;max-width:1320px;height:auto;margin:25px 0}p{max-width:1100px;line-height:1.6}</style>
<h1>All 16 proposed MM5 outdoor maps</h1><p>Six surface regions, six corresponding Skyroad regions and four separate
elemental planes. The previous terrain overview covered the six surface regions.</p>
<p><a href="index.html">Surface detail</a> · <a href="OUTDOOR_LAYERS.md">Layer and access notes</a> ·
<a href="outdoor_manifest.json">Complete manifest</a></p>
<p><a href="#sky">Skyroads</a> · <a href="#planes">Elemental planes</a> ·
<a href="MINIMAP_CONCEPTS.md">Concept decisions and prompts</a> ·
<a href="native_sky_references/README.md">Native Air / Celeste references</a></p>
<img src="all_outdoors.png" alt="All sixteen outdoor map groups">
<h2 id="sky">Skyroads</h2><img src="sky_map.png" alt="Six aligned sky regions">
<h2 id="planes">Elemental planes</h2><img src="elemental_planes.png" alt="Four separate elemental planes">
<p>The sky and plane views now show proposed textured minimap concepts. They are not native game renders or passability
results. Original event coordinates and directed travel remain in the manifest; added landforms are design proposals.</p>
<details><summary>Original source schematics — geography and event evidence</summary>
<img src="sky_source_map.png" alt="Original sky terrain schematic">
<img src="elemental_source_planes.png" alt="Original elemental plane schematics"></details></html>''')
    print('Covered all 52 original outdoor logical maps exactly once in 16 proposed groups.')


if __name__ == '__main__':
    build()
