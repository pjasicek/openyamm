#!/usr/bin/env python3
"""X4's MU-3 drawing, MU-4 blockouts and measured figures, from the L1 brief (A5, 2026-11-20).

    render_x4.py        reads devdocs/xeen/briefs/x4/L1/{plan,sketch,project}.yml

Writes into output/studio_cal/x4/mockups/:
  height.npy, colour.png     the land the sketch implies (for the drawings only; the studio builds its own)
  plan_x4.svg, plan_x4.png   the to-scale plan (PNG through headless Chrome)
  blockout_<view>.png        a crude perspective of each sketch view (Codex's composition reference)
  figures.json               the measured figures for the board and the NOTES

Nothing here is read by the game or the studio. Structure after A6's level_generation/xeen_art/phase2/plan_render.py
(not imported: its land code is X5's).
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
BRIEF = ROOT / 'devdocs/xeen/briefs/x4/L1'
OUT = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x4') / 'mockups'
RES = 6
N = 128
PLAY = (19, 19, 109, 109)
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)

BAND_BASE = {'band:rim_sea': 0, 'band:low': 980, 'band:mid': 1300, 'band:high': 1750, 'band:peaks': 2300}
GROUND = {  # sRGB per space, painted in this order over the default savannah
    'zone:west_downs': (186, 166, 110),
    'zone:uplands': (172, 160, 104),
    'zone:castle_fields': (150, 156, 88),
    'zone:south_fields': (196, 176, 108),
    'zone:east_savannah': (176, 166, 98),
    'zone:red_hills': (164, 94, 64),
    'zone:lava_fields': (56, 48, 48),
    'zone:gargoyle_range': (132, 128, 124),
    'town:burlock': (170, 150, 120),
    'town:burlock_castle': (176, 168, 150),
    'town:asp': (150, 140, 110),
    'zone:lists': (160, 150, 92),
    'zone:druid_grove': (150, 120, 70),
}
TREES = {  # space: (trees per cell, colour)
    'zone:south_fields': (0.06, (70, 92, 40)),
    'zone:west_downs': (0.05, (78, 92, 44)),
    'zone:uplands': (0.04, (70, 88, 44)),
    'zone:castle_fields': (0.07, (56, 90, 40)),
    'zone:east_savannah': (0.08, (62, 92, 42)),
    'zone:red_hills': (0.03, (80, 80, 40)),
    'zone:druid_grove': (0.9, (196, 92, 30)),
}
TOWN_LEVEL = {'town:burlock': 1300, 'town:burlock_castle': 1900, 'town:asp': 1050, 'zone:lists': 1050,
              'zone:nystor_landing': 760, 'zone:carlawna_yard': 1350, 'zone:falagar_yard': 1400}


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


def build_land(sketch):
    size = N * RES
    height = np.full((size, size), 1000.0)
    for band in sketch['heights']['bands']:
        if band['band'] != 'band:rim_sea':
            height[poly_mask(band['polygon'])] = BAND_BASE[band['band']]
    height = ndimage.gaussian_filter(height, 4 * RES)
    yy, xx = np.mgrid[0:size, 0:size] / RES
    for point in sketch['heights'].get('points', []):
        px, py = point['at']
        r = 7.0 if point['h'] > 2600 else 4.0
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
    height += np.where(calm, 0, noise * 220 + rough * (40 + 300 * steep))
    for space, level in TOWN_LEVEL.items():
        if space in masks:
            soft = ndimage.gaussian_filter(masks[space].astype(float), RES)
            height = height * (1 - soft) + level * soft
    water = np.zeros((size, size), bool)
    for river in sketch.get('water', {}).get('rivers', []):
        m = line_mask(river['line'], river.get('width_cells', 3))
        dist = ndimage.distance_transform_edt(~m) / RES
        level = river.get('level', 650)
        valley = level + 60 + dist * 110
        height = np.minimum(height, np.where(dist < 9, valley, height))
        height[m] = level
        water |= m
    for body in sketch.get('water', {}).get('bodies', []):
        if body['id'] == 'water:rim_sea':
            continue
        m = poly_mask(body['polygon'])
        height[m] = body['level']
        water |= m
    rim = poly_mask([[0, 0], [128, 0], [128, 24], [0, 24]])
    height[rim] = 0
    return height, water, rim


def colour_land(sketch, height, water, rim):
    size = N * RES
    rgb = np.zeros((size, size, 3))
    rgb[:] = (190, 172, 106)
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
    rock = np.maximum(rock, np.clip((height - 2600) / 600, 0, 0.7))
    rgb = rgb * (1 - rock[..., None]) + np.array((122, 116, 112)) * rock[..., None]
    # greener river banks
    dist = ndimage.distance_transform_edt(~water) / RES
    bank = np.clip(1 - dist / 2.5, 0, 1)[..., None] * (~water)[..., None] * 0.55
    rgb = rgb * (1 - bank) + np.array((96, 128, 60)) * bank
    # lava: glowing cracks
    if 'zone:lava_fields' in masks:
        lava = masks['zone:lava_fields']
        cracks = ndimage.gaussian_filter(np.random.default_rng(13).normal(size=(size, size)), 0.8 * RES)
        glow = lava & (np.abs(cracks) < 0.006)
        rgb[glow] = (214, 92, 26)
    rgb[water] = (52, 96, 120)
    light = np.array([-0.55, -0.65, 0.52])
    nx, ny = -gx * 2.2, -gy * 2.2
    nz = np.ones_like(nx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    shade = (nx * light[0] + ny * light[1] + nz * light[2]) / norm
    shade = np.clip(0.55 + 0.6 * shade, 0.35, 1.15)
    rgb = rgb * shade[..., None]
    rgb[water] = rgb[water] * 0.5 + np.array((52, 96, 120)) * 0.5
    stars = np.zeros((size, size, 3))
    stars[:] = (10, 12, 26)
    rng = np.random.default_rng(3)
    for y, x in rng.integers(0, size, size=(2400, 2)):
        stars[y, x] = rng.integers(140, 255)
    rgb[rim] = stars[rim]
    cliff = ndimage.binary_dilation(~rim, iterations=int(1.0 * RES)) & rim
    rgb[cliff] = (96, 92, 104)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    bare = img.copy()
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    trees = []
    for space, (density, colour) in TREES.items():
        if space not in masks:
            continue
        ys, xs = np.nonzero(masks[space][::RES, ::RES])
        for cy, cx in zip(ys, xs):
            for _ in range(rng.poisson(density * 2)):
                x = (cx + rng.random()) * RES
                y = (cy + rng.random()) * RES
                hy, hx = int(min(y, size - 1)), int(min(x, size - 1))
                if water[hy, hx] or rim[hy, hx] or height[hy, hx] > 2300 or slope[hy, hx] > 0.6:
                    continue
                s = RES * (0.35 + 0.2 * rng.random())
                draw.ellipse((x - s, y - s * 0.8, x + s, y + s * 0.8), fill=colour)
                trees.append((x / RES, y / RES, colour))
    return img, trees, bare


# ---------------------------------------------------------------- labels

KINDS = {
    'entrance:x2_road': 'arrival', 'entrance:x3_road': 'arrival', 'entrance:west_road': 'arrival',
    'entrance:east_road': 'arrival', 'entrance:burlock_square': 'town_arrival',
    'entrance:burlock_stables': 'town_arrival', 'entrance:asp_travel_pit': 'town_arrival',
    'entrance:asp_square': 'town_arrival', 'entrance:river_landing': 'town_arrival',
    'entrance:xd07_gate': 'dungeon', 'entrance:xd25_stair': 'dungeon', 'entrance:xd26_eyrie': 'dungeon',
    'entrance:xd02_adit': 'dungeon', 'entrance:xd26_sky_crack': 'special', 'entrance:throne_landing': 'special',
    'poi:saddlebags': 'chest', 'poi:champions_barrow': 'chest', 'poi:sunken_barge': 'chest', 'poi:ore_cart': 'chest',
    'poi:burned_caravan': 'chest', 'poi:gargoyle_roost': 'chest',
    'poi:barbarian_camp': 'camp', 'poi:ogre_camp': 'camp', 'poi:knights_camp': 'camp',
    'poi:carlawna': 'npc', 'poi:falagar': 'npc', 'poi:joe_caravan': 'npc', 'poi:autumn_druid': 'npc',
    'poi:adam_eve': 'npc', 'poi:signposts': 'sign', 'poi:pedestals': 'pedestal',
    'landmark:castle_burlock': 'landmark', 'landmark:gargoyle_peak': 'landmark', 'landmark:falls': 'landmark',
    'landmark:lava_fields': 'landmark', 'landmark:red_hills': 'landmark', 'landmark:kings_beacon': 'landmark',
}
for j in ['junction:burlock_cross', 'junction:east_fork', 'junction:landing_fork', 'junction:west_fork',
          'junction:asp_gate']:
    KINDS[j] = 'junction'

# id: (text, dx px, dy px, anchor); None hides the label
NAMES = {
    'entrance:x2_road': ('from X2 Rivercity (main arrival)', 12, 20, 'start'),
    'entrance:x3_road': ('from X3 Lifeforce Lagoon', 12, 20, 'start'),
    'entrance:west_road': ('from X6 Desert', 4, -16, 'start'),
    'entrance:east_road': ('from X7 Firestone', -4, -14, 'end'),
    'entrance:burlock_square': None,
    'entrance:burlock_stables': None,
    'entrance:asp_travel_pit': ('Travel Pit', 12, -6, 'start'),
    'entrance:asp_square': None,
    'entrance:river_landing': None,
    'entrance:xd07_gate': ('XD-07 Castle Burlock gate', 12, 4, 'start'),
    'entrance:throne_landing': ('throne fall lands here (+1,000)', -12, 4, 'end'),
    'entrance:xd25_stair': ('XD-25 Undercroft stair', 12, -16, 'start'),
    'entrance:xd26_eyrie': ('XD-26 Gargoyle Eyrie', 12, 4, 'start'),
    'entrance:xd26_sky_crack': ('XD-26 sky-crack ledge (3,300)', 12, -6, 'start'),
    'entrance:xd02_adit': ("XD-02 Red Dwarf Mines' west adit", 12, -8, 'start'),
    'junction:burlock_cross': ('Burlock Cross', -12, 18, 'end'),
    'junction:east_fork': ('East fork', 12, 18, 'start'),
    'junction:landing_fork': ('Landing fork', 12, 4, 'start'),
    'junction:west_fork': ('West fork', -10, 16, 'end'),
    'junction:asp_gate': None,
    'poi:obelisk': ('Obelisk', 12, 4, 'start'),
    'poi:well_might': None,
    'poi:burlock_mirror': None,
    'poi:olympian_fountain': ('Olympian Fountain (+2 Might)', 12, 18, 'start'),
    'poi:jousting_lists': ('Jousting lists (stat challenge)', 40, 6, 'start'),
    'poi:carlawna': ("Carlawna's hut", 12, 4, 'start'),
    'poi:falagar': ("Falagar's hut", 12, 4, 'start'),
    'poi:joe_caravan': ("Joe the Merchant's caravan", 12, 4, 'start'),
    'poi:barbarian_camp': ('Barbarian camp (burn)', -12, -8, 'end'),
    'poi:nystor_landing': ("Nystor's landing", -12, 4, 'end'),
    'poi:autumn_druid': ("Autumn Druid's grove", 0, 26, 'middle'),
    'poi:asp_well': None,
    'poi:rule_stone': None,
    'poi:adam_eve': None,
    'poi:asp_mirror': None,
    'poi:king_statue': None,
    'poi:shrine_fire': ('Shrine of Fire', 12, 4, 'start'),
    'poi:rim_lookout': ('Rim lookout', -12, 4, 'end'),
    'poi:quintain_field': ('Quintain field', 12, 4, 'start'),
    'poi:herders_well': ("Herders' well", 12, 4, 'start'),
    'poi:wayfarers_well': ("Wayfarers' well", 0, -12, 'middle'),
    'poi:dwarf_stone': ('Dwarf boundary stone', -12, 4, 'end'),
    'poi:asp_cemetery': ("Asp's old cemetery", 12, 4, 'start'),
    'poi:ogre_camp': ("Ogres' camp (burn)", 12, 4, 'start'),
    'poi:knights_camp': ("Renegade knights' camp (burn)", 12, 4, 'start'),
    'poi:gargoyle_roost': ('Gargoyle roost', 12, 4, 'start'),
    'poi:saddlebags': ("Fallen jouster's saddlebags", -12, 4, 'end'),
    'poi:champions_barrow': ("Champions' barrow", 12, 4, 'start'),
    'poi:sunken_barge': ('Barge on a sandbar', -12, 4, 'end'),
    'poi:ore_cart': ('Ore cart', 12, 16, 'start'),
    'poi:burned_caravan': ('Burned caravan', -12, 4, 'end'),
    'poi:mill_ruin': ('Burnt mill', 12, 4, 'start'),
    'landmark:kings_beacon': ("King's beacon", 12, 4, 'start'),
    'landmark:castle_burlock': ('CASTLE BURLOCK', 0, -32, 'middle'),
    'landmark:gargoyle_peak': ('Gargoyle Peak 3,900', 0, -14, 'middle'),
    'landmark:falls': ('the falls', 12, -4, 'start'),
    'landmark:lava_fields': None,
    'landmark:red_hills': None,
    'poi:signposts': None,
    'poi:pedestals': None,
}
AREA_CAPTION = {'pop:range_west': (30, 38), 'pop:range_east': (100, 41.5), 'pop:red_hills': (100, 82.5),
                'pop:south_fields': (68, 97.5), 'pop:west_downs': (25, 89), 'pop:pair_river_road': (91, 92), 'pop:pair_firestone_road': (94, 77),
                'pop:pair_west_ogres': (41.5, 61), 'pop:pair_west_knights': (53.5, 69)}
ENC_COLOURS = {1: '#c0282d', 2: '#d06a12', 3: '#7b3fa0'}
FAMILY = {1: 'Burlock knights', 2: 'Ogres', 3: 'Gargoyles'}
CAPTIONS = [
    ('THE GARGOYLE RANGE', (40, 27.3), 17, '#f0f0f0'),
    ('LAVA FIELDS', (115, 36), 15, '#ffb070'),
    ('RED DWARF HILLS', (116, 112), 15, '#5a1a08'),
    ('ASP (cursed)', (42.5, 78), 15, '#222'),
    ('the village', (62, 63.4), 12, '#222'),
    ('the jousting fields', (60, 112), 15, '#5a3a08'),
    ('the west downs', (24, 104), 14, '#4a3a10'),
    ('the range foot', (31, 58), 13, '#3a3a10'),
    ('river meadows', (92, 60), 13, '#2a3a10'),
    ('Great River', (84, 118), 13, '#123a5a'),
    ("King's Bridge", (80.5, 74), 12, '#222'),
    ('the world rim: a cliff above the stars', (64, 22.6), 14, '#ccd'),
]


def esc(text):
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def pts(points, s, off=(0, 0)):
    return ' '.join(f'{(x + off[0]) * s:.1f},{(y + off[1]) * s:.1f}' for x, y in points)


def rect_of(at, fp, facing):
    front, depth = fp
    wx, wy = (front, depth) if facing in 'ns' else (depth, front)
    return at[0], at[1], wx, wy


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
    # the 512 grid (every cell, faint) and 4,096 cells (every 8, stronger)
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
    # areas
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
    # roads
    for road in sketch.get('roads', []):
        lane = road.get('width') == 'lane'
        w = 3 if lane else 6
        o.append(f'<polyline points="{pts(road["line"], scale)}" fill="none" stroke="#3b2a1a" stroke-width="{w + 2}" '
                 'stroke-opacity="0.6" stroke-linecap="round" stroke-linejoin="round"/>')
        dash = ' stroke-dasharray="7 4"' if lane else ''
        o.append(f'<polyline points="{pts(road["line"], scale)}" fill="none" '
                 f'stroke="{"#e6d6a8" if lane else "#d2a868"}" stroke-width="{w}" stroke-linecap="round" '
                 f'stroke-linejoin="round"{dash}/>')
    # the King's Bridge
    o.append(f'<rect x="{78 * scale}" y="{75.6 * scale}" width="{6 * scale}" height="{0.9 * scale}" fill="#cfc6b4" '
             'stroke="#2a1a10" stroke-width="1.2"/>')
    # castle and walls (drawn, not plots)
    o.append(f'<rect x="{56.5 * scale}" y="{43.5 * scale}" width="{11 * scale}" height="{6 * scale}" fill="#e8dcc0" '
             'stroke="#3a2a1a" stroke-width="2"/>')
    o.append(f'<rect x="{60 * scale}" y="{44.5 * scale}" width="{4 * scale}" height="{3 * scale}" fill="#c9b994" '
             'stroke="#3a2a1a" stroke-width="1.5"/>')
    for tx, ty in [(56.5, 43.5), (67.5, 43.5), (56.5, 49.5), (67.5, 49.5)]:
        o.append(f'<circle cx="{tx * scale}" cy="{ty * scale}" r="{0.9 * scale}" fill="#5a6470" stroke="#222" '
                 'stroke-width="1.5"/>')
    o.append(f'<polygon points="{pts([[55, 50], [69, 50], [69, 62], [55, 62]], scale)}" fill="none" '
             'stroke="#6a6a72" stroke-width="3"/>')
    # lists
    o.append(f'<line x1="{69.5 * scale}" y1="{64 * scale}" x2="{69.5 * scale}" y2="{71.5 * scale}" '
             'stroke="#6b3a1a" stroke-width="3"/>')
    o.append(f'<rect x="{72.3 * scale}" y="{64.5 * scale}" width="{1.2 * scale}" height="{6 * scale}" '
             'fill="#7a3b5a" stroke="#222" stroke-width="1"/>')
    # plots
    buildings = {}
    for space in plan['spaces']:
        for b in space.get('buildings', []) or []:
            buildings[b['id']] = b
    for d in sketch.get('districts', []):
        for plot in d.get('plots', []) or []:
            b = buildings[plot['building']]
            fp = b['footprint_cells'][(plot.get('index') or 1) - 1]
            x, y, wx, wy = rect_of(plot['at'], fp, plot['facing'])
            service = b['service'] != 'residence'
            fill = '#7a3a26' if service else '#9a7a5a'
            o.append(f'<rect x="{x * scale:.1f}" y="{y * scale:.1f}" width="{wx * scale:.1f}" height="{wy * scale:.1f}" '
                     f'fill="{fill}" stroke="#2a1a10" stroke-width="1.2"/>')
            cx, cy = (x + wx / 2) * scale, (y + wy / 2) * scale
            tx, ty = {'n': (cx, y * scale), 's': (cx, (y + wy) * scale), 'e': ((x + wx) * scale, cy),
                      'w': (x * scale, cy)}[plot['facing']]
            o.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="2.8" fill="#ffd34d" stroke="#2a1a10" stroke-width="0.8"/>')
    # cameras
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
        dx, dy = (-14, -14) if 'arrival' in view['id'] else (14, 24)
        o.append(f'<text x="{(x + .5) * scale + dx}" y="{(y + .5) * scale + dy}" font-size="13" font-weight="bold" '
                 f'text-anchor="{"end" if dx < 0 else "start"}" fill="#0d3f80" stroke="#fff" stroke-width="3.2" '
                 f'paint-order="stroke">{name}</text>')
    # placed hostiles
    for actor in sketch.get('actors', []):
        x, y = actor['at']
        o.append(f'<circle cx="{(x + .5) * scale}" cy="{(y + .5) * scale}" r="{3 + actor["count"]}" fill="#b00" '
                 'fill-opacity="0.75" stroke="#fff" stroke-width="1"/>')
    # points
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
        elif kind == 'dungeon':
            o.append(f'<rect x="{cx - 7}" y="{cy - 7}" width="14" height="14" fill="#111" stroke="#fff" '
                     'stroke-width="2"/>')
        elif kind == 'special':
            o.append(f'<polygon points="{cx},{cy - 9} {cx + 9},{cy} {cx},{cy + 9} {cx - 9},{cy}" fill="#1f6fd1" '
                     'stroke="#fff" stroke-width="2"/>')
        elif kind == 'chest':
            o.append(f'<polygon points="{cx},{cy - 8} {cx + 8},{cy} {cx},{cy + 8} {cx - 8},{cy}" fill="#d8a010" '
                     'stroke="#222" stroke-width="1.5"/>')
        elif kind == 'camp':
            o.append(f'<polygon points="{cx},{cy - 9} {cx + 8},{cy + 7} {cx - 8},{cy + 7}" fill="#b1361e" '
                     'stroke="#fff" stroke-width="1.5"/>')
        elif kind == 'npc':
            o.append(f'<circle cx="{cx}" cy="{cy}" r="5.5" fill="#1d5fa8" stroke="#fff" stroke-width="1.5"/>')
        elif kind == 'pedestal':
            red = (point.get('index', 1) % 2) == 1
            o.append(f'<circle cx="{cx}" cy="{cy}" r="3.6" fill="{"#d22" if red else "#25c"}" stroke="#fff" '
                     'stroke-width="1"/>')
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
    # call-outs for the dense places
    callouts = [
        ((42, 86.5), (20, 116.5), "Asp's well: 8 pedestals (red/blue), rule stone by the XD-25 stair, Adam and Eve"),
        ((62, 56), (100, 14.5), ''),
    ]
    for (ax, ay), (tx, ty), text in callouts[:1]:
        o.append(f'<line x1="{ax * scale}" y1="{ay * scale}" x2="{(tx + 1) * scale}" y2="{(ty - 1) * scale}" '
                 'stroke="#222" stroke-width="1.2"/>')
        o.append(f'<text x="{tx * scale}" y="{ty * scale}" font-size="13" fill="#111" stroke="#fff" '
                 f'stroke-width="3.2" paint-order="stroke">{esc(text)}</text>')
    o.append(f'<line x1="{62 * scale}" y1="{56 * scale}" x2="{76 * scale}" y2="{56.5 * scale}" stroke="#222" '
             'stroke-width="1.2"/>')
    o.append(f'<text x="{76.3 * scale}" y="{57 * scale}" font-size="13" fill="#111" stroke="#fff" stroke-width="3.2" '
             'paint-order="stroke">village square: mirror, Well of Might</text>')
    # captions
    for text, (x, y), size_t, colour_t in CAPTIONS:
        o.append(f'<text x="{x * scale}" y="{y * scale}" font-size="{size_t}" font-style="italic" font-weight="bold" '
                 f'text-anchor="middle" fill="{colour_t}" stroke="#000" stroke-width="0.6" stroke-opacity="0.35">'
                 f'{esc(text)}</text>')
    # encounter captions (two lines) at chosen spots
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
    # title, legend and scale bar in the band north of the rim
    o.append('<text x="12" y="34" font-size="30" font-weight="bold" fill="#fff">X4 Burlock Savannah: MU-3 plan</text>')
    o.append('<text x="12" y="60" font-size="15" fill="#ccc">To scale on the 128 x 128 grid (one cell 512 units). '
             'North up. A5, 2026-11-20, gate G1.</text>')
    bx, by = 14, 96
    o.append(f'<rect x="{bx - 4}" y="{by - 18}" width="{10 * scale + 220}" height="30" fill="#000" fill-opacity="0.5"/>')
    for i in range(10):
        o.append(f'<rect x="{bx + i * scale}" y="{by - 6}" width="{scale}" height="8" '
                 f'fill="{"#fff" if i % 2 == 0 else "#333"}" stroke="#fff" stroke-width="0.6"/>')
    o.append(f'<text x="{bx + 10 * scale + 10}" y="{by + 3}" font-size="14" fill="#fff">5,120 units (10 cells of '
             '512)</text>')
    # legend below the map
    ly = size + 26
    items = [
        ('sq', '#0b6b3a', 'edge arrival (arrow: facing)'), ('sqs', '#2fa860', 'town / boat arrival'),
        ('sq', '#111', 'dungeon entrance'), ('dia', '#1f6fd1', 'fall / one-way landing'),
        ('dia', '#d8a010', 'chest with a reason'), ('tri', '#b1361e', 'camp to burn'),
        ('dot', '#1d5fa8', 'NPC outdoors'), ('dot', '#8a1f7a', 'device / place'),
        ('star', '#e07000', 'landmark'), ('dot', '#b00', 'placed hostiles (size: count)'),
        ('enc', '#c0282d', 'encounter: knights'), ('enc', '#d06a12', 'encounter: ogres'),
        ('enc', '#7b3fa0', 'encounter: gargoyles'), ('quiet', '#2e8b57', 'keep clear / quiet by design'),
        ('road', '#d2a868', 'road'), ('lane', '#e6d6a8', 'lane / path'),
        ('cam', '#1f6fd1', 'MU-4 camera and sight line'), ('plot', '#7a3a26', 'service (door dot)'),
        ('plot', '#9a7a5a', 'residence'),
    ]
    cols = 5
    for i, (shape, col, text) in enumerate(items):
        x = 10 + (i % cols) * 306
        y = ly + (i // cols) * 28
        if shape in ('sq', 'sqs', 'plot'):
            s = 14 if shape == 'sq' else 10
            o.append(f'<rect x="{x}" y="{y - s / 2}" width="{s}" height="{s}" fill="{col}" stroke="#fff"/>')
        elif shape == 'dia':
            o.append(f'<polygon points="{x + 7},{y - 8} {x + 15},{y} {x + 7},{y + 8} {x - 1},{y}" fill="{col}" '
                     'stroke="#fff"/>')
        elif shape == 'tri':
            o.append(f'<polygon points="{x + 7},{y - 8} {x + 15},{y + 7} {x - 1},{y + 7}" fill="{col}" stroke="#fff"/>')
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
    o.append(f'<text x="10" y="{ly + 4 * 28 + 4}" font-size="14" fill="#bbb">Unshaded land outside the coloured '
             f'encounter areas is quiet land: {q * 100:.0f} % of the playable land. Dashed white: the playable '
             'bounds; the land and the dressing run on to the map edge.</text>')
    o.append('</svg>')
    return '\n'.join(o)


# ---------------------------------------------------------------- perspective blockout

def blockout(height, colour_img, view, models, out_path, w=1536, h=1024, fov=80.0, annotations=None,
             max_d=48000.0):
    size = height.shape[0]
    col = np.asarray(colour_img.convert('RGB')).astype(float)
    cx, cy = (view['at'][0] + 0.5) * RES, (view['at'][1] + 0.5) * RES
    eye = height[int(cy), int(cx)] + view.get('height', 180)
    lx, ly = (view['look'][0] + 0.5) * RES, (view['look'][1] + 0.5) * RES
    yaw = math.atan2(ly - cy, lx - cx)
    pitch = math.radians(BLOCKOUT_PITCH.get(view['id'], -3.0))
    unit = RES / 512.0
    img = np.zeros((h, w, 3))
    for yy in range(h):
        t = yy / h
        img[yy, :] = (120 + 70 * t, 160 + 50 * t, 210 + 20 * t)
    focal = (w / 2) / math.tan(math.radians(fov / 2))
    horizon = h / 2 + focal * math.tan(pitch)
    zs = np.concatenate([np.arange(60, 2000, 12.0), np.arange(2000, max_d, 40.0)])
    haze = np.array((200, 206, 214))
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
            z = zs[k] * corr
            sy = int(horizon - (hgt - eye) / z * focal)
            if sy < ybuf:
                c = col[iy, ix]
                if hgt <= 1:
                    c = np.array((14, 16, 32))
                fog = min(1.0, (zs[k] / 40000.0) ** 1.5) * 0.7
                c = c * (1 - fog) + haze * fog
                img[max(sy, 0):ybuf, sx] = c
                ybuf = max(sy, 0)
                if ybuf == 0:
                    break
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
        if abs(a) > math.radians(fov / 2 + 5) or d < 200 or (len(m) > 6 and m[6] == 'tree' and d < 2600):
            continue
        z = d * math.cos(a)
        sx = w / 2 + math.tan(a) * focal
        base = height[int(my_), int(mx_)] if m[2] is None else m[2]
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
                          (sx, y0 - (y1 - y0) * 0.25)], fill=(70, 78, 92))
        elif shape == 'roof':
            draw.rectangle((sx - half, y0 + (y1 - y0) * 0.4, sx + half, y1), fill=c)
            draw.polygon([(sx - half * 1.05, y0 + (y1 - y0) * 0.4), (sx + half * 1.05, y0 + (y1 - y0) * 0.4),
                          (sx, y0)], fill=(96, 62, 44))
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
        base = height[int(min(my_, size - 1)), int(min(mx_, size - 1))] + rise
        sy = horizon - (base - eye) / z * focal
        draw.ellipse((sx - 9, sy - 9, sx + 9, sy + 9), outline=(220, 30, 30), width=4)
        draw.text((sx + 12, sy - 12), label, fill=(200, 20, 20), font=FONT)
    out.save(out_path)


def models_for(sketch, plan, trees):
    """Blocks for the blockout: (cell x, cell y, base or None, height, half width cells, colour, shape)."""
    m = [
        (62, 46.5, None, 1200, 2.2, (232, 222, 196), 'box'),      # keep
        (57, 44, None, 1300, 0.9, (226, 216, 190), 'cone'),       # towers
        (67, 44, None, 1300, 0.9, (226, 216, 190), 'cone'),
        (57, 49, None, 1050, 0.9, (226, 216, 190), 'cone'),
        (67, 49, None, 1050, 0.9, (226, 216, 190), 'cone'),
        (62, 49.6, None, 600, 5.5, (214, 204, 180), 'box'),       # curtain wall front
        (62, 49.8, None, 820, 1.2, (220, 210, 186), 'box'),       # gatehouse
        (62, 61.8, None, 220, 7.0, (128, 126, 130), 'box'),       # village south wall
        (73, 67.5, None, 300, 0.6, (120, 70, 90), 'box'),         # stands (east side)
        (67, 63.5, None, 420, 0.5, (190, 60, 50), 'cone'),        # pavilions at the north end
        (72, 63.5, None, 420, 0.5, (60, 80, 170), 'cone'),
        (82, 101, None, 420, 0.7, (120, 90, 64), 'roof'),         # Nystor's boathouse
        (80.5, 101.5, 650, 90, 0.9, (92, 70, 50), 'box'),         # jetty
        (87.5, 87, None, 300, 0.45, (150, 120, 80), 'roof'),      # Joe's wagon
        (100, 61, None, 420, 0.75, (130, 124, 116), 'roof'),      # Falagar
        (40, 53, None, 380, 0.75, (120, 100, 80), 'roof'),        # Carlawna
        (48, 66.5, None, 900, 0.25, (40, 40, 48), 'box'),         # obelisk
        (61, 74.6, None, 450, 0.25, (200, 196, 186), 'box'),      # statue
    ]
    for i in range(8):                                            # the tilt barrier, north-south
        m.append((69.5, 64 + i, None, 90, 0.12, (110, 70, 40), 'box'))
    for d in sketch['districts']:
        for plot in d.get('plots', []) or []:
            x, y = plot['at']
            m.append((x + 0.7, y + 0.7, None, 450, 0.8, (176, 150, 112), 'roof'))
    for x, y, c in trees[::2]:
        m.append((x, y, None, 700, 0.32, c, 'tree'))
    return m


BLOCKOUT_FOV = {'view:arrival': 80.0, 'view:signature': 62.0}
BLOCKOUT_PITCH = {'view:arrival': -9.0, 'view:signature': -1.0}  # negative looks down

ANNOTATIONS = {
    'view:arrival': [
        ("Nystor's landing, jetty", 81, 101, 120),
        ('landing fork, signpost', 85, 99, 300),
        ('river road north', 86, 92, 60),
        ("Joe's caravan", 87.5, 87, 120),
        ('Great River', 79, 90, 20),
        ('red dwarf hills', 104, 92, 200),
        ('Gargoyle Range peaks', 72, 30, 0),
        ('King\'s Bridge', 80, 76, 60),
    ],
    'view:signature': [
        ('Castle Burlock (keep)', 62, 46, 900),
        ('walled village', 62, 57, 400),
        ('jousting lists: tilt barrier', 69.5, 68, 150),
        ('stands', 73, 67.5, 350),
        ('Gargoyle Peak 3,900', 50, 30, 0),
        ('the falls', 80, 41, 200),
        ('Burlock Cross, statue', 61, 74.6, 450),
        ('the river', 80, 66, 30),
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
    quiet = float(((~enc) & land).sum() / n_land)
    # roads
    # roads one cell wide (road tiles), lanes counted apart: length inside the playable land
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
    # arrivals and the first fight
    pts = {p['id']: p['at'] for p in sketch['points'] if 'index' not in p}
    fights = [a['polygon'] for a in sketch['areas'] if a.get('kind', 'encounter') == 'encounter']
    placed = [a['at'] for a in sketch['actors']]

    def first_fight(at):
        x, y = at[0] + 0.5, at[1] + 0.5
        d = min([poly_dist(p, x, y) for p in fights] + [math.hypot(x - a[0] - .5, y - a[1] - .5) for a in placed])
        return int(round(d * 512, -2))
    arrivals = {k: first_fight(pts[k]) for k in ['entrance:x2_road', 'entrance:x3_road', 'entrance:west_road',
                                                 'entrance:east_road', 'entrance:burlock_stables',
                                                 'entrance:asp_travel_pit', 'entrance:river_landing']}
    # places: POIs and entrances, and the fights
    places = [p['at'] for p in sketch['points'] if p['id'].split(':')[0] in ('poi', 'entrance', 'landmark',
                                                                            'junction')]
    seed = np.zeros((N, N), bool)
    for x, y in places:
        seed[int(y), int(x)] = True
    seed |= enc
    for d in sketch['districts']:
        if d['space'].startswith('town:'):
            seed |= poly_mask(d['polygon'], scale=1)
    dist = ndimage.distance_transform_edt(~seed) * 512
    far = float(((dist > 3000) & land).sum() / n_land)
    farthest = int(round(dist[land].max(), -2))
    # POI spacing (outdoor places, not in towns, not signposts)
    poi_pts = [p['at'] for p in sketch['points'] if p['id'].startswith('poi:') and p['id'] not in (
        'poi:pedestals', 'poi:signposts', 'poi:adam_eve', 'poi:rule_stone', 'poi:asp_well', 'poi:asp_mirror',
        'poi:burlock_mirror', 'poi:well_might')]
    nn = []
    for i, a in enumerate(poi_pts):
        nn.append(min(math.hypot(a[0] - b[0], a[1] - b[1]) for j, b in enumerate(poi_pts) if j != i) * 512)
    # towns
    towns = {}
    plots_by = {}
    for d in sketch['districts']:
        if d.get('plots'):
            plots_by[d['space']] = len(d['plots'])
    for space in ['town:burlock', 'town:asp']:
        poly = next(d['polygon'] for d in sketch['districts'] if d['space'] == space)
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        cells = (max(xs) - min(xs)) * (max(ys) - min(ys))
        towns[space] = {'cells': cells, 'extent': [int((max(xs) - min(xs)) * 512), int((max(ys) - min(ys)) * 512)],
                        'buildings': plots_by[space], 'per_100': round(100 * plots_by[space] / cells, 1)}
    hs = [p['h'] for p in sketch['heights']['points']]
    river = min(r.get('level', 650) for r in sketch['water']['rivers'])
    slots = project['map_stats']['slots']
    mean = {i + 1: (s['per_marker'][0] + s['per_marker'][1]) / 2 for i, s in enumerate(slots)}
    marker_hostiles = sum(a['count'] * mean[a['slot']] for a in sketch['areas'] if a.get('kind', 'encounter') ==
                          'encounter')
    placed_n = sum(a['count'] for a in sketch['actors'])
    # kill XP (balance.py's DIF_MIX and XP = L(L+10))
    xp = lambda L: L * (L + 10)
    dif = {0: (1, 0, 0), 1: (0.9, 0.08, 0.02)}
    levels = {1: (14, 20, 26), 2: (18, 22, 30), 3: (16, 22, 28)}
    kill = 0.0
    for a in sketch['areas']:
        if a.get('kind', 'encounter') != 'encounter':
            continue
        s = a['slot']
        mix = dif[slots[s - 1]['tier']]
        kill += a['count'] * mean[s] * sum(w * xp(L) for w, L in zip(mix, levels[s]))
    actor_levels = {'11100': 14, '11101': 20, '11102': 28, '11060': 18, '11061': 22, '11140': 14, '11141': 20}
    kill += sum(a['count'] * xp(actor_levels[a['monster']]) for a in sketch['actors'])
    pois = plan['points_of_interest']
    chests = [p for p in pois if p['kind'] == 'chest'] + [p for p in pois if p['id'] in (
        'poi:barbarian_camp', 'poi:ogre_camp', 'poi:knights_camp', 'poi:asp_cemetery')]
    return {
        'land_cells': n_land,
        'quiet_share': round(quiet, 3),
        'areas': areas,
        'markers': sum(a['count'] for a in sketch['areas'] if a.get('kind', 'encounter') == 'encounter'),
        'hostiles_markers': marker_hostiles,
        'hostiles_placed': placed_n,
        'hostiles': marker_hostiles + placed_n,
        'kill_xp_member': round(kill / 4 / 1000, 1),
        'road_share': round(road_share, 4),
        'lane_share': round(lane_share, 4),
        'first_fight': arrivals,
        'far_share_3000': round(far, 3),
        'farthest_from_place': farthest,
        'poi_nn_median': int(round(float(np.median(nn)), -1)),
        'poi_nn_min': int(round(min(nn), -1)),
        'poi_nn_max': int(round(max(nn), -1)),
        'poi_count': len(pois) - 1 + 5,
        'chests': len(chests),
        'chest_ids': [p['id'] for p in chests],
        'entrances': 4,
        'height_range': [river, max(hs)],
        'height_span': max(hs) - river,
        'land_raster_range': [int(height[~rim].min()), int(height.max())],
        'towns': towns,
    }


def main():
    plan, sketch, project = load()
    OUT.mkdir(parents=True, exist_ok=True)
    height, water, rim = build_land(sketch)
    np.save(OUT / 'height.npy', height)
    img, trees, bare = colour_land(sketch, height, water, rim)
    img.save(OUT / 'colour.png')
    figures = figures_for(plan, sketch, project, height, water, rim)
    (OUT / 'figures.json').write_text(json.dumps(figures, indent=1))
    svg = svg_plan(plan, sketch, img, figures)
    (OUT / 'plan_x4.svg').write_text(svg)
    subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
                    f'--screenshot={OUT / "plan_x4.png"}', '--window-size=1600,1750',
                    f'file://{OUT / "plan_x4.svg"}'], check=True, capture_output=True, timeout=120)
    subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
                    '--force-device-scale-factor=2', f'--screenshot={OUT / "plan_x4_2x.png"}',
                    '--window-size=1600,1750', f'file://{OUT / "plan_x4.svg"}'], check=True, capture_output=True,
                   timeout=120)
    models = models_for(sketch, plan, trees)
    for view in sketch.get('views', []):
        name = view['id'].split(':')[1]
        blockout(height, bare, view, models, OUT / f'blockout_{name}.png', annotations=ANNOTATIONS.get(view['id']),
                 fov=BLOCKOUT_FOV.get(view['id'], 80.0))
    print(json.dumps({k: v for k, v in figures.items() if k not in ('areas', 'chest_ids')}, indent=1))


if __name__ == '__main__':
    main()
