#!/usr/bin/env python3
"""Create source-derived cartography for the MM5 surface proposal, not native game maps."""

from collections import Counter
import csv
import hashlib
import html
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter, label, map_coordinates, distance_transform_edt


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / 'reference/mm4_5_world_of_xeen/unpacked/maps/dark_initial_state'
SCALE = 16
WIDTH, HEIGHT = 96 * SCALE, 64 * SCALE
LAYOUT = json.loads((HERE / 'layout.json').read_text())
INPUTS = {HERE / 'layout.json', ROOT / 'test_img/1253.png', ROOT / 'test_img/mm6_worldmap.jpg'}
SURFACES = ['water', 'dirt', 'grass', 'snow', 'swamp', 'lava', 'desert', 'road', 'deep_water',
            'floor', 'sky', 'road', 'sewer', 'cloud', 'scorched', 'space']


def sourceXY(source):
    number, x, y = source
    return ((number - 1) // 4) * 16 + x, ((number - 1) % 4) * 16 + 15 - y


def point(source):
    x, y = sourceXY(source)
    return (x + .5) * SCALE, (y + .5) * SCALE


def loadSource():
    ground = np.zeros((64, 96), dtype=np.uint8)
    wall = ground.copy()
    scenery = ground.copy()
    blocks = {}
    for number in range(1, 25):
        path = SOURCE / f'maze0{number:03}.dat.json'
        INPUTS.add(path)
        block = json.loads(path.read_text())
        blocks[number] = block
        for y, row in enumerate(block['cells']):
            for x, cell in enumerate(row):
                xx, yy = sourceXY([number, x, y])
                ground[yy, xx] = block['surfaceTypes'][cell['layers'][0]]
                wall[yy, xx] = cell['layers'][1]
                scenery[yy, xx] = block['wallTypes'][cell['layers'][1]]
    return ground, wall, scenery, blocks


def texturePath(key):
    world, name = key.split(':')
    for folder in [ROOT / f'assets_dev/worlds/{world}/textures', ROOT / 'assets_dev/engine/terrain',
                   ROOT / 'assets_dev/engine/textures']:
        for path in folder.glob('*'):
            if path.stem.lower() == name and path.suffix.lower() in ('.bmp', '.png'):
                INPUTS.add(path)
                return path
    raise ValueError(f'Missing palette texture: {key}')


def nativeTexture(key):
    rgb = np.array(Image.open(texturePath(key)).convert('RGB'), dtype=float)
    chroma = (rgb[:, :, 0] > 245) & (rgb[:, :, 1] < 10) & (rgb[:, :, 2] > 245)
    rgb[chroma] = [36, 77, 104]
    return Image.fromarray(rgb.astype(np.uint8))


def repeatTexture(key):
    tile = np.array(nativeTexture(key).resize((24, 24), Image.BOX), dtype=float)
    return np.tile(tile, (HEIGHT // 24 + 1, WIDTH // 24 + 1, 1))[:HEIGHT, :WIDTH]


def renderTerrain(ground, scenery):
    """Illustrative hillshade from scenery classes; water/void membership stays source-exact."""
    rng = np.random.default_rng(501)
    yy, xx = np.indices((HEIGHT, WIDTH))
    coords = [(yy + .5) / SCALE - .5, (xx + .5) / SCALE - .5]
    enlarged = lambda a: np.repeat(np.repeat(a, SCALE, axis=0), SCALE, axis=1)
    smooth = lambda a, sigma: gaussian_filter(enlarged(a).astype(float), sigma * SCALE)
    mountain = np.isin(scenery, [1, 7, 9, 10, 12])
    forest = np.isin(scenery, [2, 3, 5, 6, 8, 11, 13, 14, 15])
    sourceWater = np.isin(ground, [0, 8]) & ~mountain
    water = smooth(sourceWater, .18) > .5
    void = smooth(ground == 15, .18) > .5
    assert np.array_equal(water[SCALE//2::SCALE, SCALE//2::SCALE], sourceWater)
    assert label(water)[1] == label(sourceWater)[1]
    base = ground.copy()
    base[np.isin(base, [0, 8])] = 0
    base[np.isin(base, [7, 11])] = 1
    base[mountain] = 16
    base[scenery == 7] = 3
    base[scenery == 10] = 14
    palette = {0: 'mm8:wtrtyl', 1: 'mm8:dirttyl', 2: 'mm8:grastyl', 3: 'mm7:7snow',
               4: 'mm8:gstyl', 5: 'mm8:lavtyl', 6: 'mm7:7sand', 14: 'mm8:plntyl',
               15: 'mm8:dirttyl', 16: 'mm8:rctyl'}
    assert set(np.unique(base)) <= set(palette), set(np.unique(base)) - set(palette)
    rgb = np.zeros((HEIGHT, WIDTH, 3), dtype=float)
    weightSum = np.zeros((HEIGHT, WIDTH), dtype=float)
    for code in np.unique(base):
        weight = smooth(base == code, .16)
        rgb += repeatTexture(palette[int(code)]) * weight[:, :, None]
        weightSum += weight
    rgb /= np.maximum(weightSum[:, :, None], .001)

    # Native texture color with large-scale illumination and fine grain; no invented coastline.
    noise = rng.normal(size=(64, 96))
    broad = map_coordinates(gaussian_filter(noise, 1.4), coords, order=1, mode='nearest')
    relief = smooth(mountain, .65) * 145 + broad * 28
    relief += gaussian_filter(rng.normal(size=(HEIGHT, WIDTH)), 7) * 22
    dy, dx = np.gradient(relief)
    shade = np.clip(.96 - .30 * dx - .40 * dy, .44, 1.48)
    rgb *= shade[:, :, None]
    rgb *= (1 + broad[:, :, None] * .12)
    wood = smooth(forest, .2)
    snowWood = enlarged(np.isin(scenery, [5, 6]))
    darkWood = enlarged(scenery == 3)
    rgb *= (1 - wood[:, :, None] * .28)
    rgb[:, :, 1] += wood * 13

    # Necropolis: a declared local art-direction overlay, without altering source geometry.
    nx, ny = point([6, 8, 12])
    necro = np.exp(-(((xx - nx) / 55) ** 2 + ((yy - ny) / 48) ** 2))
    necro *= enlarged(np.isin(ground, [1, 6, 14])) * .62
    rgb = rgb * (1 - necro[:, :, None]) + repeatTexture('mm8:gstyl') * necro[:, :, None]

    depth = distance_transform_edt(water)
    deep = enlarged(ground == 8)
    ripples = np.sin(xx * .37 + yy * .08) * 2 + np.sin(yy * .43) * 2
    waterRgb = np.empty_like(rgb)
    for channel, color in enumerate([43, 91, 124]):
        waterRgb[:, :, channel] = color + 14 * np.exp(-depth / 8) - deep * 12 + ripples
    rgb[water] = waterRgb[water]
    lava = smooth((ground == 5) & ~mountain, .18) > .5
    rgb[lava] = rgb[lava] * .45 + np.array([180, 54, 14]) * .55
    rgb[void] = [17, 24, 31]
    image = Image.fromarray(np.uint8(np.clip(rgb, 0, 255)))
    draw = ImageDraw.Draw(image)

    # Small top-down crowns suggest the source forests, with source water kept untouched.
    for _ in range(14500):
        x, y = int(rng.integers(WIDTH)), int(rng.integers(HEIGHT))
        if wood[y, x] < .65 or water[y, x] or void[y, x] or rng.random() > wood[y, x]:
            continue
        radius = int(rng.integers(2, 5))
        color = (99, 124, 119) if snowWood[y, x] else (35, 70, 35) if darkWood[y, x] else (63, 95, 40)
        draw.ellipse((x-radius+1, y-radius+2, x+radius+1, y+radius+2), fill=(24, 43, 29))
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)
        draw.point((x-1, y-1), fill=tuple(min(255, v+30) for v in color))

    # Retain exactly the source road graph; avoid decorative spurs to every landmark.
    roads = np.isin(ground, [7, 11])
    for y, x in zip(*np.where(roads)):
        a = ((x+.5)*SCALE, (y+.5)*SCALE)
        for dx, dy in [(1, 0), (0, 1)]:
            if x+dx < 96 and y+dy < 64 and roads[y+dy, x+dx]:
                b = ((x+dx+.5)*SCALE, (y+dy+.5)*SCALE)
                draw.line([a, b], fill=(73, 57, 37), width=6)
                draw.line([a, b], fill=(182, 151, 97), width=3)
    image.save(HERE / 'world_terrain.png')
    (HERE / 'regions').mkdir(exist_ok=True)
    for region in LAYOUT['regions']:
        x, y = region['column'] * 512, region['row'] * 512
        image.crop((x, y, x+512, y+512)).save(HERE / 'regions' / f'{region["id"]}.png')
    return image


def verifyTravel(ground, wall, blocks):
    # Conservative terrain-only screen: no swimming, water walking, mountaineering or lava damage.
    # Raw middle nibble controls movement; mapped scenery is only for visual classification.
    walk = ~np.isin(ground, [0, 5, 8, 10, 13, 15]) & ~np.isin(wall, [1, 5, 7, 9, 10, 12])
    components, _ = label(walk)
    startX, startY = sourceXY([4, 14, 11])
    mainComponent = components[startY, startX]
    assert mainComponent > 0
    rows = []
    for connection in LAYOUT['connections']:
        source, destination = connection['source'], connection['destination']
        ax, ay = sourceXY(source)
        bx, by = sourceXY(destination)
        assert abs(ax-bx) + abs(ay-by) == 1
        assert components[ay, ax] == components[by, bx] == mainComponent
        direction = 'east' if bx > ax else 'west' if bx < ax else 'south' if by > ay else 'north'
        opposite = {'east': 'west', 'west': 'east', 'north': 'south', 'south': 'north'}[direction]
        assert blocks[source[0]]['neighbors'][direction] == destination[0]
        assert blocks[destination[0]]['neighbors'][opposite] == source[0]
        road = int(ground[ay, ax]) in (7, 11) and int(ground[by, bx]) in (7, 11)
        assert road == (connection['kind'] == 'road')
        rows.append(dict(id=connection['id'], kind=connection['kind'], source=source, destination=destination,
                         sourceGround=SURFACES[ground[ay, ax]], destinationGround=SURFACES[ground[by, bx]],
                         reciprocalNeighbors=True, connectedToCastleviewByTerrain=True, travelDays=None))
    with (HERE / 'foot_connections.csv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def svgText(x, y, text, size=16, color='#eee5cd', extra=''):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" {extra}>'
            f'{html.escape(text)}</text>')


def svgHeader(width, height):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            'font-family="DejaVu Sans, sans-serif">',
            f'<rect width="{width}" height="{height}" fill="#111820"/>']


def writeSvg(name, parts, width, height):
    path = HERE / f'{name}.svg'
    path.write_text('\n'.join(parts + ['</svg>']))
    import gi
    gi.require_version('Rsvg', '2.0')
    from gi.repository import Rsvg
    import cairo
    handle = Rsvg.Handle.new_from_file(str(path))
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    handle.render_cairo(cairo.Context(surface))
    surface.write_to_png(str(HERE / f'{name}.png'))


def worldMap():
    width, height = WIDTH+80, HEIGHT+220
    parts = svgHeader(width, height)
    parts += [svgText(40, 37, 'DARKSIDE OF XEEN', 25, extra='font-weight="bold"'),
              svgText(40, 64, 'Surface study v1 · six equal travel areas · north up', 15, '#b9c4c8'),
              '<g transform="translate(40 90)">',
              f'<image xlink:href="world_terrain.png" width="{WIDTH}" height="{HEIGHT}"/>',
              '<g id="source-grid" opacity=".22">']
    for x in range(256, WIDTH, 256):
        parts.append(f'<path d="M{x} 0V{HEIGHT}" stroke="#f8f0cb" stroke-dasharray="3 7"/>')
    for y in range(256, HEIGHT, 256):
        parts.append(f'<path d="M0 {y}H{WIDTH}" stroke="#f8f0cb" stroke-dasharray="3 7"/>')
    parts += ['</g>', '<g id="regions">']
    for region in LAYOUT['regions']:
        x, y = region['column']*512, region['row']*512
        parts.append(f'<rect x="{x}" y="{y}" width="512" height="512" fill="none" '
                     'stroke="#dfc785" stroke-width="2"/>')
        parts.append(f'<rect x="{x+8}" y="{y+8}" width="496" height="43" rx="3" fill="#101820" opacity=".85"/>')
        parts.append(svgText(x+18, y+28, region['id'].upper()+'  '+region['title'], 16,
                             extra='font-weight="bold"'))
        parts.append(svgText(x+18, y+44, ' · '.join(region['squares']), 11, '#b9c5b4'))
    parts += ['</g>', '<g id="labels">']
    occupied = [(r['column']*512+8, r['row']*512+8, r['column']*512+504, r['row']*512+51)
                for r in LAYOUT['regions']]
    for landmark in LAYOUT['landmarks']:
        x, y = point(landmark['source'])
        name, kind = landmark['name'], landmark['kind']
        color = '#9cd3e5' if kind == 'water' else '#efe2b3'
        if kind in ('town', 'castle'):
            parts.append(f'<rect x="{x-5}" y="{y-5}" width="10" height="10" fill="{color}" stroke="#171e24" stroke-width="2"/>')
        else:
            parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}" stroke="#171e24" stroke-width="1.5"/>')
        textWidth = len(name)*7.5 + 10
        chosen = None
        for dx, dy in [(10, 4), (-textWidth-10, 4), (10, -12), (10, 22), (-textWidth-10, -12),
                       (10, 36), (-textWidth-10, 36), (10, -32)]:
            tx, ty = x+dx, y+dy
            box = (tx-3, ty-14, tx+textWidth, ty+4)
            if box[0] < 3 or box[2] > WIDTH-3 or box[1] < 52:
                continue
            if any(box[0]<b[2] and box[2]>b[0] and box[1]<b[3] and box[3]>b[1] for b in occupied):
                continue
            chosen = box
            break
        assert chosen is not None, f'No clear label placement for {name}'
        occupied.append(box)
        if abs(ty-y) > 20:
            parts.append(f'<path d="M{x} {y}L{tx-3 if tx>x else tx+textWidth} {ty-4}" '
                         f'stroke="{color}" stroke-width="1" opacity=".8"/>')
        parts.append(svgText(tx, ty, name, 13, '#101820',
                            extra='stroke="#101820" stroke-width="3" stroke-linejoin="round"'))
        parts.append(svgText(tx, ty, name, 13, color))
    parts += ['</g>', '<g id="crossings">']
    for connection in LAYOUT['connections']:
        a, b = point(connection['source']), point(connection['destination'])
        x, y = (a[0]+b[0])/2, (a[1]+b[1])/2
        color = '#f7da8b' if connection['kind'] == 'road' else '#85dfdf'
        parts.append(f'<path d="M{x} {y-8}l8 8-8 8-8-8Z" fill="{color}" stroke="#111820" stroke-width="2"/>')
    parts += ['</g>', '</g>',
              svgText(40, HEIGHT+120, 'Gold diamonds: road crossings    Cyan diamonds: proposed off-road crossing anchors', 14),
              svgText(40, HEIGHT+146, 'Geography from all 24 MM5 surface grids; native MM8 ground textures + MM7 snow/sand. Relief is illustrative.', 13, '#b9c4c8'),
              svgText(40, HEIGHT+170, 'Landmark symbols are source anchors, not final building footprints. The dark outer rim is world-edge space, not sea.', 13, '#b9c4c8'),
              svgText(40, HEIGHT+194, 'First region: SW Castleview / Kalindra. Native map generation follows town-footprint and terrain-bank review.', 13, '#dccc94')]
    writeSvg('world_map', parts, width, height)


def travelMap():
    width, height = 1320, 820
    parts = svgHeader(width, height)
    parts += [svgText(40, 45, 'MM5 — SURFACE FOOT TRAVEL', 25, extra='font-weight="bold"'),
              svgText(40, 75, 'Seven neighboring links · four roads · three off-road approaches', 16, '#b9c4c8')]
    positions = {r['id']: (90+r['column']*430, 140+r['row']*310) for r in LAYOUT['regions']}
    for connection in LAYOUT['connections']:
        ax, ay = positions[connection['a']]
        bx, by = positions[connection['b']]
        if ax == bx:
            ax, ay, bx, by = ax+140, min(ay, by)+210, bx+140, max(ay, by)
        else:
            ax, ay, bx, by = min(ax, bx)+280, ay+105, max(ax, bx), by+105
        color = '#f7da8b' if connection['kind'] == 'road' else '#85dfdf'
        dash = '' if connection['kind'] == 'road' else 'stroke-dasharray="8 7"'
        parts.append(f'<path d="M{ax} {ay}L{bx} {by}" stroke="{color}" stroke-width="4" {dash}/>')
    for region in LAYOUT['regions']:
        x, y = positions[region['id']]
        parts.append(f'<image x="{x}" y="{y}" width="280" height="210" preserveAspectRatio="none" '
                     f'xlink:href="regions/{region["id"]}.png"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="280" height="210" fill="none" stroke="#b7c3b1" stroke-width="2"/>')
        parts.append(f'<rect x="{x}" y="{y+126}" width="280" height="84" fill="#111820" opacity=".93"/>')
        parts.append(svgText(x+12, y+149, region['id'].upper(), 17, '#f3d98d', 'font-weight="bold"'))
        title = region['title'].split(' / ')
        for i, text in enumerate(title):
            parts.append(svgText(x+12, y+172+i*19, text, 15))
        if region['id'] == 'sw':
            parts.append(svgText(x+182, y+149, 'START HERE', 11, '#b5efa0'))
    parts += [svgText(40, 732, 'Solid gold = source road connection    Dashed cyan = terrain-supported off-road connection', 16),
              svgText(40, 760, 'Link positions are schematic. Exact source crossing cells are marked on the terrain map and recorded in foot_connections.csv.', 13, '#b9c4c8'),
              svgText(40, 784, 'Terrain-only checks exclude water/lava/mountaineering. Events, danger, travel days and final arrival points remain to be authored.', 13, '#b9c4c8')]
    writeSvg('foot_travel', parts, width, height)


def palettePlate():
    fontPath = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    font = ImageFont.truetype(fontPath, 17)
    small = ImageFont.truetype(fontPath, 13)
    image = Image.new('RGB', (1200, 1050), '#111820')
    draw = ImageDraw.Draw(image)
    draw.text((30, 20), 'MM5 WORLD — NATIVE MATERIAL STARTING PALETTE', font=font, fill='#eee5cd')
    draw.text((30, 50), 'Actual local texture swatches; biome recipes still need transition-bank and scenery review.', font=small, fill='#b9c4c8')
    evidence = []
    for index, palette in enumerate(LAYOUT['palettes']):
        y = 90+index*104
        draw.text((30, y), palette['name'], font=font, fill='#eee5cd')
        draw.text((30, y+25), palette['donor'], font=small, fill='#b9c4c8')
        for n, key in enumerate(palette['textures']):
            x = 505+n*225
            image.paste(nativeTexture(key).resize((72, 72), Image.NEAREST), (x, y))
            draw.text((x+80, y+8), key.split(':')[0], font=small, fill='#b9c4c8')
            draw.text((x+80, y+29), key.split(':')[1], font=small, fill='#eee5cd')
            evidence.append(dict(palette=palette['id'], key=key, path=str(texturePath(key).relative_to(ROOT))))
    image.save(HERE / 'tileset_palette.png')
    (HERE / 'palette_sources.json').write_text(json.dumps(evidence, indent=2)+'\n')


def browser():
    svg = (HERE / 'world_map.svg').read_text()
    payload = json.dumps(LAYOUT).replace('<', '\\u003c')
    document = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>MM5 surface world layout</title>
<style>body{margin:24px;background:#111820;color:#eee5cd;font:15px system-ui}a{color:#a8d7ec}
h1{font-size:25px}p{line-height:1.6;max-width:1100px}.controls{display:flex;gap:18px;flex-wrap:wrap;margin:18px 0}
button,select{font:inherit;color:inherit;background:#283741;border:1px solid #899995;padding:8px;cursor:pointer}
#terrain svg{width:100%;height:auto}#travel img,#palette img{width:100%;height:auto;max-width:1320px}
#detail{padding:20px;background:#223039;margin:15px 0;line-height:1.6}#detail h2{margin-top:0}
.links{display:flex;gap:15px;flex-wrap:wrap}.hidden{display:none}label{cursor:pointer}
</style><h1>MM5 surface world — first layout</h1>
<p>Six adjoining travel areas derived from the original Darkside wilderness. The terrain view is a minimap-style
planning study with illustrative relief, not a screenshot of generated game maps. Each region uses the same proposed
native terrain dimensions; towns will get separately authored footprints.</p>
<div class="links"><a href="README.md">Design decisions</a><a href="world_map.png">World map PNG</a>
<a href="foot_travel.png">Foot-travel PNG</a><a href="layout.json">Editable layout</a>
<a href="../atlas.html">Original-map atlas</a><a href="other_outdoors.html">All 16 outdoor maps: surface, sky and planes</a></div>
<div class="controls"><button data-view="terrain">Terrain overview</button><button data-view="travel">Foot travel</button>
<button data-view="palette">Material palette</button><select id="region" aria-label="Region details"><option value="sw">SW — Castleview / Kalindra</option></select></div>
<div class="controls" id="layers"><label><input type="checkbox" data-layer="regions" checked> Region boundaries</label>
<label><input type="checkbox" data-layer="source-grid" checked> Original squares</label>
<label><input type="checkbox" data-layer="labels" checked> Landmarks</label>
<label><input type="checkbox" data-layer="crossings" checked> Foot crossings</label></div>
<section id="terrain">SVG</section><section id="travel" class="hidden"><img src="foot_travel.png" alt="Foot travel diagram"></section>
<section id="palette" class="hidden"><img src="tileset_palette.png" alt="Native texture palette"></section><aside id="detail"></aside>
<script>const layout=DATA;
const select=document.querySelector('#region'),detail=document.querySelector('#detail');select.replaceChildren();
for(const r of layout.regions){const o=document.createElement('option');o.value=r.id;o.textContent=r.id.toUpperCase()+' — '+r.title;select.append(o)}
select.value='sw';
function showRegion(){const r=layout.regions.find(r=>r.id===select.value);detail.replaceChildren();
const h=document.createElement('h2');h.textContent=r.id.toUpperCase()+' — '+r.title;detail.append(h);
for(const text of [r.squares.join(', '),r.intent,'Material families: '+r.palette.join(', '),
 r.id==='sw'?layout.firstRegion.firstBuildScope:'Equal native terrain footprint; actual playable land and occupied area vary.']){
 const p=document.createElement('p');p.textContent=text;detail.append(p)}
const a=document.createElement('a');a.href='regions/'+r.id+'.png';a.textContent='Open equal-size region crop';detail.append(a)}
select.addEventListener('change',showRegion);showRegion();
for(const button of document.querySelectorAll('[data-view]'))button.addEventListener('click',()=>{
 for(const name of ['terrain','travel','palette'])document.getElementById(name).classList.toggle('hidden',name!==button.dataset.view);
 document.getElementById('layers').classList.toggle('hidden',button.dataset.view!=='terrain')});
for(const input of document.querySelectorAll('[data-layer]'))input.addEventListener('change',()=>{
 document.getElementById(input.dataset.layer).style.display=input.checked?'':'none'});
</script></html>'''
    (HERE / 'index.html').write_text(document.replace('SVG', svg).replace('DATA;', payload+';'))


def main():
    ground, wall, scenery, blocks = loadSource()
    renderTerrain(ground, scenery)
    crossings = verifyTravel(ground, wall, blocks)
    worldMap()
    travelMap()
    palettePlate()
    browser()
    # Exact crop reconstruction demonstrates geographic continuity across all six region edges.
    joined = Image.new('RGB', (WIDTH, HEIGHT))
    metrics = []
    for region in LAYOUT['regions']:
        x, y = region['column']*512, region['row']*512
        crop = Image.open(HERE / 'regions' / f'{region["id"]}.png')
        assert crop.size == (512, 512)
        joined.paste(crop, (x, y))
        raw = ground[y//16:y//16+32, x//16:x//16+32]
        metrics.append(dict(region=region['id'], sourceSurfaceCells=dict(Counter(SURFACES[v] for v in raw.flat))))
    assert np.array_equal(np.array(joined), np.array(Image.open(HERE / 'world_terrain.png')))
    report = dict(passed=True, sourceCells=int(ground.size), regions=6, regionCropSize=[512, 512],
                  exactCropReconstruction=True, waterCellCentersAndComponentCountPreserved=True,
                  roadConnections=4, offRoadConnections=3,
                  crossings=crossings, regionSourceMetrics=metrics,
                  limitations=['Terrain connectivity only; event restrictions and monsters are not simulated.',
                               'Relief and Necropolis ground treatment are proposed visualization, not extracted elevation.',
                               'No native game maps, material bank assignments or runtime travel registrations generated.'],
                  sources=[dict(path=str(p.relative_to(ROOT)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                           for p in sorted(INPUTS)])
    (HERE / 'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ['passed', 'sourceCells', 'regions', 'roadConnections', 'offRoadConnections']}))


if __name__ == '__main__':
    main()
