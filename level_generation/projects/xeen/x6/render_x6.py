#!/usr/bin/env python3
"""X6's MU-3 drawing, MU-4 blockouts and measured figures, from the L1 brief (A5, 2026-11-20).

    render_x6.py        reads devdocs/xeen/briefs/x6/L1/{plan,sketch,project}.yml

Writes into output/studio_cal/x6/mockups/:
  height.npy, colour.png     the land the sketch implies (for the drawings only; the studio builds its own)
  plan_x6.svg, plan_x6.png   the to-scale plan (PNG through headless Chrome), plan_x6_2x.png for the board's crops
  blockout_<view>.png        a crude perspective of each sketch view (Codex's composition reference)
  figures.json               the measured figures for the board and the NOTES

Nothing here is read by the game or the studio. Adapted from level_generation/projects/xeen/d3/render_d3.py; the POI count
is the D-20 census (chained within 400, service doors in, residences, NPCs, exits and landmarks out). The height
range is measured on the drawn land inside the playable square (D-28), not on the crags outside it.
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
BRIEF = ROOT / 'devdocs/xeen/briefs/x6/L1'
OUT = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x6') / 'mockups'
RES = 6
N = 128
PLAY = (24, 24, 109, 109)     # the playable square [19, 109] cut by the west and north rims (x 24, y 24)
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)

BAND_BASE = {'band:rim_sea': 0, 'band:oasis': 1100, 'band:pan': 1250, 'band:desert': 1420, 'band:dunes': 1480,
             'band:downs': 1750, 'band:heights': 2450, 'band:peaks': 2800}
GROUND = {  # sRGB per space, painted in this order over the default sand
    'zone:central_pan': (206, 182, 132),
    'zone:sphinx_desert': (224, 194, 138),
    'zone:west_dunes': (228, 200, 146),
    'zone:cliff_foot': (196, 164, 120),
    'zone:ruin_fields': (196, 178, 140),
    'zone:south_steppe': (176, 164, 112),
    'zone:east_downs': (190, 160, 112),
    'zone:stony_rises': (160, 140, 112),
    'zone:basenji_heights': (150, 108, 88),
    'zone:gargoyle_foothills': (140, 116, 100),
    'zone:barbaric_mountains': (150, 104, 84),
    'zone:oasis': (120, 140, 80),
    'town:sphinx_wells': (200, 176, 128),
    'zone:coach_yard': (184, 164, 128),
    'zone:druid_grove': (120, 136, 76),
}
TREES = {  # space: (trees per cell, [colours])
    'zone:oasis': (0.7, [(60, 110, 50), (74, 124, 56)]),
    'town:sphinx_wells': (0.25, [(60, 110, 50)]),
    'zone:druid_grove': (0.8, [(92, 120, 64), (110, 128, 70)]),
    'zone:south_steppe': (0.04, [(120, 120, 70)]),
    'zone:east_downs': (0.02, [(120, 116, 70)]),
    'zone:central_pan': (0.01, [(110, 116, 66)]),
    'zone:saul_hermitage': (0.3, [(60, 110, 50)]),
}
TOWN_LEVEL = {'town:sphinx_wells': 1250, 'zone:coach_yard': 1500, 'zone:arie_camp': 1450, 'zone:oasis': 1080,
              'zone:saul_hermitage': 1400, 'zone:druid_grove': 1450, 'zone:basenji_crag': 2700,
              'zone:sphinx_forecourt': 1400, 'zone:southern_sphinx': 1550}


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
    height = np.full((size, size), 1300.0)
    for band in sketch['heights']['bands']:
        if band['band'] != 'band:rim_sea':
            height[poly_mask(band['polygon'])] = BAND_BASE[band['band']]
    height = ndimage.gaussian_filter(height, 4 * RES)
    yy, xx = np.mgrid[0:size, 0:size] / RES
    for point in sketch['heights'].get('points', []):
        px, py = point['at']
        r = 7.0 if point['h'] > 2600 else 4.0
        if 'mesa' in point.get('notes', ''):
            r = 3.2
        d = np.hypot(xx - px - 0.5, yy - py - 0.5)
        t = np.clip(1 - d / r, 0, 1)
        w = t * t * (3 - 2 * t)
        if 'mesa' in point.get('notes', ''):
            w = np.clip(w * 2.2, 0, 1)        # flat tops, steep sides
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
    dune = np.sin((xx * 0.9 + yy * 0.35) * 1.6 + noise * 6) * 0.5 + 0.5
    masks = districts(sketch)
    dunes = np.zeros((size, size), bool)
    for space in ('zone:sphinx_desert', 'zone:west_dunes'):
        dunes |= masks.get(space, dunes)
    dunes = ndimage.gaussian_filter(dunes.astype(float), 2 * RES)
    calm = np.zeros((size, size), bool)
    for space in TOWN_LEVEL:
        if space in masks:
            calm |= masks[space]
    calm = ndimage.binary_dilation(calm, iterations=2 * RES)
    steep = np.clip((height - 1800) / 1200, 0, 1)
    height += np.where(calm, 0, noise * 140 + rough * (25 + 260 * steep) + dune * dunes * 110)
    for space, level in TOWN_LEVEL.items():
        if space in masks:
            soft = ndimage.gaussian_filter(masks[space].astype(float), RES * 0.6)
            height = height * (1 - soft) + level * soft
    water = np.zeros((size, size), bool)
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
    rgb[:] = (214, 188, 136)
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
    rock = np.clip((slope - 0.45) * 2.2, 0, 1)
    rock = np.maximum(rock, np.clip((height - 2300) / 700, 0, 0.75))
    yy, xx = np.mgrid[0:size, 0:size] / RES
    for point in sketch['heights'].get('points', []):
        if 'mesa' in point.get('notes', ''):
            px, py = point['at']
            rock = np.maximum(rock, np.clip(3.4 - np.hypot(xx - px - 0.5, yy - py - 0.5), 0, 1) * 0.85)
    rgb = rgb * (1 - rock[..., None]) + np.array((150, 92, 72)) * rock[..., None]
    dist = ndimage.distance_transform_edt(~water) / RES
    bank = np.clip(1 - dist / 2.5, 0, 1)[..., None] * (~water)[..., None] * 0.6
    rgb = rgb * (1 - bank) + np.array((96, 128, 66)) * bank
    light = np.array([-0.55, -0.65, 0.52])
    nx, ny = -gx * 2.2, -gy * 2.2
    nz = np.ones_like(nx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    shade = (nx * light[0] + ny * light[1] + nz * light[2]) / norm
    shade = np.clip(0.6 + 0.55 * shade, 0.38, 1.15)
    rgb = rgb * shade[..., None]
    rgb[water] = rgb[water] * 0.3 + np.array((60, 130, 150)) * 0.7
    stars = np.zeros((size, size, 3))
    stars[:] = (10, 12, 26)
    rng = np.random.default_rng(3)
    for y, x in rng.integers(0, size, size=(2400, 2)):
        stars[y, x] = rng.integers(140, 255)
    rgb[rim] = stars[rim]
    cliff = ndimage.binary_dilation(~rim, iterations=int(1.0 * RES)) & rim
    rgb[cliff] = (132, 96, 78)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    bare = img.copy()
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    trees = []
    for space, (density, colours) in TREES.items():
        if space not in masks:
            continue
        ys, xs = np.nonzero(masks[space][::RES, ::RES])
        for cy, cx in zip(ys, xs):
            for _ in range(rng.poisson(density * 2)):
                x = (cx + rng.random()) * RES
                y = (cy + rng.random()) * RES
                hy, hx = int(min(y, size - 1)), int(min(x, size - 1))
                if water[hy, hx] or rim[hy, hx] or height[hy, hx] > 2400 or slope[hy, hx] > 0.6:
                    continue
                colour = colours[rng.integers(len(colours))]
                s = RES * (0.3 + 0.15 * rng.random())
                draw.ellipse((x - s, y - s * 0.8, x + s, y + s * 0.8), fill=colour)
                trees.append((x / RES, y / RES, colour))
    return img, trees, bare


# ---------------------------------------------------------------- labels

KINDS = {
    'entrance:east_road': 'arrival', 'entrance:south_road': 'arrival',
    'entrance:sphinx_wells': 'town_arrival', 'entrance:warzone_coach': 'town_arrival',
    'entrance:yard_gate': 'gate',
    'entrance:xd14_gate': 'dungeon', 'entrance:xd15_door': 'dungeon', 'entrance:xd20_gate': 'dungeon',
    'entrance:fd02_door': 'dungeon',
    'poi:swallowed_wagon': 'chest', 'poi:werewolf_den': 'chest', 'poi:caravanserai': 'chest',
    'poi:bone_field': 'chest', 'poi:rim_pack': 'chest', 'poi:mesa_nest': 'chest', 'poi:prospector_camp': 'chest',
    'poi:arie': 'npc', 'poi:saul': 'npc', 'poi:summer_druid': 'npc', 'poi:signposts': 'sign',
    'landmark:basenji': 'landmark', 'landmark:northern_sphinx': 'landmark', 'landmark:southern_sphinx': 'landmark',
    'landmark:red_mesas': 'landmark', 'landmark:barbaric_mountains': 'landmark', 'landmark:sand_falls': 'landmark',
}
for j in ['junction:wells_fork', 'junction:sphinx_fork', 'junction:south_fork']:
    KINDS[j] = 'junction'

# id: (text, dx px, dy px, anchor); None hides the label
NAMES = {
    'entrance:east_road': ('from X4 Burlock (y 60)', -14, -18, 'end'),
    'entrance:south_road': ('from X5 Winterkill (x 50)', 14, 4, 'start'),
    'entrance:sphinx_wells': None, 'entrance:warzone_coach': None, 'entrance:yard_gate': None,
    'entrance:xd14_gate': ('XD-14 Castle Basenji', 12, 22, 'start'),
    'entrance:xd15_door': ('XD-15 the Sphinx (amulet)', 12, 20, 'start'),
    'entrance:xd20_gate': None,
    'entrance:fd02_door': ('FD-02 Southern Sphinx (Act VI)', 12, 4, 'start'),
    'junction:wells_fork': None,
    'junction:sphinx_fork': ('Sphinx fork', 12, 18, 'start'),
    'junction:south_fork': ('South fork', 12, 4, 'start'),
    'poi:obelisk': ('Obelisk', -12, 4, 'end'),
    'poi:wells_well': None,
    'poi:oasis_fountain': ('oasis fountain (+2 End)', -12, -10, 'end'),
    'poi:well_accuracy': ('Well of Accuracy', 12, 4, 'start'),
    'poi:shrine_energy': ('Shrine of Energy', 12, 4, 'start'),
    'poi:waters_power': ('Waters of Great Power', 12, 18, 'start'),
    'poi:air_reflector': ('Air Reflector (M37)', 12, 4, 'start'),
    'poi:saul_urn': None,
    'poi:cloud_hoard': None,
    'poi:arie': ("Arie's camp (Q-C8)", 12, 4, 'start'),
    'poi:saul': ("Saul's hermitage, urn", 12, -6, 'start'),
    'poi:summer_druid': ('Summer Druid (Q-C1)', -12, 4, 'end'),
    'poi:swallowed_wagon': ('swallowed wagon', 12, 4, 'start'),
    'poi:werewolf_den': ("werewolves' den", 12, 4, 'start'),
    'poi:caravanserai': ('ruined caravanserai', 12, 4, 'start'),
    'poi:bone_field': ('bone fields', 12, 4, 'start'),
    'poi:rim_pack': ("explorer's pack", 12, 4, 'start'),
    'poi:mesa_nest': ('mesa nest', -12, -6, 'end'),
    'poi:sun_stones': ('sun stones', 12, 4, 'start'),
    'poi:caravan_cairn': ('caravan cairn', 12, -6, 'start'),
    'poi:prospector_camp': ("prospector's camp", -12, -8, 'end'),
    'landmark:basenji': None,
    'landmark:northern_sphinx': None,
    'landmark:southern_sphinx': None,
    'landmark:red_mesas': None,
    'landmark:barbaric_mountains': None,
    'landmark:sand_falls': None,
    'poi:signposts': None,
}
AREA_CAPTION = {'pop:sphinx_dunes': (93, 30), 'pop:west_dunes': (36, 98), 'pop:basenji_heights': (50, 26.6),
                'pop:east_downs': (100, 70), 'pop:ruin_fields': (71, 72), 'pop:barbaric': (103, 106)}
ENC_COLOURS = {1: '#b8620a', 2: '#c0282d', 3: '#6b3fa0'}
FAMILY = {1: 'Sand burrowers', 2: 'Werewolves', 3: 'Sand golems'}
CAPTIONS = [
    ('CASTLE BASENJI', (38.5, 26.2), 15, '#f0e0d0'),
    ('THE DESERT OF THE SPHINX', (78, 50.5), 15, '#5a3a08'),
    ('SPHINX WELLS', (61.5, 69.6), 14, '#222'),
    ('the pan', (88, 58), 13, '#5a4010'),
    ('the rim dunes', (36, 76), 14, '#5a3a08'),
    ('THE BARBARIC MOUNTAINS', (101, 84.4), 14, '#2a1008'),
    ('the bone fields', (70, 84.6), 13, '#3a2a10'),
    ('the dry downs', (113, 76), 13, '#3a2a10'),
    ('the south steppe', (60, 99), 13, '#3a2a10'),
    ('Gargoyle foothills', (114, 30), 13, '#e8e8e8'),
    ('the world rim: a cliff above the stars', (64, 21.5), 14, '#ccd'),
    ('the west rim: sand pours into the stars', (11, 64), 13, '#ccd'),
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


def plot_list(plan, sketch):
    """Every plot: (building id, index, door [x, y] in cells, service?, rect, facing)."""
    buildings = {}
    for space in plan['spaces']:
        for b in space.get('buildings', []) or []:
            buildings[b['id']] = b
    out = []
    for d in sketch.get('districts', []):
        for plot in d.get('plots', []) or []:
            b = buildings[plot['building']]
            fp = b['footprint_cells'][(plot.get('index') or 1) - 1]
            service = b['service'] != 'residence'
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
         'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#0b6b3a"/></marker></defs>']
    # sand streaming off the west rim
    for k in range(9):
        y = 66 + k * 4.4
        o.append(f'<path d="M{24 * scale},{y * scale} q-{3 * scale},{0.6 * scale} -{9 * scale},{2.4 * scale}" '
                 'fill="none" stroke="#e8d0a0" stroke-opacity="0.45" stroke-width="3" stroke-dasharray="2 5"/>')
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
    for road in sketch.get('roads', []):
        lane = road.get('width') == 'lane'
        w = 3 if lane else 6
        o.append(f'<polyline points="{pts(road["line"], scale)}" fill="none" stroke="#3b2a1a" stroke-width="{w + 2}" '
                 'stroke-opacity="0.6" stroke-linecap="round" stroke-linejoin="round"/>')
        dash = ' stroke-dasharray="7 4"' if lane else ''
        o.append(f'<polyline points="{pts(road["line"], scale)}" fill="none" '
                 f'stroke="{"#f2e6c4" if lane else "#d2a868"}" stroke-width="{w}" stroke-linecap="round" '
                 f'stroke-linejoin="round"{dash}/>')
    # Castle Basenji: curtain wall and towers on the crag
    o.append(f'<polygon points="{pts([[34, 28], [43, 28], [43, 36], [34, 36]], scale)}" fill="#4a4048" '
             'fill-opacity="0.75" stroke="#1a1418" stroke-width="3"/>')
    for tx, ty in [(34, 28), (43, 28), (34, 36), (43, 36), (38.5, 30.5)]:
        o.append(f'<circle cx="{tx * scale}" cy="{ty * scale}" r="{0.9 * scale}" fill="#2a2228" stroke="#c8b8a8" '
                 'stroke-width="1.2"/>')
    # the Northern Sphinx (body, head, paws) facing south, and the Southern Sphinx facing east (half buried)
    o.append(f'<rect x="{80 * scale}" y="{33 * scale}" width="{5 * scale}" height="{9 * scale}" rx="{1.5 * scale}" '
             'fill="#d8b070" stroke="#4a3010" stroke-width="2"/>')
    o.append(f'<circle cx="{82.5 * scale}" cy="{40.5 * scale}" r="{1.6 * scale}" fill="#e0bc7c" stroke="#4a3010" '
             'stroke-width="2"/>')
    for pxx in (80.4, 83.6):
        o.append(f'<rect x="{pxx * scale}" y="{41 * scale}" width="{1 * scale}" height="{3 * scale}" fill="#d8b070" '
                 'stroke="#4a3010" stroke-width="1.5"/>')
    o.append(f'<rect x="{31.5 * scale}" y="{83 * scale}" width="{5 * scale}" height="{3 * scale}" rx="{1 * scale}" '
             'fill="#c8a468" fill-opacity="0.8" stroke="#4a3010" stroke-width="2" stroke-dasharray="4 3"/>')
    o.append(f'<circle cx="{37 * scale}" cy="{84.5 * scale}" r="{1.3 * scale}" fill="#d8b070" stroke="#4a3010" '
             'stroke-width="2"/>')
    # the coach yard's wall (gate gap on the west), the arena gate in the cliff
    yard = [[83, 92], [89, 92], [89, 98], [83, 98]]
    o.append(f'<polyline points="{pts([[83, 95.4], [83, 92], [89, 92], [89, 98], [83, 98], [83, 96.6]], scale)}" '
             'fill="none" stroke="#6a5a40" stroke-width="4"/>')
    o.append(f'<polygon points="{pts(yard, scale)}" fill="#b0a080" fill-opacity="0.25"/>')
    o.append(f'<rect x="{82.6 * scale}" y="{95.4 * scale}" width="{0.8 * scale}" height="{1.2 * scale}" '
             'fill="#e0b040" stroke="#222" stroke-width="1.5"/>')
    # Sphinx Wells' camel pen behind the stables
    o.append(f'<rect x="{62.5 * scale}" y="{56.4 * scale}" width="{3 * scale}" height="{1.4 * scale}" fill="none" '
             'stroke="#6a5030" stroke-width="1.5" stroke-dasharray="3 2"/>')
    # plots
    for bid, idx, door, service, (x, y, wx, wy), facing in plot_list(plan, sketch):
        fill = '#7a3a26' if service else '#9a7a5a'
        o.append(f'<rect x="{x * scale:.1f}" y="{y * scale:.1f}" width="{wx * scale:.1f}" height="{wy * scale:.1f}" '
                 f'fill="{fill}" stroke="#2a1a10" stroke-width="1.2"/>')
        o.append(f'<circle cx="{door[0] * scale:.1f}" cy="{door[1] * scale:.1f}" r="2.8" fill="#ffd34d" '
                 'stroke="#2a1a10" stroke-width="0.8"/>')
    for view in sketch.get('views', []):
        x, y = view['at']
        lx, ly = view['look']
        ang = math.atan2(ly - y, lx - x)
        dist = math.hypot(lx - x, ly - y)
        half = math.radians(39)
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
        dx, dy = (-10, 30) if 'arrival' in view['id'] else (12, 4)
        o.append(f'<text x="{(x + .5) * scale + dx}" y="{(y + .5) * scale + dy}" font-size="13" font-weight="bold" '
                 f'text-anchor="{"end" if dx < 0 else "start"}" fill="#0d3f80" stroke="#fff" stroke-width="3.2" '
                 f'paint-order="stroke">{name}</text>')
    seen = set()
    for point in sketch.get('points', []):
        pid = point['id']
        x, y = point['at']
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
        ((61.5, 59), (66, 54.6), 'Sphinx Wells: tavern 4301, caravans 4302, 2 homes, well'),
        ((86, 96.5), (66, 104.5), 'coach yard (D-8.1): coach house 4305, arena gate XD-20,'),
        ((83, 96), (66, 106), 'desert gate barred from inside (x6.warzone_gate)'),
        ((82.5, 44.5), (88, 47.5), "cloud hoard mound between the paws (obelisks)"),
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
    o.append(f'<text x="{11 * scale}" y="{8 * scale}" font-size="15" font-weight="bold" text-anchor="middle" '
             'fill="#fff">X6 Desert of</text>')
    o.append(f'<text x="{11 * scale}" y="{9.5 * scale}" font-size="15" font-weight="bold" text-anchor="middle" '
             'fill="#fff">the Sphinx</text>')
    o.append(f'<text x="{11 * scale}" y="{11.2 * scale}" font-size="12" text-anchor="middle" fill="#ccc">MU-3 plan, '
             'A5, 2026-11-20</text>')
    bx, by = 2 * scale, 120 * scale
    for i in range(10):
        o.append(f'<rect x="{bx + i * scale}" y="{by - 6}" width="{scale}" height="8" '
                 f'fill="{"#fff" if i % 2 == 0 else "#333"}" stroke="#fff" stroke-width="0.6"/>')
    o.append(f'<text x="{bx}" y="{by + 20}" font-size="13" fill="#fff">5,120 units (10 cells of 512)</text>')
    ly = size + 26
    items = [
        ('sq', '#0b6b3a', 'edge arrival (arrow: facing)'), ('sqs', '#2fa860', 'town arrival'),
        ('gate', '#e0b040', "coach yard's desert gate"), ('sq', '#111', 'dungeon entrance'),
        ('dia', '#d8a010', 'chest with a reason'), ('dot', '#1d5fa8', 'NPC outdoors (not a POI)'),
        ('dot', '#8a1f7a', 'device / place'), ('star', '#e07000', 'landmark'),
        ('enc', '#b8620a', 'encounter: sand burrowers'), ('enc', '#c0282d', 'encounter: werewolves'),
        ('enc', '#6b3fa0', 'encounter: sand golems'), ('quiet', '#2e8b57', 'keep clear / quiet by design'),
        ('road', '#d2a868', 'road'), ('lane', '#f2e6c4', 'lane / path'),
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
            dash = ' stroke-dasharray="6 3"' if shape == 'lane' else ''
            o.append(f'<line x1="{x}" y1="{y}" x2="{x + 20}" y2="{y}" stroke="{col}" '
                     f'stroke-width="{6 if shape == "road" else 3}"{dash}/>')
        elif shape == 'cam':
            o.append(f'<circle cx="{x + 7}" cy="{y}" r="6" fill="{col}" stroke="#fff"/>'
                     f'<line x1="{x + 7}" y1="{y}" x2="{x + 24}" y2="{y - 6}" stroke="{col}" stroke-width="2"/>')
        o.append(f'<text x="{x + 28}" y="{y + 5}" font-size="14" fill="#e8e8e8">{esc(text)}</text>')
    q = figures['quiet_share']
    o.append(f'<text x="10" y="{ly + 4 * 28 + 4}" font-size="14" fill="#bbb">Land outside the coloured '
             f'areas is quiet: {q * 100:.0f} % of the playable land. Dashed white: the playable bounds; the land runs '
             'on to the east and south edges; west of x 24 and north of y 24, the stars.</text>')
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
    # Cloudside's clear arid sky: a deep blue zenith, a pale hot haze at the horizon
    for yy in range(h):
        t = np.clip((yy - (horizon - 560)) / 560, 0, 1)
        img[yy, :] = np.array((70, 120, 190)) * (1 - t) + np.array((236, 226, 200)) * t
    zs = np.concatenate([np.arange(60, 2000, 12.0), np.arange(2000, max_d, 40.0)])
    haze = np.array((232, 220, 192))
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
                fog = min(1.0, (zs[k] / 42000.0) ** 1.5) * 0.7
                c = c * (1 - fog) + haze * fog
                img[max(sy, 0):ybuf, sx] = c
                ybuf = max(sy, 0)
                if ybuf == 0:
                    break
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
        if abs(a) > math.radians(fov / 2 + 5) or d < 200 or (len(m) > 6 and m[6] == 'tree' and d < 1200):
            continue
        z = d * math.cos(a)
        sx = w / 2 + math.tan(a) * focal
        base = height[int(min(my_, size - 1)), int(min(mx_, size - 1))] if m[2] is None else m[2]
        top = base + m[3]
        y0 = horizon - (top - eye) / z * focal
        y1 = horizon - (base - eye) / z * focal
        half = m[4] * 512 / z * focal
        fog = min(1.0, (d / 42000.0) ** 1.5) * 0.7
        c = tuple(int(v * (1 - fog) + f * fog) for v, f in zip(m[5], haze))
        shape = m[6] if len(m) > 6 else 'box'
        if shape == 'tree':
            draw.rectangle((sx - half * 0.12, (y0 + y1) / 2, sx + half * 0.12, y1), fill=(110, 84, 56))
            draw.ellipse((sx - half, y0, sx + half, y0 + (y1 - y0) * 0.45), fill=c)
        elif shape == 'cone':
            draw.rectangle((sx - half, y0 + (y1 - y0) * 0.3, sx + half, y1), fill=c)
            draw.polygon([(sx - half * 1.2, y0 + (y1 - y0) * 0.3), (sx + half * 1.2, y0 + (y1 - y0) * 0.3),
                          (sx, y0 - (y1 - y0) * 0.25)], fill=(40, 36, 44))
        elif shape == 'tent':
            draw.polygon([(sx - half, y1), (sx + half, y1), (sx, y0)], fill=c)
        elif shape == 'sphinx':
            # a long low body with a raised head at the front
            draw.rectangle((sx - half, y0 + (y1 - y0) * 0.45, sx + half, y1), fill=c)
            draw.rectangle((sx - half * 0.28, y0, sx + half * 0.28, y1), fill=tuple(int(v * 1.06) for v in c))
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
        base = (hb if hb > 1 else 1400) + rise
        sy = horizon - (base - eye) / z * focal
        draw.ellipse((sx - 9, sy - 9, sx + 9, sy + 9), outline=(220, 30, 30), width=4)
        draw.text((sx + 12, sy - 12), label, fill=(200, 20, 20), font=FONT)
    out.save(out_path)


def models_for(sketch, plan, trees):
    """Blocks for the blockout: (cell x, cell y, base or None, height, half width cells, colour, shape)."""
    m = []
    grey = (92, 84, 90)
    # Castle Basenji on its crag: a curtain wall, four corner towers and a keep (grey rubble, black roofs)
    for x in range(34, 44, 2):
        m.append((x, 28, 2700, 520, 1.05, grey, 'box'))
        m.append((x, 36, 2700, 520, 1.05, grey, 'box'))
    for y in range(29, 36, 2):
        m.append((34, y, 2700, 520, 1.05, grey, 'box'))
        m.append((43, y, 2700, 520, 1.05, grey, 'box'))
    for tx, ty in [(34, 28), (43, 28), (34, 36), (43, 36)]:
        m.append((tx, ty, 2700, 1000, 0.8, (78, 70, 78), 'cone'))
    m.append((38.5, 31, 2700, 1500, 1.4, (70, 64, 72), 'cone'))      # the keep
    m.append((38.5, 36.4, 2700, 700, 1.0, (84, 76, 82), 'box'))       # the gatehouse
    # the Northern Sphinx facing south: body along y 33-42, head at the front
    m.append((82.5, 37.5, 1400, 900, 2.6, (214, 176, 112), 'box'))
    m.append((82.5, 40.5, 1400, 1600, 1.4, (222, 186, 122), 'box'))
    m.append((81, 43, 1400, 300, 0.5, (214, 176, 112), 'box'))
    m.append((84, 43, 1400, 300, 0.5, (214, 176, 112), 'box'))
    # the Southern Sphinx facing east, buried to the shoulders
    m.append((34, 84.5, 1450, 420, 2.4, (206, 170, 110), 'box'))
    m.append((37, 84.5, 1450, 950, 1.2, (214, 178, 116), 'box'))
    # Sphinx Wells
    for bid, idx, door, service, (x, y, wx, wy), facing in plot_list(plan, sketch):
        if bid == 'building:warzone_coach':
            m.append((x + wx / 2, y + wy / 2, 1500, 520, max(wx, wy) * 0.45, (176, 160, 130), 'box'))
            continue
        m.append((x + wx / 2, y + wy / 2, None, 560 if service else 420, max(wx, wy) * 0.45, (214, 192, 150),
                  'box'))
    m.append((61.5, 61.5, None, 120, 0.3, (150, 130, 100), 'box'))     # Old Ibb's well
    # the coach yard wall and the arena gate in the cliff
    for x in range(83, 90, 2):
        m.append((x, 92, 1500, 380, 1.05, (170, 150, 116), 'box'))
        m.append((x, 98, 1500, 380, 1.05, (170, 150, 116), 'box'))
    for y in (93, 97):
        m.append((83, y, 1500, 380, 1.05, (170, 150, 116), 'box'))
    m.append((88.6, 95, 1500, 900, 1.2, (120, 92, 76), 'box'))
    m += [
        (75, 51, None, 900, 0.25, (40, 40, 48), 'box'),          # obelisk
        (26, 26, None, 700, 0.6, (120, 140, 160), 'box'),        # the Air Reflector
        (78, 76, None, 420, 1.6, (180, 150, 110), 'box'),        # the ruined caravanserai
        (30, 70, None, 380, 0.7, (170, 146, 110), 'box'),        # Saul's hut
        (31, 71, None, 140, 0.2, (150, 110, 70), 'box'),         # the urn
        (45, 45, None, 240, 0.5, (190, 160, 120), 'tent'),       # Arie's tent
        (30, 48, None, 450, 0.5, (160, 150, 170), 'box'),        # Shrine of Energy
        (94, 32, None, 200, 0.6, (120, 90, 60), 'box'),          # swallowed wagon
    ]
    for x, y, c in trees:
        m.append((x, y, None, 640, 0.32, c, 'tree'))
    return m


BLOCKOUT_FOV = {'view:arrival': 80.0, 'view:signature': 80.0}
BLOCKOUT_PITCH = {'view:arrival': -1.0, 'view:signature': -4.0}  # negative looks down

ANNOTATIONS = {
    'view:arrival': [
        ('Sphinx Wells (palms, tavern, stables)', 61.5, 59, 600),
        ('Northern Sphinx in the dunes', 82.5, 39, 1700),
        ('red mesas', 68, 37, 400),
        ('Castle Basenji on its cliff', 38.5, 31, 1600),
        ('obelisk knoll', 75, 51, 900),
    ],
    'view:signature': [
        ('dunes pour over the rim', 25, 86, 0),
        ('stars below the rim', 20, 82, -1200),
        ('Southern Sphinx (half buried)', 36, 84.5, 1000),
        ("Saul's hermitage", 30, 70, 400),
        ('Castle Basenji, far', 38.5, 31, 1600),
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
NOT_POI = ('poi:arie', 'poi:saul', 'poi:summer_druid')   # NPC actors: places for the 6,000 rule, not POIs
POI_ENTRANCES = ('entrance:xd14_gate', 'entrance:xd15_door', 'entrance:xd20_gate', 'entrance:fd02_door',
                 'entrance:yard_gate')
DIF_MIX = {0: (1, 0, 0), 1: (0.9, 0.08, 0.02), 2: (0.7, 0.2, 0.1), 3: (0.5, 0.3, 0.2), 4: (0.3, 0.4, 0.3),
           5: (0.1, 0.5, 0.4)}   # tools/xeen/balance.py
LEVELS = {'Xeen Sand Worm': (30, 38, 45), 'Xeen Werewolf': (20, 30, 40), 'Xeen Elemental Golem': (22, 28, 50)}


def census(plan, sketch):
    spots = []      # (label, x, y) in cells, centred
    for p in sketch['points']:
        pid = p['id']
        if pid.startswith('poi:') and pid not in NOT_POI or pid in POI_ENTRANCES:
            spots.append((pid + (f'#{p["index"]}' if 'index' in p else ''), p['at'][0] + 0.5, p['at'][1] + 0.5))
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


def figures_for(plan, sketch, project, height, water, rim):
    x0, y0, x1, y1 = PLAY
    land = np.zeros((N, N), bool)
    land[y0:y1, x0:x1] = True
    hc = height[RES // 2::RES, RES // 2::RES]
    wc = water[RES // 2::RES, RES // 2::RES]
    box = land & (hc > 1)
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
    plots = plot_list(plan, sketch)
    town_doors = [p[2] for p in plots]

    def first_fight(at):
        x, y = at[0] + 0.5, at[1] + 0.5
        return int(round(min(poly_dist(p, x, y) for p in fights) * 512, -2))

    def nearest_fight_to(doors):
        best = min(min(poly_dist(p, dx_, dy_) for p in fights) for dx_, dy_ in doors)
        return int(round(best * 512, -2))
    edge = {k: first_fight(pts_[k]) for k in ['entrance:east_road', 'entrance:south_road']}
    town_arr = {k: first_fight(pts_[k]) for k in ['entrance:sphinx_wells', 'entrance:warzone_coach']}
    hamlet_doors = [p[2] for p in plots if p[0].startswith('building:x6_')]
    yard = [p[2] for p in plots if p[0] == 'building:warzone_coach'] + [
        (pts_[k][0] + 0.5, pts_[k][1] + 0.5) for k in ('entrance:yard_gate', 'entrance:xd20_gate')]
    buffers = {'Sphinx Wells doors': nearest_fight_to(hamlet_doors),
               'coach yard (house, both gates)': nearest_fight_to(yard),
               'Arie': first_fight(pts_['poi:arie']), 'Saul': first_fight(pts_['poi:saul']),
               'Summer Druid': first_fight(pts_['poi:summer_druid'])}
    comps = census(plan, sketch)
    # places for the 6,000 rule: every point on land (POIs, NPCs, entrances, junctions, landmarks), every door,
    # every encounter area, the towns
    seed = np.zeros((N, N), bool)
    for p in sketch['points']:
        x, y = p['at']
        if 0 <= x < N and 0 <= y < N and not rim[int((y + .5) * RES), int((x + .5) * RES)]:
            seed[int(y), int(x)] = True
    for dx_, dy_ in town_doors:
        seed[int(dy_), int(dx_)] = True
    seed |= enc
    for d in sketch['districts']:
        if d['space'].startswith('town:') or d['space'] == 'zone:coach_yard':
            seed |= poly_mask(d['polygon'], scale=1)
    dist = ndimage.distance_transform_edt(~seed) * 512
    far = float(((dist > 3000) & land).sum() / n_land)
    farthest = int(round(dist[land].max(), -2))
    fy, fx = np.unravel_index(np.argmax(np.where(land, dist, 0)), dist.shape)
    nn = []
    cpts = [c['at'] for c in comps]
    for i, a in enumerate(cpts):
        nn.append(min(math.hypot(a[0] - b[0], a[1] - b[1]) for j, b in enumerate(cpts) if j != i) * 512)
    towns = {}
    poly = next(d['polygon'] for d in sketch['districts'] if d['space'] == 'town:sphinx_wells')
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    cells = (max(xs) - min(xs)) * (max(ys) - min(ys))
    nb = sum(1 for p in plots if p[0].startswith('building:x6_'))
    towns['town:sphinx_wells'] = {'cells': cells, 'extent': [int((max(xs) - min(xs)) * 512),
                                                             int((max(ys) - min(ys)) * 512)],
                                  'buildings': nb, 'per_100': round(100 * nb / cells, 1),
                                  'services': sum(1 for p in plots if p[0].startswith('building:x6_') and p[3])}
    # relief inside the playable square, sampled on the drawn land (water surface included)
    hbox = hc[box]
    pts_h = [p['h'] for p in sketch['heights']['points']]
    inside_pts = [p['h'] for p in sketch['heights']['points']
                  if x0 <= p['at'][0] < x1 and y0 <= p['at'][1] < y1]
    hy_, hx_ = np.unravel_index(np.argmax(np.where(box, hc, 0)), hc.shape)
    ly_, lx_ = np.unravel_index(np.argmin(np.where(box, hc, 1e9)), hc.shape)
    slots = project['map_stats']['slots']
    mean = {i + 1: (s['per_marker'][0] + s['per_marker'][1]) / 2 for i, s in enumerate(slots)}
    marker_hostiles = sum(a['count'] * mean[a['slot']] for a in sketch['areas'] if a.get('kind', 'encounter') ==
                          'encounter')
    xp = lambda L: L * (L + 10)
    kill = 0.0
    per_family = {}
    level_mean = {}
    for a in sketch['areas']:
        if a.get('kind', 'encounter') != 'encounter':
            continue
        s = slots[a['slot'] - 1]
        mix = DIF_MIX[s['tier']]
        lv = LEVELS[s['monster']]
        v = a['count'] * mean[a['slot']] * sum(w * xp(L) for w, L in zip(mix, lv))
        kill += v
        per_family[s['monster']] = per_family.get(s['monster'], 0) + v
        level_mean[s['monster']] = round(sum(w * L for w, L in zip(mix, lv)), 1)
    pois = plan['points_of_interest']
    chests = [p['id'] for p in pois if p['kind'] == 'chest']
    return {
        'land_cells': n_land,
        'quiet_share': round(quiet, 3),
        'areas': areas,
        'markers': sum(a['count'] for a in sketch['areas'] if a.get('kind', 'encounter') == 'encounter'),
        'hostiles_markers': marker_hostiles,
        'hostiles_placed': 0,
        'hostiles': marker_hostiles,
        'kill_xp_member': round(kill / 4 / 1000, 1),
        'kill_xp_by_family_member': {k: round(v / 4 / 1000, 1) for k, v in per_family.items()},
        'mean_level_by_family': level_mean,
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
        'entrances': 4,
        'height_range_points': [min(pts_h), max(pts_h)],
        'height_range_points_inside': [min(inside_pts), max(inside_pts)],
        'height_box_field': [int(round(float(hbox.min()), -1)), int(round(float(hbox.max()), -1))],
        'height_box_span': int(round(float(hbox.max() - hbox.min()), -1)),
        'height_box_low_at': [int(lx_), int(ly_)],
        'height_box_high_at': [int(hx_), int(hy_)],
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
    (OUT / 'plan_x6.svg').write_text(svg)
    chrome(OUT / 'plan_x6.svg', OUT / 'plan_x6.png')
    chrome(OUT / 'plan_x6.svg', OUT / 'plan_x6_2x.png', scale=2)
    models = models_for(sketch, plan, trees)
    for view in sketch.get('views', []):
        name = view['id'].split(':')[1]
        blockout(height, bare, view, models, OUT / f'blockout_{name}.png', annotations=ANNOTATIONS.get(view['id']),
                 fov=BLOCKOUT_FOV.get(view['id'], 80.0))
    print(json.dumps({k: v for k, v in figures.items() if k not in ('areas', 'chest_ids', 'poi_components')},
                     indent=1))


if __name__ == '__main__':
    main()
