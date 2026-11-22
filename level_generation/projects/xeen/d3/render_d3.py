#!/usr/bin/env python3
"""D3's MU-3 drawing, MU-4 blockouts and measured figures, from the L1 brief (A5, 2026-11-20).

    render_d3.py        reads devdocs/xeen/briefs/d3/L1/{plan,sketch,project}.yml

Writes into output/studio_cal/d3/mockups/:
  height.npy, colour.png     the land the sketch implies (for the drawings only; the studio builds its own)
  plan_d3.svg, plan_d3.png   the to-scale plan (PNG through headless Chrome), plan_d3_2x.png for the board's crops
  blockout_<view>.png        a crude perspective of each sketch view (Codex's composition reference)
  figures.json               the measured figures for the board and the NOTES

Nothing here is read by the game or the studio. Adapted from level_generation/projects/xeen/x4/render_x4.py; the POI count
is the D-20 census (chained within 400, service doors in, residences, NPCs, exits and landmarks out).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import base64
import io
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[4]
BRIEF = ROOT / 'devdocs/xeen/briefs/d3/L1'
OUT = pathlib.Path(_REPO_ROOT, 'output/studio_cal/d3') / 'mockups'
RES = 6
N = 128
PLAY = (19, 19, 104, 104)     # the playable square cut by the east and south rims
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)

BAND_BASE = {'band:rim_sea': 0, 'band:fen': 960, 'band:low': 1120, 'band:plain': 1270, 'band:mid': 1500,
             'band:high': 1850, 'band:peaks': 2600, 'band:ridge': 1700}
GROUND = {  # sRGB per space, painted in this order over the default dry ground
    'zone:caravan_valley': (182, 160, 110),
    'zone:desert_edge': (208, 180, 122),
    'zone:crossroads_plain': (168, 156, 104),
    'zone:wrath_hills': (138, 124, 100),
    'zone:river_meadows': (124, 132, 82),
    'zone:howling_woods': (78, 84, 60),
    'zone:aging_forest': (150, 104, 56),
    'zone:venom_fen': (92, 104, 66),
    'zone:gemstone_crags': (104, 104, 116),
    'town:sandcaster': (200, 170, 116),
    'zone:wizard_quarter': (198, 152, 140),
    'zone:caravan_yard': (190, 166, 118),
    'town:crossroads': (186, 164, 122),
    'zone:tower_knoll': (120, 112, 100),
}
TREES = {  # space: (trees per cell, [colours])
    'zone:howling_woods': (0.55, [(40, 58, 42), (52, 66, 46)]),
    'zone:aging_forest': (0.6, [(196, 100, 36), (214, 152, 52), (170, 70, 40)]),
    'zone:venom_fen': (0.12, [(76, 96, 50)]),
    'zone:river_meadows': (0.09, [(84, 104, 56)]),
    'zone:crossroads_plain': (0.03, [(96, 104, 60)]),
    'zone:caravan_valley': (0.03, [(110, 112, 66)]),
    'zone:desert_edge': (0.015, [(96, 120, 70)]),
    'zone:wrath_hills': (0.06, [(70, 82, 52)]),
}
TOWN_LEVEL = {'town:sandcaster': 1500, 'zone:wizard_quarter': 1700, 'zone:caravan_yard': 1300,
              'town:crossroads': 1250, 'zone:celia_yard': 1220, 'zone:thaddeus_yard': 960,
              'zone:cornelius_glade': 1120, 'zone:tower_knoll': 1950}


def load():
    read = lambda name: yaml.safe_load((BRIEF / name).read_text())
    return read('plan.yml'), read('sketch.yml'), read('project.yml')


def poly_mask(points, scale=RES, size=N):
    img = Image.new('L', (size * scale, size * scale), 0)
    ImageDraw.Draw(img).polygon([(x * scale, y * scale) for x, y in points], fill=255)
    return np.asarray(img) > 127


def line_mask(points, width_cells, scale=RES, size=N):
    img = Image.new('L', (size * scale, size * scale), 0)
    d = ImageDraw.Draw(img)
    pts = [(x * scale, y * scale) for x, y in points]
    w = max(1, int(width_cells * scale))
    d.line(pts, fill=255, width=w, joint='curve')
    for p in pts:
        d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=255)
    return np.asarray(img) > 127


def districts(sketch):
    out = {}
    for d in sketch.get('districts', []):
        out.setdefault(d['space'], np.zeros((N * RES, N * RES), bool))
        out[d['space']] |= poly_mask(d['polygon'])
    return out


def rim_poly(sketch):
    return next(d['polygon'] for d in sketch['districts'] if d['space'] == 'zone:rim')


def build_land(sketch):
    size = N * RES
    height = np.full((size, size), 1250.0)
    for band in sketch['heights']['bands']:
        if band['band'] != 'band:rim_sea':
            height[poly_mask(band['polygon'])] = BAND_BASE[band['band']]
    height = ndimage.gaussian_filter(height, 4 * RES)
    yy, xx = np.mgrid[0:size, 0:size] / RES
    for point in sketch['heights'].get('points', []):
        px, py = point['at']
        r = 7.0 if point['h'] > 2500 else 4.0
        d = np.hypot(xx - px - 0.5, yy - py - 0.5)
        t = np.clip(1 - d / r, 0, 1)
        w = t * t * (3 - 2 * t)
        height = height * (1 - w) + point['h'] * w
    for ridge in sketch['heights'].get('ridges', []):
        m = line_mask(ridge['line'], ridge.get('width', 2))
        dist = ndimage.distance_transform_edt(~m) / RES
        w = np.clip(1 - dist / (ridge.get('slope', 3) + 2.5), 0, 1)
        height = np.maximum(height, height * (1 - w) + ridge['height'] * w)
    rng = np.random.default_rng(4)
    noise = ndimage.gaussian_filter(rng.normal(size=(size, size)), 3 * RES)
    noise /= np.abs(noise).max() + 1e-6
    rough = ndimage.gaussian_filter(rng.normal(size=(size, size)), 0.7 * RES)
    rough /= np.abs(rough).max() + 1e-6
    masks = districts(sketch)
    calm = np.zeros((size, size), bool)
    for space in TOWN_LEVEL:
        if space in masks:
            calm |= masks[space]
    calm = ndimage.binary_dilation(calm, iterations=2 * RES)
    steep = np.clip((height - 1600) / 1200, 0, 1)
    height += np.where(calm, 0, noise * 160 + rough * (30 + 280 * steep))
    for space, level in TOWN_LEVEL.items():
        if space in masks:
            soft = ndimage.gaussian_filter(masks[space].astype(float), RES * 0.6)
            height = height * (1 - soft) + level * soft
    water = np.zeros((size, size), bool)
    for river in sketch.get('water', {}).get('rivers', []):
        m = line_mask(river['line'], river.get('width_cells', 3))
        dist = ndimage.distance_transform_edt(~m) / RES
        level = river.get('level', 1000)
        valley = level + 60 + dist * 130
        height = np.minimum(height, np.where(dist < 9, valley, height))
        height[m] = level
        water |= m
    for body in sketch.get('water', {}).get('bodies', []):
        if body['id'] == 'water:rim_sea':
            continue
        m = poly_mask(body['polygon'])
        dist = ndimage.distance_transform_edt(~m) / RES
        height = np.minimum(height, np.where(dist < 4, body['level'] + 30 + dist * 40, height))
        height[m] = body['level']
        water |= m
    rim = poly_mask(rim_poly(sketch))
    height[rim] = 0
    water &= ~rim
    return height, water, rim


def colour_land(sketch, height, water, rim):
    size = N * RES
    rgb = np.zeros((size, size, 3))
    rgb[:] = (180, 160, 108)
    masks = districts(sketch)
    jitter = ndimage.gaussian_filter(np.random.default_rng(8).normal(size=(size, size)), 1.5 * RES)
    jitter /= np.abs(jitter).max() + 1e-6
    for space, colour in GROUND.items():
        if space in masks:
            soft = ndimage.gaussian_filter(masks[space].astype(float), 2.0 * RES)
            soft = np.clip(soft + jitter * 0.35 * soft * (1 - soft) * 4, 0, 1)[..., None]
            rgb = rgb * (1 - soft) + np.array(colour) * soft
    gy, gx = np.gradient(height, 512 / RES)
    slope = np.hypot(gx, gy)
    rock = np.clip((slope - 0.5) * 2.2, 0, 1)
    rock = np.maximum(rock, np.clip((height - 2500) / 600, 0, 0.7))
    rgb = rgb * (1 - rock[..., None]) + np.array((118, 108, 104)) * rock[..., None]
    dist = ndimage.distance_transform_edt(~water) / RES
    bank = np.clip(1 - dist / 2.0, 0, 1)[..., None] * (~water)[..., None] * 0.5
    rgb = rgb * (1 - bank) + np.array((90, 116, 60)) * bank
    pond = poly_mask(next(b['polygon'] for b in sketch['water']['bodies'] if b['id'] == 'water:venom_pond'))
    rgb[water] = (52, 96, 120)
    rgb[pond] = (66, 104, 58)
    light = np.array([-0.55, -0.65, 0.52])
    nx, ny = -gx * 2.2, -gy * 2.2
    nz = np.ones_like(nx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    shade = (nx * light[0] + ny * light[1] + nz * light[2]) / norm
    shade = np.clip(0.55 + 0.6 * shade, 0.35, 1.15)
    rgb = rgb * shade[..., None]
    rgb[water & ~pond] = rgb[water & ~pond] * 0.5 + np.array((52, 96, 120)) * 0.5
    rgb[pond] = rgb[pond] * 0.5 + np.array((66, 104, 58)) * 0.5
    stars = np.zeros((size, size, 3))
    stars[:] = (10, 12, 26)
    rng = np.random.default_rng(3)
    for y, x in rng.integers(0, size, size=(2400, 2)):
        stars[y, x] = rng.integers(140, 255)
    rgb[rim] = stars[rim]
    cliff = ndimage.binary_dilation(~rim, iterations=int(1.0 * RES)) & rim
    rgb[cliff] = (110, 92, 82)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    bare = img.copy()
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    trees = []
    town = np.zeros((size, size), bool)
    for space in TOWN_LEVEL:
        if space in masks:
            town |= masks[space]
    for space, (density, colours) in TREES.items():
        if space not in masks:
            continue
        ys, xs = np.nonzero(masks[space][::RES, ::RES])
        for cy, cx in zip(ys, xs):
            for _ in range(rng.poisson(density * 2)):
                x = (cx + rng.random()) * RES
                y = (cy + rng.random()) * RES
                hy, hx = int(min(y, size - 1)), int(min(x, size - 1))
                if water[hy, hx] or rim[hy, hx] or town[hy, hx] or height[hy, hx] > 2400 or slope[hy, hx] > 0.6:
                    continue
                colour = colours[rng.integers(len(colours))]
                s = RES * (0.35 + 0.2 * rng.random())
                draw.ellipse((x - s, y - s * 0.8, x + s, y + s * 0.8), fill=colour)
                trees.append((x / RES, y / RES, colour))
    return img, trees, bare


# ---------------------------------------------------------------- labels

KINDS = {
    'entrance:west_road': 'arrival', 'entrance:north_road': 'arrival',
    'entrance:sandcaster_square': 'town_arrival', 'entrance:sandcaster_stables': 'town_arrival',
    'entrance:lucio_jetty': 'special', 'entrance:south_gate': 'gate', 'entrance:east_gate': 'gate',
    'entrance:dd18_shaft': 'dungeon', 'entrance:dd19_gate': 'dungeon', 'entrance:dd07_door': 'dungeon',
    'poi:caravan_wreck': 'chest', 'poi:mantis_mound': 'chest', 'poi:aged_skeleton': 'chest',
    'poi:drowned_skiff': 'chest', 'poi:tower_cart': 'chest', 'poi:smugglers_rope': 'chest',
    'poi:fallen_courier': 'chest', 'poi:rim_watch': 'chest',
    'poi:cornelius': 'npc', 'poi:signposts': 'sign',
    'landmark:sandcaster': 'landmark', 'landmark:sky_stair': 'landmark', 'landmark:eastern_tower': 'landmark',
    'landmark:wrath_falls': 'landmark', 'landmark:rim_glow': 'landmark', 'landmark:gemstone_crags': 'landmark',
}
for j in ['junction:gate_fork', 'junction:crossroads', 'junction:east_fork', 'junction:venom_fork',
          'junction:forest_fork']:
    KINDS[j] = 'junction'

# id: (text, dx px, dy px, anchor); None hides the label
NAMES = {
    'entrance:west_road': ('from D2 Sprite Forest (y 44)', 4, -16, 'start'),
    'entrance:north_road': ('from D4 Lakeside (x 88)', 14, 4, 'start'),
    'entrance:sandcaster_square': None, 'entrance:sandcaster_stables': None, 'entrance:lucio_jetty': None,
    'entrance:south_gate': None, 'entrance:east_gate': None, 'entrance:dd18_shaft': None,
    'entrance:dd19_gate': None,
    'entrance:dd07_door': ('DD-07 Eastern Tower', 10, 26, 'start'),
    'junction:gate_fork': None,
    'junction:crossroads': None,
    'junction:east_fork': ('East fork', 12, -8, 'start'),
    'junction:venom_fork': ('Venom fork', 12, 4, 'start'),
    'junction:forest_fork': ('Forest fork', 12, 4, 'start'),
    'poi:obelisk': ('Obelisk', 12, 4, 'start'),
    'poi:sc_mirror': None, 'poi:sc_well': None, 'poi:market_well': None,
    'poi:cornelius': ('Cornelius (Perception teacher)', 12, 4, 'start'),
    'poi:vespar_ruin': ("Vespar's ruin (emerald handle)", 12, 18, 'start'),
    'poi:fountain_youth': ('Fountain of Youth', -12, 18, 'end'),
    'poi:fountain_protection': ('Fountain of Great Protection', -12, -10, 'end'),
    'poi:fruit_hut_river': ('fruit hut', 12, 4, 'start'),
    'poi:fruit_hut_forest': ('fruit hut', 12, 4, 'start'),
    'poi:wrath_spring': ('Wrath Spring', -12, 4, 'end'),
    'poi:rim_watch': ('Rim Watch', -12, -8, 'end'),
    'poi:howling_stone': ('howling stone', 12, 4, 'start'),
    'poi:edge_cairn': ('edge cairn', 12, -6, 'start'),
    'poi:caravan_well': ('caravan well', 12, 4, 'start'),
    'poi:great_oak': ('great oak', -12, -6, 'end'),
    'poi:wayside_shrine': ('wayside shrine', -12, 4, 'end'),
    'poi:caravan_wreck': ('swallowed caravan', -12, -6, 'end'),
    'poi:mantis_mound': ('mantis mound', 12, 4, 'start'),
    'poi:aged_skeleton': ('aged skeleton', 12, 4, 'start'),
    'poi:drowned_skiff': ('drowned skiff', -12, 14, 'end'),
    'poi:tower_cart': ("mages' cart", -12, -6, 'end'),
    'poi:smugglers_rope': ("smugglers' rope", 12, -6, 'start'),
    'poi:fallen_courier': ('fallen courier', 12, 4, 'start'),
    'landmark:sandcaster': None,
    'landmark:sky_stair': None,
    'landmark:eastern_tower': None,
    'landmark:wrath_falls': ('Wrath Falls', -10, 24, 'end'),
    'landmark:rim_glow': None,
    'landmark:gemstone_crags': None,
    'poi:signposts': None,
}
AREA_CAPTION = {'pop:dune_scrub': (66, 22.5), 'pop:wrath_hills': (95, 33), 'pop:howling_woods': (26, 58),
                'pop:venom_fen': (82, 98)}
ENC_COLOURS = {1: '#c0282d', 2: '#d06a12', 3: '#7b3fa0'}
FAMILY = {1: 'Mantis ants', 2: 'Cobras', 3: 'Sand burrowers'}
CAPTIONS = [
    ('SANDCASTER', (37, 18.6), 17, '#3a2208'),
    ('the desert edge', (64, 16.5), 15, '#5a3a08'),
    ('THE WRATH HILLS', (92, 14), 15, '#2a2010'),
    ('THE CROSSROADS', (60, 52.5), 14, '#222'),
    ('the caravan valley', (12, 41), 13, '#3a2a10'),
    ('THE HOWLING WOODS', (19, 72), 15, '#e8e8e8'),
    ('THE AGING FOREST', (50, 75), 16, '#3a1a04'),
    ('Venom Pond', (72, 81.5), 13, '#e8f0d0'),
    ('the fen', (94, 87), 13, '#1a2a0a'),
    ('River of Wrath', (82, 31), 13, '#123a5a'),
    ('river meadows', (93, 70), 13, '#2a3a10'),
    ('last Gemstone crags 3,400', (9, 1.8), 13, '#e8e8e8'),
    ('the world rim: a cliff above the stars, the bright face\'s glow beyond', (64, 108), 14, '#ccd'),
    ('the east rim', (110, 80), 14, '#ccd'),
]


def esc(text):
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def pts(points, s, off=(0, 0)):
    return ' '.join(f'{(x + off[0]) * s:.1f},{(y + off[1]) * s:.1f}' for x, y in points)


def rect_of(at, fp, facing):
    front, depth = fp
    wx, wy = (front, depth) if facing in 'ns' else (depth, front)
    return at[0], at[1], wx, wy


def door_of(at, fp, facing):
    x, y, wx, wy = rect_of(at, fp, facing)
    return {'n': (x + wx / 2, y), 's': (x + wx / 2, y + wy), 'e': (x + wx, y + wy / 2), 'w': (x, y + wy / 2)}[facing]


RESIDENCES = ('building:celia_derek_cottage', 'building:thaddeus_hut')   # A4: kind residence


def plot_list(plan, sketch):
    """Every plot: (building id, index, door [x, y] in cells, service?, rect)."""
    buildings = {}
    for space in plan['spaces']:
        for b in space.get('buildings', []) or []:
            buildings[b['id']] = b
    out = []
    for d in sketch.get('districts', []):
        for plot in d.get('plots', []) or []:
            b = buildings[plot['building']]
            fp = b['footprint_cells'][(plot.get('index') or 1) - 1]
            service = b['service'] not in ('residence',) and plot['building'] not in RESIDENCES and not (
                plot['building'] == 'building:xr_stall' and plot.get('index') == 6)
            out.append((plot['building'], plot.get('index'), door_of(plot['at'], fp, plot['facing']), service,
                        rect_of(plot['at'], fp, plot['facing']), plot['facing']))
    return out


def svg_plan(plan, sketch, colour, figures, scale=12):
    size = N * scale
    mx, my = 32, 32
    W, H = size + 2 * mx, size + 2 * my + 150
    buf = io.BytesIO()
    colour.resize((size, size), Image.LANCZOS).save(buf, 'JPEG', quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode()
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-mx} {-my} {W} {H}" width="{W}" height="{H}" '
         'font-family="DejaVu Sans, sans-serif">',
         f'<rect x="{-mx}" y="{-my}" width="{W}" height="{H}" fill="#1b1d22"/>',
         f'<image href="data:image/jpeg;base64,{b64}" x="0" y="0" width="{size}" height="{size}"/>',
         '<defs><pattern id="quiet" width="12" height="12" patternUnits="userSpaceOnUse" '
         'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="12" stroke="#2e8b57" '
         'stroke-width="2.5" stroke-opacity="0.6"/></pattern>'
         '<marker id="arr" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" '
         'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#0b6b3a"/></marker>'
         '<linearGradient id="glow" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffe9a8" '
         'stop-opacity="0"/><stop offset="1" stop-color="#ffe9a8" stop-opacity="0.55"/></linearGradient></defs>']
    # the bright face's glow beyond the east rim
    o.append(f'<rect x="{106 * scale}" y="0" width="{22 * scale}" height="{104 * scale}" fill="url(#glow)"/>')
    for i in range(0, N + 1):
        strong = i % 8 == 0
        op = 0.22 if strong else 0.07
        o.append(f'<line x1="{i * scale}" y1="0" x2="{i * scale}" y2="{size}" stroke="#000" stroke-opacity="{op}" '
                 f'stroke-width="{1.2 if strong else 0.6}"/>')
        o.append(f'<line x1="0" y1="{i * scale}" x2="{size}" y2="{i * scale}" stroke="#000" stroke-opacity="{op}" '
                 f'stroke-width="{1.2 if strong else 0.6}"/>')
        if i % 16 == 0:
            o.append(f'<text x="{i * scale}" y="-10" font-size="13" text-anchor="middle" fill="#bbb">{i}</text>')
            o.append(f'<text x="-8" y="{i * scale + 4}" font-size="13" text-anchor="end" fill="#bbb">{i}</text>')
    px, py, pw, ph = sketch['frame']['playable']
    o.append(f'<rect x="{px * scale}" y="{py * scale}" width="{pw * scale}" height="{ph * scale}" fill="none" '
             'stroke="#fff" stroke-opacity="0.8" stroke-dasharray="10 6" stroke-width="1.8"/>')
    for area in sketch.get('areas', []):
        kind = area.get('kind', 'encounter')
        poly = area['polygon']
        if kind in ('keep_clear', 'open'):
            o.append(f'<polygon points="{pts(poly, scale)}" fill="url(#quiet)" stroke="#2e8b57" stroke-opacity="0.9" '
                     'stroke-width="1.6" stroke-dasharray="5 3"/>')
        else:
            c = ENC_COLOURS[area['slot']]
            o.append(f'<polygon points="{pts(poly, scale)}" fill="{c}" fill-opacity="0.16" stroke="{c}" '
                     'stroke-width="2.6" stroke-opacity="0.95"/>')
    # hornet nests: a dashed disc of radius 3 (counted as fight land)
    for actor in sketch.get('actors', []):
        if actor['count'] >= 3:
            x, y = actor['at']
            o.append(f'<circle cx="{(x + .5) * scale}" cy="{(y + .5) * scale}" r="{3 * scale}" fill="#c08000" '
                     'fill-opacity="0.15" stroke="#c08000" stroke-width="2" stroke-dasharray="6 3"/>')
    for road in sketch.get('roads', []):
        lane = road.get('width') == 'lane'
        w = 3 if lane else 6
        o.append(f'<polyline points="{pts(road["line"], scale)}" fill="none" stroke="#3b2a1a" stroke-width="{w + 2}" '
                 'stroke-opacity="0.6" stroke-linecap="round" stroke-linejoin="round"/>')
        dash = ' stroke-dasharray="7 4"' if lane else ''
        o.append(f'<polyline points="{pts(road["line"], scale)}" fill="none" '
                 f'stroke="{"#e6d6a8" if lane else "#d2a868"}" stroke-width="{w}" stroke-linecap="round" '
                 f'stroke-linejoin="round"{dash}/>')
    # Wrath Bridge
    o.append(f'<rect x="{73.6 * scale}" y="{45.5 * scale}" width="{4 * scale}" height="{0.9 * scale}" fill="#d8c49a" '
             'stroke="#2a1a10" stroke-width="1.2"/>')
    # Sandcaster's wall, the quarter's inner wall, the Sky Stair
    o.append(f'<polygon points="{pts([[27, 20], [47, 20], [47, 39], [27, 39]], scale)}" fill="none" '
             'stroke="#7a5a30" stroke-width="4"/>')
    o.append(f'<polygon points="{pts([[40, 20], [47, 20], [47, 27], [40, 27]], scale)}" fill="#c89a8c" '
             'fill-opacity="0.35" stroke="#a06a60" stroke-width="2.5"/>')
    for tx, ty in [(27, 20), (47, 20), (27, 39), (47, 39), (37, 20), (27, 30)]:
        o.append(f'<rect x="{(tx - 0.6) * scale}" y="{(ty - 0.6) * scale}" width="{1.2 * scale}" '
                 f'height="{1.2 * scale}" fill="#c8a066" stroke="#3a2a10" stroke-width="1.2"/>')
    # plots
    for bid, idx, door, service, (x, y, wx, wy), facing in plot_list(plan, sketch):
        fill = '#7a3a26' if service else '#9a7a5a'
        if bid.startswith('building:wq_'):
            fill = '#9a4a6a' if service else '#b07a8a'
        o.append(f'<rect x="{x * scale:.1f}" y="{y * scale:.1f}" width="{wx * scale:.1f}" height="{wy * scale:.1f}" '
                 f'fill="{fill}" stroke="#2a1a10" stroke-width="1.2"/>')
        o.append(f'<circle cx="{door[0] * scale:.1f}" cy="{door[1] * scale:.1f}" r="2.8" fill="#ffd34d" '
                 'stroke="#2a1a10" stroke-width="0.8"/>')
    for view in sketch.get('views', []):
        x, y = view['at']
        lx, ly = view['look']
        ang = math.atan2(ly - y, lx - x)
        dist = math.hypot(lx - x, ly - y)
        half = math.radians(37)
        p1 = (x + math.cos(ang - half) * dist, y + math.sin(ang - half) * dist)
        p2 = (x + math.cos(ang + half) * dist, y + math.sin(ang + half) * dist)
        col = '#1f6fd1'
        o.append(f'<polygon points="{pts([(x, y), p1, p2], scale, (0.5, 0.5))}" fill="{col}" fill-opacity="0.10" '
                 f'stroke="{col}" stroke-width="1.6" stroke-dasharray="7 4"/>')
        o.append(f'<line x1="{(x + .5) * scale}" y1="{(y + .5) * scale}" x2="{(lx + .5) * scale}" '
                 f'y2="{(ly + .5) * scale}" stroke="{col}" stroke-width="2.4"/>')
        o.append(f'<circle cx="{(x + .5) * scale}" cy="{(y + .5) * scale}" r="8" fill="{col}" stroke="#fff" '
                 'stroke-width="2"/>')
        name = 'camera: arrival' if 'arrival' in view['id'] else 'camera: signature'
        dx, dy = (6, 30) if 'arrival' in view['id'] else (-14, -14)
        o.append(f'<text x="{(x + .5) * scale + dx}" y="{(y + .5) * scale + dy}" font-size="13" font-weight="bold" '
                 f'text-anchor="{"end" if dx < 0 else "start"}" fill="#0d3f80" stroke="#fff" stroke-width="3.2" '
                 f'paint-order="stroke">{name}</text>')
    for actor in sketch.get('actors', []):
        x, y = actor['at']
        o.append(f'<circle cx="{(x + .5) * scale}" cy="{(y + .5) * scale}" r="{3 + actor["count"]}" fill="#b00" '
                 'fill-opacity="0.75" stroke="#fff" stroke-width="1"/>')
    seen = set()
    for point in sketch.get('points', []):
        pid = point['id']
        x, y = point['at']
        if x > 106:
            continue
        cx, cy = (x + 0.5) * scale, (y + 0.5) * scale
        kind = KINDS.get(pid, 'poi')
        if kind == 'arrival':
            o.append(f'<rect x="{cx - 8}" y="{cy - 8}" width="16" height="16" fill="#0b6b3a" stroke="#fff" '
                     'stroke-width="2"/>')
            dx, dy = {'n': (0, -1), 's': (0, 1), 'e': (1, 0), 'w': (-1, 0)}[point.get('facing', 'n')]
            o.append(f'<line x1="{cx - dx * 34}" y1="{cy - dy * 34}" x2="{cx - dx * 11}" y2="{cy - dy * 11}" '
                     'stroke="#0b6b3a" stroke-width="5" marker-end="url(#arr)"/>')
        elif kind == 'town_arrival':
            o.append(f'<rect x="{cx - 5}" y="{cy - 5}" width="10" height="10" fill="#2fa860" stroke="#fff" '
                     'stroke-width="1.5"/>')
        elif kind == 'gate':
            o.append(f'<rect x="{cx - 6}" y="{cy - 6}" width="12" height="12" fill="#e0b040" stroke="#222" '
                     'stroke-width="2"/>')
        elif kind == 'dungeon':
            o.append(f'<rect x="{cx - 7}" y="{cy - 7}" width="14" height="14" fill="#111" stroke="#fff" '
                     'stroke-width="2"/>')
        elif kind == 'special':
            o.append(f'<polygon points="{cx},{cy - 9} {cx + 9},{cy} {cx},{cy + 9} {cx - 9},{cy}" fill="#1f6fd1" '
                     'stroke="#fff" stroke-width="2"/>')
        elif kind == 'chest':
            o.append(f'<polygon points="{cx},{cy - 8} {cx + 8},{cy} {cx},{cy + 8} {cx - 8},{cy}" fill="#d8a010" '
                     'stroke="#222" stroke-width="1.5"/>')
        elif kind == 'npc':
            o.append(f'<circle cx="{cx}" cy="{cy}" r="5.5" fill="#1d5fa8" stroke="#fff" stroke-width="1.5"/>')
        elif kind == 'junction':
            o.append(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="#5a4630" stroke="#fff" stroke-width="1.5"/>')
        elif kind == 'sign':
            o.append(f'<rect x="{cx - 2}" y="{cy - 6}" width="4" height="10" fill="#6b4a20"/>')
        elif kind == 'landmark':
            star = []
            for i in range(10):
                r = 10 if i % 2 == 0 else 4.5
                a = -math.pi / 2 + i * math.pi / 5
                star.append(f'{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}')
            o.append(f'<polygon points="{" ".join(star)}" fill="#e07000" stroke="#fff" stroke-width="1.2"/>')
        else:
            o.append(f'<circle cx="{cx}" cy="{cy}" r="5.5" fill="#8a1f7a" stroke="#fff" stroke-width="1.5"/>')
        label = NAMES.get(pid, (pid.split(':')[1].replace('_', ' '), 10, 4, 'start'))
        if not label or (pid, label[0]) in seen:
            continue
        seen.add((pid, label[0]))
        text, dx, dy, anchor = label
        o.append(f'<text x="{cx + dx}" y="{cy + dy}" font-size="14" text-anchor="{anchor}" fill="#111" '
                 'stroke="#fff" stroke-width="3.4" paint-order="stroke" stroke-linejoin="round">'
                 f'{esc(text)}</text>')
    callouts = [
        ((28.5, 21.5), (1, 5), "Sky Stair: Lucio's Jetty on top (4649, after M30)"),
        ((43.5, 21), (1, 7.8), 'wizard quarter: 5 sealed doors, guild gate = DD-19'),
        ((30.5, 32.5), (1, 10.6), "DD-18 street shaft by Barticus' Gym (D-27)"),
        ((36.5, 39), (1, 13.4), 'gates: south and east, the Sandcaster Pass (Q-D8)'),
        ((37, 41.5), (1, 16.2), 'caravan yard: stables 4611, town arrival'),
        ((60, 44), (66, 40.5), 'the Crossroads: 6 stalls, 6 roads'),
        ((66, 50), (69, 51.5), "Celia and Derek's cottage (4647)"),
        ((81.5, 75), (86, 77.5), "Thaddeus's hut (4648)"),
    ]
    for (ax, ay), (tx, ty), text in callouts:
        o.append(f'<line x1="{ax * scale}" y1="{ay * scale}" x2="{(tx + 0.3) * scale}" y2="{(ty - 0.4) * scale}" '
                 'stroke="#222" stroke-width="1.2"/>')
        o.append(f'<text x="{tx * scale}" y="{ty * scale}" font-size="13" fill="#111" stroke="#fff" '
                 f'stroke-width="3.2" paint-order="stroke">{esc(text)}</text>')
    for text, (x, y), size_t, colour_t in CAPTIONS:
        o.append(f'<text x="{x * scale}" y="{y * scale}" font-size="{size_t}" font-style="italic" font-weight="bold" '
                 f'text-anchor="middle" fill="{colour_t}" stroke="#000" stroke-width="0.6" stroke-opacity="0.35">'
                 f'{esc(text)}</text>')
    for area in sketch.get('areas', []):
        if area.get('kind', 'encounter') != 'encounter':
            continue
        cx, cy = AREA_CAPTION[area['id']]
        fam = FAMILY[area['slot']]
        cells = figures['areas'][area['id']]['cells_4096']
        for k, line in enumerate([f'{fam}', f'{area["count"]} markers, {cells:.1f} of 4,096²']):
            o.append(f'<text x="{cx * scale}" y="{cy * scale + k * 15}" font-size="13" text-anchor="middle" '
                     f'fill="{ENC_COLOURS[area["slot"]]}" font-weight="bold" stroke="#fff" stroke-width="3" '
                     f'paint-order="stroke">{esc(line)}</text>')
    o.append(f'<text x="{47 * scale}" y="{61 * scale}" font-size="13" text-anchor="middle" fill="#8a5a00" '
             'font-weight="bold" stroke="#fff" stroke-width="3" paint-order="stroke">hell hornet nests '
             '(3 x 6 placed)</text>')
    o.append(f'<text x="{116 * scale}" y="{14 * scale}" font-size="15" font-weight="bold" text-anchor="middle" '
             'fill="#fff">D3 Sandcaster and</text>')
    o.append(f'<text x="{116 * scale}" y="{15.5 * scale}" font-size="15" font-weight="bold" text-anchor="middle" '
             'fill="#fff">the Aging Forest</text>')
    o.append(f'<text x="{116 * scale}" y="{17.2 * scale}" font-size="12" text-anchor="middle" fill="#ccc">MU-3 plan, '
             'A5, 2026-11-20</text>')
    bx, by = 106.5 * scale, 112 * scale
    for i in range(10):
        o.append(f'<rect x="{bx + i * scale}" y="{by - 6}" width="{scale}" height="8" '
                 f'fill="{"#fff" if i % 2 == 0 else "#333"}" stroke="#fff" stroke-width="0.6"/>')
    o.append(f'<text x="{bx}" y="{by + 20}" font-size="13" fill="#fff">5,120 units (10 cells of 512)</text>')
    ly = size + 26
    items = [
        ('sq', '#0b6b3a', 'edge arrival (arrow: facing)'), ('sqs', '#2fa860', 'town arrival'),
        ('gate', '#e0b040', 'city gate (the pass)'), ('sq', '#111', 'dungeon entrance'),
        ('dia', '#1f6fd1', "Lucio's Jetty (boat)"), ('dia', '#d8a010', 'chest with a reason'),
        ('dot', '#1d5fa8', 'NPC outdoors'), ('dot', '#8a1f7a', 'device / place'),
        ('star', '#e07000', 'landmark'), ('dot', '#b00', 'placed hostiles (size: count)'),
        ('enc', '#c0282d', 'encounter: mantis ants'), ('enc', '#d06a12', 'encounter: cobras'),
        ('enc', '#7b3fa0', 'encounter: sand burrowers'), ('enc', '#c08000', 'hornet nest (radius 3 cells)'),
        ('quiet', '#2e8b57', 'keep clear / quiet by design'),
        ('road', '#d2a868', 'road'), ('lane', '#e6d6a8', 'lane / path'),
        ('cam', '#1f6fd1', 'MU-4 camera and sight line'), ('plot', '#7a3a26', 'service (door dot)'),
        ('plot', '#9a7a5a', 'residence'),
    ]
    cols = 5
    for i, (shape, col, text) in enumerate(items):
        x = 10 + (i % cols) * 306
        y = ly + (i // cols) * 28
        if shape in ('sq', 'sqs', 'plot', 'gate'):
            s = 14 if shape == 'sq' else (12 if shape == 'gate' else 10)
            o.append(f'<rect x="{x}" y="{y - s / 2}" width="{s}" height="{s}" fill="{col}" stroke="#fff"/>')
        elif shape == 'dia':
            o.append(f'<polygon points="{x + 7},{y - 8} {x + 15},{y} {x + 7},{y + 8} {x - 1},{y}" fill="{col}" '
                     'stroke="#fff"/>')
        elif shape in ('dot', 'star'):
            o.append(f'<circle cx="{x + 7}" cy="{y}" r="6" fill="{col}" stroke="#fff"/>')
        elif shape == 'enc':
            o.append(f'<rect x="{x}" y="{y - 7}" width="18" height="14" fill="{col}" fill-opacity="0.3" '
                     f'stroke="{col}" stroke-width="2.5"/>')
        elif shape == 'quiet':
            o.append(f'<rect x="{x}" y="{y - 7}" width="18" height="14" fill="url(#quiet)" stroke="{col}" '
                     'stroke-dasharray="4 2"/>')
        elif shape in ('road', 'lane'):
            o.append(f'<line x1="{x}" y1="{y}" x2="{x + 20}" y2="{y}" stroke="{col}" '
                     f'stroke-width="{6 if shape == "road" else 3}"{" stroke-dasharray=\"6 3\"" if shape == "lane" else ""}/>')
        elif shape == 'cam':
            o.append(f'<circle cx="{x + 7}" cy="{y}" r="6" fill="{col}" stroke="#fff"/>'
                     f'<line x1="{x + 7}" y1="{y}" x2="{x + 24}" y2="{y - 6}" stroke="{col}" stroke-width="2"/>')
        o.append(f'<text x="{x + 28}" y="{y + 5}" font-size="14" fill="#e8e8e8">{esc(text)}</text>')
    q = figures['quiet_share']
    o.append(f'<text x="10" y="{ly + 4 * 28 + 4}" font-size="14" fill="#bbb">Land outside the coloured '
             f'areas and the nests is quiet: {q * 100:.0f} % of the playable land. Dashed white: the '
             'playable bounds; the land and the trees run on to the map edge; past x 104 and y 104, the stars.'
             '</text>')
    o.append('</svg>')
    return '\n'.join(o)


# ---------------------------------------------------------------- perspective blockout

def blockout(height, colour_img, view, models, out_path, w=1536, h=1024, fov=80.0, annotations=None,
             max_d=52000.0):
    size = height.shape[0]
    col = np.asarray(colour_img.convert('RGB')).astype(float)
    cx, cy = (view['at'][0] + 0.5) * RES, (view['at'][1] + 0.5) * RES
    eye = height[int(cy), int(cx)] + view.get('height', 180)
    lx, ly = (view['look'][0] + 0.5) * RES, (view['look'][1] + 0.5) * RES
    yaw = math.atan2(ly - cy, lx - cx)
    pitch = math.radians(BLOCKOUT_PITCH.get(view['id'], -3.0))
    unit = RES / 512.0
    img = np.zeros((h, w, 3))
    focal = (w / 2) / math.tan(math.radians(fov / 2))
    horizon = h / 2 + focal * math.tan(pitch)
    # the Darkside sky: a dusky zenith, an amber band at the horizon, the bright face's glow low in the east
    for yy in range(h):
        t = np.clip((yy - (horizon - 520)) / 520, 0, 1)
        img[yy, :] = np.array((86, 72, 92)) * (1 - t) + np.array((214, 164, 96)) * t
    for sx in range(w):
        a = yaw + math.atan2(sx - w / 2, focal)
        east = math.exp(-((math.atan2(math.sin(a), math.cos(a))) / 0.55) ** 2)
        for yy in range(int(max(0, horizon - 260)), int(min(h, horizon + 4))):
            g = east * math.exp(-((horizon - yy) / 120.0) ** 2) * 0.85
            img[yy, sx] = img[yy, sx] * (1 - g) + np.array((255, 238, 190)) * g
    zs = np.concatenate([np.arange(60, 2000, 12.0), np.arange(2000, max_d, 40.0)])
    haze = np.array((206, 176, 132))
    for sx in range(w):
        a = yaw + math.atan2(sx - w / 2, focal)
        dx, dy = math.cos(a), math.sin(a)
        corr = math.cos(a - yaw)
        ybuf = h
        rx = cx + dx * zs * unit
        ry = cy + dy * zs * unit
        inside = (rx >= 0) & (rx < size - 1) & (ry >= 0) & (ry < size - 1)
        for k in np.nonzero(inside)[0]:
            ix, iy = int(rx[k]), int(ry[k])
            fx, fy = rx[k] - ix, ry[k] - iy
            hgt = (height[iy, ix] * (1 - fx) * (1 - fy) + height[iy, ix + 1] * fx * (1 - fy)
                   + height[iy + 1, ix] * (1 - fx) * fy + height[iy + 1, ix + 1] * fx * fy)
            if hgt <= 1:
                continue      # the stars below the rim: the sky shows through
            z = zs[k] * corr
            sy = int(horizon - (hgt - eye) / z * focal)
            if sy < ybuf:
                c = col[iy, ix]
                fog = min(1.0, (zs[k] / 40000.0) ** 1.5) * 0.7
                c = c * (1 - fog) + haze * fog
                img[max(sy, 0):ybuf, sx] = c
                ybuf = max(sy, 0)
                if ybuf == 0:
                    break
        # below the horizon where no land was drawn: the starfield
        if ybuf > horizon:
            top = int(max(horizon, 0))
            img[top:ybuf, sx] = (12, 14, 30)
    rng = np.random.default_rng(5)
    for _ in range(900):
        sx_, sy_ = rng.integers(0, w), rng.integers(int(max(horizon, 0)), h)
        if img[sy_, sx_].sum() < 70:
            img[sy_, sx_] = (220, 220, 240)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(out)
    order = []
    for m in models:
        mx_, my_ = (m[0] + 0.5) * RES, (m[1] + 0.5) * RES
        order.append((math.hypot(mx_ - cx, my_ - cy) / unit, m))
    for d, m in sorted(order, key=lambda t: -t[0]):
        mx_, my_ = (m[0] + 0.5) * RES, (m[1] + 0.5) * RES
        a = math.atan2(my_ - cy, mx_ - cx) - yaw
        a = (a + math.pi) % (2 * math.pi) - math.pi
        if abs(a) > math.radians(fov / 2 + 5) or d < 200 or (len(m) > 6 and m[6] == 'tree' and d < 1800):
            continue
        z = d * math.cos(a)
        sx = w / 2 + math.tan(a) * focal
        base = height[int(min(my_, size - 1)), int(min(mx_, size - 1))] if m[2] is None else m[2]
        top = base + m[3]
        y0 = horizon - (top - eye) / z * focal
        y1 = horizon - (base - eye) / z * focal
        half = m[4] * 512 / z * focal
        fog = min(1.0, (d / 40000.0) ** 1.5) * 0.7
        c = tuple(int(v * (1 - fog) + f * fog) for v, f in zip(m[5], haze))
        shape = m[6] if len(m) > 6 else 'box'
        if shape == 'tree':
            draw.rectangle((sx - half * 0.15, (y0 + y1) / 2, sx + half * 0.15, y1), fill=(70, 54, 36))
            draw.ellipse((sx - half, y0, sx + half, y0 + (y1 - y0) * 0.6), fill=c)
        elif shape == 'cone':
            draw.rectangle((sx - half, y0 + (y1 - y0) * 0.3, sx + half, y1), fill=c)
            draw.polygon([(sx - half * 1.2, y0 + (y1 - y0) * 0.3), (sx + half * 1.2, y0 + (y1 - y0) * 0.3),
                          (sx, y0 - (y1 - y0) * 0.25)], fill=(150, 90, 80))
        elif shape == 'tent':
            draw.polygon([(sx - half, y1), (sx + half, y1), (sx, y0)], fill=c)
        elif shape == 'water':
            draw.rectangle((sx - half, y0, sx + half, y1), fill=(170, 200, 220))
        else:
            draw.rectangle((sx - half, y0, sx + half, y1), fill=c)
    for label, ax, ay, rise in annotations or []:
        mx_, my_ = (ax + 0.5) * RES, (ay + 0.5) * RES
        a = math.atan2(my_ - cy, mx_ - cx) - yaw
        a = (a + math.pi) % (2 * math.pi) - math.pi
        if abs(a) > math.radians(fov / 2):
            continue
        d = math.hypot(mx_ - cx, my_ - cy) / unit
        z = d * math.cos(a)
        sx = w / 2 + math.tan(a) * focal
        hb = height[int(min(my_, size - 1)), int(min(mx_, size - 1))]
        base = (hb if hb > 1 else 1000) + rise
        sy = horizon - (base - eye) / z * focal
        draw.ellipse((sx - 9, sy - 9, sx + 9, sy + 9), outline=(220, 30, 30), width=4)
        draw.text((sx + 12, sy - 12), label, fill=(200, 20, 20), font=FONT)
    out.save(out_path)


def models_for(sketch, plan, trees):
    """Blocks for the blockout: (cell x, cell y, base or None, height, half width cells, colour, shape)."""
    m = []
    sand = (214, 178, 120)
    # Sandcaster's walls (500 high on the terrace) and corner towers
    for x in range(27, 48, 2):
        m.append((x, 20, None, 520, 1.05, sand, 'box'))
        m.append((x, 39, None, 520, 1.05, sand, 'box'))
    for y in range(21, 39, 2):
        m.append((27, y, None, 520, 1.05, sand, 'box'))
        m.append((47, y, None, 520, 1.05, sand, 'box'))
    for tx, ty in [(27, 20), (47, 39), (27, 39), (37, 20), (27, 30), (47, 20)]:
        m.append((tx, ty, None, 800, 0.7, (224, 188, 128), 'box'))
    m.append((36.5, 39, None, 880, 1.2, (226, 190, 130), 'box'))      # south gatehouse
    m.append((47, 31.5, None, 880, 1.2, (226, 190, 130), 'box'))      # east gatehouse
    m.append((28.5, 21.5, None, 1900, 0.9, (226, 186, 124), 'box'))   # the Sky Stair
    m.append((28.5, 20.2, 1500 + 1800, 60, 1.6, (110, 80, 50), 'box'))  # Lucio's jetty on top, pointing north
    for qx, qy, hh in [(41.2, 25.2, 1500), (43.2, 25.7, 1700), (45.2, 25.2, 1450), (41.5, 22.5, 1200),
                       (45.2, 22.5, 1100)]:
        m.append((qx, qy, None, hh, 0.65, (210, 150, 140), 'cone'))   # the wizard quarter's pink towers
    m.append((43.5, 20.4, None, 1000, 1.0, (200, 140, 130), 'box'))  # the guild gate
    for bid, idx, door, service, (x, y, wx, wy), facing in plot_list(plan, sketch):
        if bid.startswith('building:wq_') or bid == 'building:sc_lucio_jetty':
            continue
        if bid == 'building:xr_stall':
            colours = [(200, 60, 50), (60, 90, 170), (220, 180, 60), (120, 60, 140), (60, 140, 90), (180, 120, 60)]
            m.append((x + wx / 2, y + wy / 2, None, 380, 0.55, colours[(idx or 1) - 1], 'tent'))
            continue
        hgt = 650 if service else 420
        if 'guild' in bid or 'temple' in bid:
            hgt = 900
        m.append((x + wx / 2, y + wy / 2, None, hgt, max(wx, wy) * 0.45, (206, 168, 114), 'box'))
    m += [
        (97, 46, None, 2600, 1.1, (70, 66, 74), 'cone'),         # the Great Eastern Tower
        (101, 57, None, 420, 0.7, (150, 130, 110), 'box'),        # the Rim Watch ruin
        (103.6, 64, 820, 420, 1.0, None, 'water'),               # the falls' spray over the lip
        (50.5, 27, None, 900, 0.25, (40, 40, 48), 'box'),         # obelisk
        (45, 47.5, None, 320, 0.9, (150, 136, 110), 'box'),       # Vespar's ruin
        (75.5, 46, 1250, 60, 2.0, (200, 180, 140), 'box'),        # Wrath Bridge deck
        (81.8, 74.8, None, 360, 0.75, (150, 120, 80), 'box'),     # Thaddeus's hut
        (79.6, 76.4, None, 200, 0.4, (90, 140, 90), 'box'),       # the Fountain of Youth
        (66.2, 49.8, None, 380, 0.75, (176, 140, 96), 'box'),     # Celia and Derek's cottage
        (88, 65, None, 300, 0.5, (150, 110, 60), 'box'),         # fruit hut
        (50, 62, None, 1500, 1.6, (176, 92, 40), 'tree'),         # the great oak
    ]
    m = [x if x[5] is not None else (x[0], x[1], x[2], x[3], x[4], (170, 200, 220), x[6]) for x in m]
    for x, y, c in trees[::2]:
        m.append((x, y, None, 760, 0.34, c, 'tree'))
    return m


BLOCKOUT_FOV = {'view:arrival': 82.0, 'view:signature': 78.0}
BLOCKOUT_PITCH = {'view:arrival': -1.5, 'view:signature': -4.0}  # negative looks down

ANNOTATIONS = {
    'view:arrival': [
        ('Sandcaster walls on the terrace', 30, 39, 400),
        ("Sky Stair + Lucio's jetty", 28.5, 21.5, 1950),
        ('wizard quarter towers', 43, 24, 1450),
        ("Vespar's ruin", 45, 47.5, 250),
        ('Crossroads stalls', 60, 44, 900),
        ('Aging Forest (red-gold)', 44, 54, 700),
    ],
    'view:signature': [
        ('River of Wrath', 92, 61.5, 20),
        ('Wrath Falls: river drops off the rim', 103.5, 64, 0),
        ("bright face's glow above the rim", 112, 56, 3200),
        ('Eastern Tower on its knoll', 97, 46, 2400),
        ('Rim Watch ruin', 101, 57, 700),
        ('fruit hut', 88, 65, 300),
    ],
}


# ---------------------------------------------------------------- figures

def point_in(poly, x, y):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def poly_dist(poly, x, y):
    if point_in(poly, x, y):
        return 0.0
    return min(seg_dist(x, y, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


# D-20's census: what is a bound event that does something
NOT_POI = ('poi:cornelius',)          # an NPC actor (a teacher): a place for the 6,000 rule, not a POI
POI_ENTRANCES = ('entrance:south_gate', 'entrance:east_gate', 'entrance:dd18_shaft', 'entrance:dd19_gate',
                 'entrance:dd07_door')


def census(plan, sketch):
    spots = []      # (label, x, y) in cells, centred
    for p in sketch['points']:
        pid = p['id']
        if pid.startswith('poi:') and pid not in NOT_POI or pid in POI_ENTRANCES:
            spots.append((pid, p['at'][0] + 0.5, p['at'][1] + 0.5))
    for bid, idx, door, service, rect, facing in plot_list(plan, sketch):
        if service:
            spots.append((bid + (f'#{idx}' if idx else ''), door[0], door[1]))
    n = len(spots)
    parent = list(range(n))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if math.hypot(spots[i][1] - spots[j][1], spots[i][2] - spots[j][2]) * 512 <= 400:
                parent[root(i)] = root(j)
    groups = {}
    for i in range(n):
        groups.setdefault(root(i), []).append(i)
    comps = []
    for g in groups.values():
        comps.append({'members': [spots[i][0] for i in g],
                      'at': [round(sum(spots[i][1] for i in g) / len(g), 2),
                             round(sum(spots[i][2] for i in g) / len(g), 2)]})
    return comps


def box_range(height, rim):
    x0, y0, x1, y1 = PLAY
    sub = height[y0 * RES:y1 * RES, x0 * RES:x1 * RES]
    land = ~rim[y0 * RES:y1 * RES, x0 * RES:x1 * RES]
    return [int(sub[land].min()), int(sub[land].max())]


def figures_for(plan, sketch, project, height, water, rim):
    x0, y0, x1, y1 = PLAY
    land = np.zeros((N, N), bool)
    land[y0:y1, x0:x1] = True
    hc = height[RES // 2::RES, RES // 2::RES]
    wc = water[RES // 2::RES, RES // 2::RES]
    land &= (hc > 1) & ~wc
    n_land = int(land.sum())
    enc = np.zeros((N, N), bool)
    areas = {}
    for area in sketch['areas']:
        if area.get('kind', 'encounter') != 'encounter':
            continue
        m = poly_mask(area['polygon'], scale=1)
        cells = int((m & land).sum())
        areas[area['id']] = {'slot': area['slot'], 'count': area['count'], 'cells': cells,
                             'cells_4096': round(cells / 64, 1)}
        enc |= m
    yy, xx = np.mgrid[0:N, 0:N]
    nests = [a['at'] for a in sketch['actors'] if a['count'] >= 3]
    for nx_, ny_ in nests:
        enc |= np.hypot(xx - nx_, yy - ny_) <= 3
    quiet = float(((~enc) & land).sum() / n_land)
    length = {'road': 0.0, 'lane': 0.0, 'high_road': 0.0}
    for r in sketch['roads']:
        for a, b in zip(r['line'], r['line'][1:]):
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.25))
            for i in range(n):
                t = (i + 0.5) / n
                x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                if 0 <= x < N and 0 <= y < N and land[int(y), int(x)]:
                    length[r.get('width', 'road')] += math.hypot(b[0] - a[0], b[1] - a[1]) / n
    road_share = float((length['road'] + length['high_road']) / n_land)
    lane_share = float(length['lane'] / n_land)
    pts_ = {p['id']: p['at'] for p in sketch['points'] if 'index' not in p}
    fights = [a['polygon'] for a in sketch['areas'] if a.get('kind', 'encounter') == 'encounter']
    placed = [a['at'] for a in sketch['actors']]
    plots = plot_list(plan, sketch)
    town_doors = [p[2] for p in plots]

    def first_fight(at):
        x, y = at[0] + 0.5, at[1] + 0.5
        d = min([poly_dist(p, x, y) for p in fights] + [math.hypot(x - a[0] - .5, y - a[1] - .5) for a in placed])
        return int(round(d * 512, -2))

    def nearest_fight_to_doors(doors):
        best = 1e9
        for dx_, dy_ in doors:
            best = min(best, min([poly_dist(p, dx_, dy_) for p in fights]
                                 + [math.hypot(dx_ - a[0] - .5, dy_ - a[1] - .5) for a in placed]))
        return int(round(best * 512, -2))
    edge = {k: first_fight(pts_[k]) for k in ['entrance:west_road', 'entrance:north_road']}
    town_arr = {k: first_fight(pts_[k]) for k in ['entrance:sandcaster_square', 'entrance:sandcaster_stables']}
    sc_doors = [p[2] for p in plots if p[0].startswith(('building:sc_', 'building:wq_'))]
    xr_doors = [p[2] for p in plots if p[0] == 'building:xr_stall']
    hut_doors = {p[0]: p[2] for p in plots if p[0] in ('building:celia_derek_cottage', 'building:thaddeus_hut')}
    buffers = {'Sandcaster doors': nearest_fight_to_doors(sc_doors),
               'Crossroads stalls': nearest_fight_to_doors(xr_doors),
               "Celia and Derek's cottage": nearest_fight_to_doors([hut_doors['building:celia_derek_cottage']]),
               "Thaddeus's hut": nearest_fight_to_doors([hut_doors['building:thaddeus_hut']]),
               'Cornelius': first_fight(pts_['poi:cornelius'])}
    comps = census(plan, sketch)
    # places for the 6,000 rule: every point on land (POIs, NPCs, entrances, junctions, landmarks), every door
    seed = np.zeros((N, N), bool)
    for p in sketch['points']:
        x, y = p['at']
        if 0 <= x < N and 0 <= y < N and not rim[int((y + .5) * RES), int((x + .5) * RES)]:
            seed[int(y), int(x)] = True
    for dx_, dy_ in town_doors:
        seed[int(dy_), int(dx_)] = True
    seed |= enc
    for d in sketch['districts']:
        if d['space'].startswith('town:'):
            seed |= poly_mask(d['polygon'], scale=1)
    dist = ndimage.distance_transform_edt(~seed) * 512
    far = float(((dist > 3000) & land).sum() / n_land)
    farthest = int(round(dist[land].max(), -2))
    fy, fx = np.unravel_index(np.argmax(np.where(land, dist, 0)), dist.shape)
    # wild land (outside towns) far from anything: the D-11.5 figure
    nn = []
    cpts = [c['at'] for c in comps]
    for i, a in enumerate(cpts):
        nn.append(min(math.hypot(a[0] - b[0], a[1] - b[1]) for j, b in enumerate(cpts) if j != i) * 512)
    towns = {}
    for space, prefix in [('town:sandcaster', ('building:sc_', 'building:wq_')), ('town:crossroads',
                                                                                   ('building:xr_',))]:
        poly = next(d['polygon'] for d in sketch['districts'] if d['space'] == space)
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        cells = (max(xs) - min(xs)) * (max(ys) - min(ys))
        nb = sum(1 for p in plots if p[0].startswith(prefix) and p[0] != 'building:sc_stables')
        towns[space] = {'cells': cells, 'extent': [int((max(xs) - min(xs)) * 512), int((max(ys) - min(ys)) * 512)],
                        'buildings': nb, 'per_100': round(100 * nb / cells, 1),
                        'services': sum(1 for p in plots if p[0].startswith(prefix) and p[3])}
    hs = [p['h'] for p in sketch['heights']['points']]
    low = min([b['level'] for b in sketch['water']['bodies'] if b['id'] != 'water:rim_sea']
              + [r['level'] for r in sketch['water']['rivers']])
    slots = project['map_stats']['slots']
    mean = {i + 1: (s['per_marker'][0] + s['per_marker'][1]) / 2 for i, s in enumerate(slots)}
    marker_hostiles = sum(a['count'] * mean[a['slot']] for a in sketch['areas'] if a.get('kind', 'encounter') ==
                          'encounter')
    placed_n = sum(a['count'] for a in sketch['actors'])
    xp = lambda L: L * (L + 10)
    dif = {0: (1, 0, 0), 1: (0.9, 0.08, 0.02), 2: (0.7, 0.2, 0.1)}
    levels = {1: (22, 30, 38), 2: (30, 38, 45), 3: (30, 38, 45)}
    kill = 0.0
    per_family = {}
    for a in sketch['areas']:
        if a.get('kind', 'encounter') != 'encounter':
            continue
        s = a['slot']
        mix = dif[slots[s - 1]['tier']]
        v = a['count'] * mean[s] * sum(w * xp(L) for w, L in zip(mix, levels[s]))
        kill += v
        per_family[slots[s - 1]['monster']] = per_family.get(slots[s - 1]['monster'], 0) + v
    actor_levels = {'11350': 35, '11351': 42}
    hv = sum(a['count'] * xp(actor_levels[a['monster']]) for a in sketch['actors'])
    kill += hv
    per_family['Xeen Hornet (placed)'] = hv
    pois = plan['points_of_interest']
    chests = [p['id'] for p in pois if p['kind'] == 'chest']
    return {
        'land_cells': n_land,
        'quiet_share': round(quiet, 3),
        'areas': areas,
        'markers': sum(a['count'] for a in sketch['areas'] if a.get('kind', 'encounter') == 'encounter'),
        'hostiles_markers': marker_hostiles,
        'hostiles_placed': placed_n,
        'hostiles': marker_hostiles + placed_n,
        'kill_xp_member': round(kill / 4 / 1000, 1),
        'kill_xp_by_family_member': {k: round(v / 4 / 1000, 1) for k, v in per_family.items()},
        'road_share': round(road_share, 4),
        'lane_share': round(lane_share, 4),
        'first_fight_edges': edge,
        'first_fight_town_arrivals': town_arr,
        'town_buffers': buffers,
        'far_share_3000': round(far, 3),
        'farthest_from_place': farthest,
        'farthest_at': [int(fx), int(fy)],
        'poi_count': len(comps),
        'poi_components': comps,
        'poi_nn_median': int(round(float(np.median(nn)), -1)),
        'poi_nn_min': int(round(min(nn), -1)),
        'poi_nn_max': int(round(max(nn), -1)),
        'chests': len(chests),
        'chest_ids': chests,
        'entrances': 3,
        'height_range': [low, max(hs)],
        'height_range_box': box_range(height, rim),   # D-28: inside the playable box, land only
        'height_span': max(hs) - low,
        'towns': towns,
    }


def chrome(svg, png, scale=1):
    args = ['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
            f'--screenshot={png}', '--window-size=1600,1750', f'file://{svg}']
    if scale != 1:
        args.insert(5, f'--force-device-scale-factor={scale}')
    subprocess.run(args, check=True, capture_output=True, timeout=120)


def main():
    plan, sketch, project = load()
    OUT.mkdir(parents=True, exist_ok=True)
    height, water, rim = build_land(sketch)
    np.save(OUT / 'height.npy', height.astype(np.float32))
    img, trees, bare = colour_land(sketch, height, water, rim)
    img.save(OUT / 'colour.png')
    figures = figures_for(plan, sketch, project, height, water, rim)
    (OUT / 'figures.json').write_text(json.dumps(figures, indent=1))
    svg = svg_plan(plan, sketch, img, figures)
    (OUT / 'plan_d3.svg').write_text(svg)
    chrome(OUT / 'plan_d3.svg', OUT / 'plan_d3.png')
    chrome(OUT / 'plan_d3.svg', OUT / 'plan_d3_2x.png', scale=2)
    models = models_for(sketch, plan, trees)
    for view in sketch.get('views', []):
        name = view['id'].split(':')[1]
        blockout(height, bare, view, models, OUT / f'blockout_{name}.png', annotations=ANNOTATIONS.get(view['id']),
                 fov=BLOCKOUT_FOV.get(view['id'], 80.0))
    print(json.dumps({k: v for k, v in figures.items() if k not in ('areas', 'chest_ids', 'poi_components')},
                     indent=1))


if __name__ == '__main__':
    main()
