#!/usr/bin/env python3
"""X7's MU-3 drawing, MU-4 blockouts and measured figures, from the L1 brief (A5, 2026-11-20).

    render_x7.py        reads devdocs/xeen/briefs/x7/L1/{plan,sketch,project}.yml

Writes into output/studio_cal/x7/mockups/:
  height.npy, colour.png     the land the sketch implies (for the drawings only; the studio builds its own)
  plan_x7.svg, plan_x7.png   the to-scale plan (PNG through headless Chrome), plan_x7_2x.png for the board's crops
  blockout_<view>.png        a crude perspective of each sketch view (Codex's composition reference)
  figures.json               the measured figures for the board and the NOTES

Nothing here is read by the game or the studio. Adapted from level_generation/projects/xeen/x6/render_x6.py; the POI count is
the D-20 census (chained within 400, dungeon doors in, NPCs, exits and landmarks out). The height range is measured on
the drawn land inside the playable square (D-28), lava surfaces included. Mount Firestone is drawn as a cone with a
crater (the sketch's points round it are the studio's; this drawing only needs the shape).
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
BRIEF = ROOT / 'devdocs/xeen/briefs/x7/L1'
OUT = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x7') / 'mockups'
RES = 6
N = 128
PLAY = (19, 24, 104, 109)     # the playable square [19, 109] cut by the north and east rims (y 24, x 104)
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
FIRESTONE = (88.5, 40.5)      # the crater's centre (cell centre)
CONE_FOOT, CONE_RIM, CRATER_R, CONE_R = 2300.0, 5000.0, 3.0, 15.0

BAND_BASE = {'band:rim_sea': 0, 'band:basin': 1750, 'band:flats': 2150, 'band:volcano': 2500, 'band:range': 2500,
             'band:slopes': 1950}
GROUND = {  # sRGB per space, painted in this order over the default red earth
    'zone:south_slopes': (156, 104, 78),
    'zone:red_dwarf_range': (136, 88, 72),
    'zone:ash_flats': (118, 112, 108),
    'zone:lava_basin': (90, 82, 80),
    'zone:firestone': (66, 60, 60),
    'zone:the_gap': (142, 100, 80),
    'zone:dwarf_watch': (150, 120, 92),
    'zone:sablewing_cave': (150, 104, 80),
    'zone:orc_outpost': (140, 110, 80),
    'zone:lava_island': (60, 50, 48),
}
TREES = {  # space: (trees per cell, [colours]): dry scrub and burnt snags
    'zone:south_slopes': (0.05, [(96, 92, 52), (110, 98, 60)]),
    'zone:dwarf_watch': (0.05, [(96, 92, 52)]),
    'zone:ash_flats': (0.01, [(40, 36, 34)]),
}
TOWN_LEVEL = {'zone:dwarf_watch': 2100, 'zone:sablewing_cave': 2050, 'zone:orc_outpost': 2000, 'zone:the_gap': 2300,
              'zone:volcano_mouth': 2250, 'zone:lava_island': 1560}
LAVA = np.array((236, 96, 24))


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
    pts_ = [(x * scale, y * scale) for x, y in points]
    w = max(1, int(width_cells * scale))
    d.line(pts_, fill=255, width=w, joint='curve')
    for p in pts_:
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


def cone(xx, yy):
    d = np.hypot(xx - FIRESTONE[0], yy - FIRESTONE[1])
    outer = CONE_FOOT + (CONE_RIM - CONE_FOOT) * np.clip(1 - (d - CRATER_R) / (CONE_R - CRATER_R), 0, 1) ** 1.35
    inner = 4600 + 400 * np.clip(d / CRATER_R, 0, 1) ** 2
    return np.where(d < CRATER_R, inner, outer), d


def build_land(sketch):
    size = N * RES
    height = np.full((size, size), 1950.0)
    for band in sketch['heights']['bands']:
        if band['band'] != 'band:rim_sea':
            height[poly_mask(band['polygon'])] = BAND_BASE[band['band']]
    height = ndimage.gaussian_filter(height, 4 * RES)
    yy, xx = np.mgrid[0:size, 0:size] / RES
    for point in sketch['heights'].get('points', []):
        px, py = point['at']
        if math.hypot(px + 0.5 - FIRESTONE[0], py + 0.5 - FIRESTONE[1]) < 13 and point['h'] > 3000:
            continue      # the cone below draws Mount Firestone
        r = 6.0 if point['h'] > 2600 else 3.5
        d = np.hypot(xx - px - 0.5, yy - py - 0.5)
        t = np.clip(1 - d / r, 0, 1)
        w = t * t * (3 - 2 * t)
        height = height * (1 - w) + point['h'] * w
    for ridge in sketch['heights'].get('ridges', []):
        m = line_mask(ridge['line'], ridge.get('width', 2))
        dist = ndimage.distance_transform_edt(~m) / RES
        w = np.clip(1 - dist / (ridge.get('slope', 3) + 2.5), 0, 1)
        height = np.maximum(height, height * (1 - w) + ridge['height'] * w)
    c, cd = cone(xx, yy)
    height = np.where(cd < CONE_R + 2, np.maximum(height, c), height)
    height = np.where(cd < CRATER_R, c, height)
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
    steep = np.clip((height - 2300) / 1200, 0, 1)
    height += np.where(calm, 0, noise * 160 + rough * (30 + 240 * steep))
    for space, level in TOWN_LEVEL.items():
        if space in masks:
            soft = ndimage.gaussian_filter(masks[space].astype(float), RES * 0.6)
            height = height * (1 - soft) + level * soft
    lava = np.zeros((size, size), bool)
    for body in sketch.get('water', {}).get('bodies', []):
        if body['id'] == 'water:rim_sea':
            continue
        m = poly_mask(body['polygon'])
        dist = ndimage.distance_transform_edt(~m) / RES
        height = np.minimum(height, np.where(dist < 3, body['level'] + 40 + dist * 60, height))
        height[m] = body['level']
        lava |= m
    for river in sketch.get('water', {}).get('rivers', []):
        m = line_mask(river['line'], river.get('width_cells', 1.5))
        bed = ndimage.gaussian_filter(ndimage.grey_erosion(height, size=(3 * RES, 3 * RES)), RES) - 60
        soft = np.clip(ndimage.gaussian_filter(m.astype(float), RES * 0.6) * 1.6, 0, 1)
        height = height * (1 - soft) + bed * soft
        lava |= m
    rim = poly_mask(rim_poly(sketch))
    height[rim] = 0
    lava &= ~rim
    return height, lava, rim


def colour_land(sketch, height, lava, rim):
    size = N * RES
    rgb = np.zeros((size, size, 3))
    rgb[:] = (150, 100, 78)
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
    rock = np.maximum(rock, np.clip((height - 2700) / 900, 0, 0.7))
    yy, xx = np.mgrid[0:size, 0:size] / RES
    c, cd = cone(xx, yy)
    black = np.clip(1 - (cd - CONE_R) / 3, 0, 1)
    rgb = rgb * (1 - rock[..., None]) + np.array((92, 70, 64)) * rock[..., None]
    rgb = rgb * (1 - black[..., None] * 0.7) + np.array((48, 44, 46)) * black[..., None] * 0.7
    # ash: a grey dusting over the north, heavier toward Firestone
    north = np.clip((60 - yy) / 20, 0, 1) * 0.35
    rgb = rgb * (1 - north[..., None]) + np.array((128, 124, 122)) * north[..., None]
    light = np.array([-0.55, -0.65, 0.52])
    nx, ny = -gx * 2.2, -gy * 2.2
    nz = np.ones_like(nx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    shade = (nx * light[0] + ny * light[1] + nz * light[2]) / norm
    shade = np.clip(0.6 + 0.55 * shade, 0.38, 1.15)
    rgb = rgb * shade[..., None]
    dist = ndimage.distance_transform_edt(~lava) / RES
    glow = np.clip(1 - dist / 2.0, 0, 1)[..., None] * (~lava)[..., None] * 0.45
    rgb = rgb * (1 - glow) + np.array((200, 70, 20)) * glow
    crust = ndimage.gaussian_filter(np.random.default_rng(9).normal(size=(size, size)), 0.8 * RES)
    crust = np.clip(0.75 + crust / (np.abs(crust).max() + 1e-6) * 0.6, 0.35, 1.1)
    rgb[lava] = (LAVA * crust[..., None])[lava]
    stars = np.zeros((size, size, 3))
    stars[:] = (10, 12, 26)
    rng = np.random.default_rng(3)
    for y, x in rng.integers(0, size, size=(2400, 2)):
        stars[y, x] = rng.integers(140, 255)
    rgb[rim] = stars[rim]
    cliff = ndimage.binary_dilation(~rim, iterations=int(1.0 * RES)) & rim
    rgb[cliff] = (84, 64, 58)
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
                if lava[hy, hx] or rim[hy, hx] or height[hy, hx] > 2600 or slope[hy, hx] > 0.6:
                    continue
                colour = colours[rng.integers(len(colours))]
                s = RES * (0.22 + 0.12 * rng.random())
                draw.ellipse((x - s, y - s * 0.8, x + s, y + s * 0.8), fill=colour)
                trees.append((x / RES, y / RES, colour))
    return img, trees, bare


# ---------------------------------------------------------------- labels

KINDS = {
    'entrance:west_road': 'arrival', 'entrance:south_road': 'arrival',
    'entrance:xd16_mouth': 'dungeon', 'entrance:xd17_cleft': 'dungeon', 'entrance:xd18_mouth': 'dungeon',
    'entrance:fd04_door': 'dungeon', 'entrance:xd05_gate': 'dungeon',
    'poi:watch_chest': 'chest', 'poi:outpost_chest': 'chest', 'poi:orc_den': 'chest', 'poi:miner_cache': 'chest',
    'poi:knight_remains': 'chest', 'poi:dragon_hoard': 'chest', 'poi:hydra_wallow': 'chest',
    'poi:sablewing': 'npc', 'poi:signposts': 'sign',
    'landmark:firestone': 'landmark', 'landmark:lava_falls': 'landmark', 'landmark:dragon_tower': 'landmark',
    'landmark:watch_tower': 'landmark', 'landmark:black_bridge': 'landmark', 'landmark:red_dwarf_range': 'landmark',
}
for _k in ['dragon_skull', 'fallen_cart', 'pony_shed', 'charcoal_pits', 'east_lookout', 'slag_heaps', 'boundary_stone']:
    KINDS['landmark:' + _k] = 'minor'
for j in ['junction:gap', 'junction:lava_fork', 'junction:slope_fork']:
    KINDS[j] = 'junction'

# id: (text, dx px, dy px, anchor); None hides the label
NAMES = {
    'entrance:west_road': ('from X4 Burlock (y 66)', -14, -16, 'end'),
    'entrance:south_road': ('from X1 Vertigo (x 69)', 14, 4, 'start'),
    'entrance:xd16_mouth': ('XD-16 Volcano Cave', 12, -10, 'start'),
    'entrance:xd17_cleft': ("XD-17 Shangri-La's cleft (Q-C26)", 12, 22, 'start'),
    'entrance:xd18_mouth': ('XD-18 Dragon Cave (tax office)', 12, 18, 'start'),
    'entrance:fd04_door': ('FD-04 Dragon Tower (phase 6)', 12, 18, 'start'),
    'entrance:xd05_gate': ("XD-05 Orc Caves' back gate", 12, 4, 'start'),
    'junction:gap': ('the Firestone Gap', -12, 20, 'end'),
    'junction:lava_fork': ('lava fork', -12, 4, 'end'),
    'junction:slope_fork': ('slope fork', -12, 4, 'end'),
    'poi:obelisk': ('Obelisk (SPHINX)', 12, -6, 'start'),
    'poi:shrine_fire': ('Shrine of Fire', -12, 4, 'end'),
    'poi:well_speed': ('Well of Speed (+2 Spd)', 12, 4, 'start'),
    'poi:fire_reflector': ('Fire Reflector (M37)', -12, 22, 'end'),
    'poi:lava_rock': ('Ever-Hot Lava Rock (Q-C14)', 12, 4, 'start'),
    'poi:demon_idols': None,
    'poi:hot_spring': ('hot spring', 12, 4, 'start'),
    'poi:cairn': ('cairn of the unreturned', -12, -8, 'end'),
    'poi:orc_outpost': ('orc outpost (burn)', 12, -8, 'start'),
    'poi:sablewing': ("Sablewing's cave (4720, Dragon Master)", 12, 4, 'start'),
    'poi:watch_chest': None,
    'poi:outpost_chest': None,
    'poi:orc_den': ("orcs' den", 12, 8, 'start'),
    'poi:miner_cache': ("miner's cache", 12, 8, 'start'),
    'poi:knight_remains': ("knight's remains", -12, 4, 'end'),
    'poi:dragon_hoard': ("dragon's hoard", 12, 4, 'start'),
    'poi:hydra_wallow': ("hydras' wallow", 12, 14, 'start'),
    'landmark:firestone': None, 'landmark:lava_falls': None, 'landmark:dragon_tower': None,
    'landmark:watch_tower': None, 'landmark:black_bridge': ('black bridge', -12, -6, 'end'),
    'landmark:red_dwarf_range': None,
    'poi:signposts': None,
}
AREA_CAPTION = {'pop:lava_basin': (24, 56), 'pop:ash_flats': (63, 33.5), 'pop:firestone': (96, 55),
                'pop:west_slopes': (34, 79), 'pop:red_river': (95, 106)}
ENC_COLOURS = {1: '#b8620a', 2: '#2a7a3a', 3: '#c0282d'}
FAMILY = {1: 'Orcs (5-10)', 2: 'Hydras (45-65)', 3: 'Dragons (60-75)'}
CAPTIONS = [
    ('MOUNT FIRESTONE', (88.5, 53.5), 15, '#ffd8b0'),
    ('THE RED DWARF RANGE', (40, 62.6), 15, '#f0d8c8'),
    ('the south slopes', (52, 88), 14, '#3a1a08'),
    ('the ash flats', (66, 58), 13, '#eee'),
    ('the lava lake', (40, 38.5), 13, '#ffe0a0'),
    ('the world rim: a cliff above the stars', (40, 21.5), 14, '#ccd'),
    ('the east rim', (116, 64), 13, '#ccd'),
    ('lava falls into the stars', (73, 15.5), 13, '#ffb070'),
]


def esc(text):
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def pts(points, s, off=(0, 0)):
    return ' '.join(f'{(x + off[0]) * s:.1f},{(y + off[1]) * s:.1f}' for x, y in points)


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
    # the lava falling off the north rim into the stars
    for k in range(5):
        x = 71.5 + k * 0.7
        o.append(f'<path d="M{x * scale},{28 * scale} q{0.4 * scale},{-2 * scale} {0.2 * scale},{-11 * scale}" '
                 f'fill="none" stroke="#ff8a30" stroke-opacity="{0.75 - k * 0.1}" stroke-width="4"/>')
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
        if kind == 'open':
            continue
        if kind == 'keep_clear':
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
    # the crater's rim
    o.append(f'<circle cx="{FIRESTONE[0] * scale}" cy="{FIRESTONE[1] * scale}" r="{CRATER_R * scale}" fill="none" '
             'stroke="#2a2022" stroke-width="5"/>')
    # the Dragon Tower on its crag
    o.append(f'<circle cx="{29.5 * scale}" cy="{29.5 * scale}" r="{1.6 * scale}" fill="#2a2228" stroke="#d8c0a8" '
             'stroke-width="2"/>')
    # the dwarves' watch: a stockade with its tower, gate west
    o.append(f'<polyline points="{pts([[65, 81.4], [65, 80], [70, 80], [70, 85], [65, 85], [65, 82.6]], scale)}" '
             'fill="none" stroke="#5a4028" stroke-width="4"/>')
    o.append(f'<rect x="{65.6 * scale}" y="{80.6 * scale}" width="{1.2 * scale}" height="{1.2 * scale}" '
             'fill="#7a5a3a" stroke="#222" stroke-width="1.5"/>')
    # the black bridge
    o.append(f'<line x1="{61 * scale}" y1="{41.6 * scale}" x2="{61 * scale}" y2="{44.6 * scale}" stroke="#151515" '
             'stroke-width="9" stroke-linecap="round"/>')
    for view in sketch.get('views', []):
        x, y = view['at']
        lx, ly = view['look']
        ang = math.atan2(ly - y, lx - x)
        dist = math.hypot(lx - x, ly - y)
        hf = math.radians(39)
        p1 = (x + math.cos(ang - hf) * dist, y + math.sin(ang - hf) * dist)
        p2 = (x + math.cos(ang + hf) * dist, y + math.sin(ang + hf) * dist)
        col = '#1f6fd1'
        o.append(f'<polygon points="{pts([(x, y), p1, p2], scale, (0.5, 0.5))}" fill="{col}" fill-opacity="0.10" '
                 f'stroke="{col}" stroke-width="1.6" stroke-dasharray="7 4"/>')
        o.append(f'<line x1="{(x + .5) * scale}" y1="{(y + .5) * scale}" x2="{(lx + .5) * scale}" '
                 f'y2="{(ly + .5) * scale}" stroke="{col}" stroke-width="2.4"/>')
        o.append(f'<circle cx="{(x + .5) * scale}" cy="{(y + .5) * scale}" r="8" fill="{col}" stroke="#fff" '
                 'stroke-width="2"/>')
        name = 'camera: arrival' if 'arrival' in view['id'] else 'camera: signature'
        dx, dy = (-12, 30) if 'arrival' in view['id'] else (-12, -12)
        o.append(f'<text x="{(x + .5) * scale + dx}" y="{(y + .5) * scale + dy}" font-size="13" font-weight="bold" '
                 f'text-anchor="end" fill="#0d3f80" stroke="#fff" stroke-width="3.2" '
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
        elif kind == 'dungeon':
            o.append(f'<rect x="{cx - 7}" y="{cy - 7}" width="14" height="14" fill="#111" stroke="#fff" '
                     'stroke-width="2"/>')
        elif kind == 'chest':
            o.append(f'<polygon points="{cx},{cy - 8} {cx + 8},{cy} {cx},{cy + 8} {cx - 8},{cy}" fill="#d8a010" '
                     'stroke="#222" stroke-width="1.5"/>')
        elif kind == 'npc':
            o.append(f'<circle cx="{cx}" cy="{cy}" r="6.5" fill="#1d5fa8" stroke="#fff" stroke-width="1.8"/>')
        elif kind == 'junction':
            o.append(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="#5a4630" stroke="#fff" stroke-width="1.5"/>')
        elif kind == 'sign':
            o.append(f'<rect x="{cx - 2}" y="{cy - 6}" width="4" height="10" fill="#6b4a20"/>')
        elif kind == 'minor':
            o.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="#e0a060" stroke="#222" stroke-width="1.2"/>')
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
    for actor in sketch.get('actors', []):
        if actor['monster'] != '11593':
            continue
        ax, ay = actor['at']
        o.append(f'<circle cx="{ax * scale}" cy="{ay * scale}" r="{max(5, actor.get("spread", 1) * scale)}" '
                 'fill="#ff5a10" fill-opacity="0.25" stroke="#7a1a00" stroke-width="2" stroke-dasharray="3 2"/>')
    callouts = [
        ((67.5, 82.5), (76, 78.6), "the dwarves' watch: stockade, signal tower, pay chest"),
        ((35.5, 46), (2, 31), 'lava golems (8 placed, 55)'),
        ((66.5, 46.5), (40, 50.5), 'demon and devil idols'),
        ((88.5, 40.5), (98, 33.5), 'crater (lava 4,600)'),
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
    o.append(f'<text x="{116 * scale}" y="{8 * scale}" font-size="15" font-weight="bold" text-anchor="middle" '
             'fill="#fff">X7 Mount</text>')
    o.append(f'<text x="{116 * scale}" y="{9.5 * scale}" font-size="15" font-weight="bold" text-anchor="middle" '
             'fill="#fff">Firestone</text>')
    o.append(f'<text x="{116 * scale}" y="{11.2 * scale}" font-size="12" text-anchor="middle" fill="#ccc">MU-3 plan, '
             'A5, 2026-11-20</text>')
    bx, by = 108 * scale, 120 * scale
    for i in range(10):
        o.append(f'<rect x="{bx + i * scale}" y="{by - 6}" width="{scale}" height="8" '
                 f'fill="{"#fff" if i % 2 == 0 else "#333"}" stroke="#fff" stroke-width="0.6"/>')
    o.append(f'<text x="{bx}" y="{by + 20}" font-size="13" fill="#fff">5,120 units (10 cells of 512)</text>')
    ly = size + 26
    items = [
        ('sq', '#0b6b3a', 'edge arrival (arrow: facing)'), ('sq', '#111', 'dungeon entrance (sealed until built)'),
        ('dia', '#d8a010', 'chest with a reason'), ('dot', '#1d5fa8', 'NPC outdoors (not a POI)'),
        ('dot', '#8a1f7a', 'device / place'), ('star', '#e07000', 'landmark'),
        ('enc', '#b8620a', 'encounter: orcs (south)'), ('enc', '#2a7a3a', 'encounter: hydras (north)'),
        ('enc', '#c0282d', 'encounter: dragons (north)'), ('quiet', '#2e8b57', 'keep clear'),
        ('road', '#d2a868', 'road'), ('lane', '#f2e6c4', 'lane / path'),
        ('cam', '#1f6fd1', 'MU-4 camera and sight line'), ('lava', '#ec6018', 'lava (lake, crater, river)'),
        ('golem', '#ff5a10', 'placed lava golems'),
    ]
    cols = 5
    for i, (shape, col, text) in enumerate(items):
        x = 10 + (i % cols) * 306
        y = ly + (i // cols) * 28
        if shape == 'sq':
            o.append(f'<rect x="{x}" y="{y - 7}" width="14" height="14" fill="{col}" stroke="#fff"/>')
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
        elif shape == 'lava':
            o.append(f'<rect x="{x}" y="{y - 7}" width="18" height="14" fill="{col}"/>')
        elif shape == 'golem':
            o.append(f'<circle cx="{x + 8}" cy="{y}" r="7" fill="{col}" fill-opacity="0.3" stroke="#7a1a00" '
                     'stroke-dasharray="3 2"/>')
        o.append(f'<text x="{x + 28}" y="{y + 5}" font-size="14" fill="#e8e8e8">{esc(text)}</text>')
    q = figures['quiet_share']
    o.append(f'<text x="10" y="{ly + 3 * 28 + 4}" font-size="14" fill="#bbb">Land outside the coloured '
             f'areas is quiet: {q * 100:.0f} % of the playable land. Dashed white: the playable bounds; the land runs '
             'on to the west and south edges; north of y 24 and east of x 104, the stars.</text>')
    o.append('</svg>')
    return '\n'.join(o)


# ---------------------------------------------------------------- perspective blockout

def blockout(height, colour_img, view, models, out_path, w=1536, h=1024, fov=80.0, annotations=None,
             max_d=56000.0, lava=None):
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
    # the ashen sky: a dull brown-grey zenith, a ruddy haze at the horizon
    for yy in range(h):
        t = np.clip((yy - (horizon - 560)) / 560, 0, 1)
        img[yy, :] = np.array((96, 92, 98)) * (1 - t) + np.array((196, 160, 136)) * t
    zs = np.concatenate([np.arange(60, 2000, 12.0), np.arange(2000, max_d, 40.0)])
    haze = np.array((180, 150, 132))
    depth = np.full((h, w), np.inf)      # the terrain's distance per pixel: models hide behind it
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
                glow = lava is not None and lava[iy, ix]
                fog = min(1.0, (zs[k] / 40000.0) ** 1.5) * (0.35 if glow else 0.7)
                c = c * (1 - fog) + haze * fog
                img[max(sy, 0):ybuf, sx] = c
                depth[max(sy, 0):ybuf, sx] = zs[k]
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
    order = []
    for m in models:
        mx_, my_ = (m[0] + 0.5) * RES, (m[1] + 0.5) * RES
        order.append((math.hypot(mx_ - cx, my_ - cy) / unit, m))
    for d, m in sorted(order, key=lambda t: -t[0]):
        mx_, my_ = (m[0] + 0.5) * RES, (m[1] + 0.5) * RES
        a = math.atan2(my_ - cy, mx_ - cx) - yaw
        a = (a + math.pi) % (2 * math.pi) - math.pi
        if abs(a) > math.radians(fov / 2 + 5) or d < 200 or (len(m) > 6 and m[6] == 'tree' and d < 3000):
            continue
        z = d * math.cos(a)
        sx = w / 2 + math.tan(a) * focal
        base = height[int(min(my_, size - 1)), int(min(mx_, size - 1))] if m[2] is None else m[2]
        top = base + m[3]
        y0 = horizon - (top - eye) / z * focal
        y1 = horizon - (base - eye) / z * focal
        half = m[4] * 512 / z * focal
        shape = m[6] if len(m) > 6 else 'box'
        fog = min(1.0, (d / 40000.0) ** 1.5) * (0.25 if shape in ('smoke', 'falls') else 0.7)
        c = tuple(int(v * (1 - fog) + f * fog) for v, f in zip(m[5], haze))
        layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        if shape == 'tree':
            draw.rectangle((sx - half * 0.12, (y0 + y1) / 2, sx + half * 0.12, y1), fill=(80, 64, 50))
            draw.ellipse((sx - half, y0, sx + half, y0 + (y1 - y0) * 0.45), fill=c)
        elif shape == 'cone':
            draw.rectangle((sx - half, y0 + (y1 - y0) * 0.3, sx + half, y1), fill=c)
            draw.polygon([(sx - half * 1.2, y0 + (y1 - y0) * 0.3), (sx + half * 1.2, y0 + (y1 - y0) * 0.3),
                          (sx, y0 - (y1 - y0) * 0.25)], fill=(30, 26, 30))
        elif shape == 'tent':
            draw.polygon([(sx - half, y1), (sx + half, y1), (sx, y0)], fill=c)
        elif shape == 'smoke':
            # a widening plume leaning east with the wind
            draw.polygon([(sx - half * 0.3, y1), (sx + half * 0.3, y1), (sx + half * 1.8, y0),
                          (sx - half * 0.2, y0)], fill=c)
        elif shape == 'falls':
            draw.rectangle((sx - half, y0, sx + half, y1), fill=c)
        else:
            draw.rectangle((sx - half, y0, sx + half, y1), fill=c)
        bx0, bx1 = max(0, int(sx - half * 2) - 2), min(w, int(sx + half * 2) + 3)
        by0, by1 = max(0, int(y0 - (y1 - y0) * 0.3) - 2), min(h, int(y1) + 3)
        if bx0 >= bx1 or by0 >= by1:
            continue
        alpha = np.asarray(layer.crop((bx0, by0, bx1, by1)).split()[3]).copy()
        alpha[depth[by0:by1, bx0:bx1] < d * 0.98] = 0
        mask = Image.fromarray(alpha)
        out.paste(layer.crop((bx0, by0, bx1, by1)).convert('RGB'), (bx0, by0), mask)
    draw = ImageDraw.Draw(out)
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
        base = (hb if hb > 1 else 2200) + rise
        sy = horizon - (base - eye) / z * focal
        draw.ellipse((sx - 9, sy - 9, sx + 9, sy + 9), outline=(40, 200, 255), width=4)
        draw.text((sx + 12, sy - 12), label, fill=(20, 170, 240), font=FONT)
    out.save(out_path)


def models_for(sketch, plan, trees):
    """Blocks for the blockout: (cell x, cell y, base or None, height, half width cells, colour, shape)."""
    m = []
    timber = (120, 92, 66)
    # the dwarves' watch: a stockade with a signal tower at its north-west corner
    for x in range(65, 71):
        m.append((x, 80, None, 300, 0.55, timber, 'box'))
        m.append((x, 85, None, 300, 0.55, timber, 'box'))
    for y in (81, 84):
        m.append((65, y, None, 300, 0.55, timber, 'box'))
        m.append((70, y, None, 300, 0.55, timber, 'box'))
    m.append((66, 81, None, 900, 0.6, (132, 100, 76), 'cone'))
    # Sablewing's crag with the dark cave mouth
    m.append((77.5, 89.5, None, 520, 1.6, (128, 80, 64), 'box'))
    m.append((76.5, 90.5, None, 220, 0.5, (20, 16, 16), 'box'))
    # the orc outpost: hide tents round a fire
    for dx, dy in [(0, 0), (1.2, 0.8), (-1, 1)]:
        m.append((31 + dx, 86 + dy, None, 220, 0.5, (120, 96, 70), 'tent'))
    # the Orc Caves' back gate, the Shrine of Fire, the Well of Speed, the obelisk, the cairn
    m.append((88.5, 100.5, None, 260, 0.5, (70, 50, 36), 'box'))
    m.append((52, 98, None, 380, 0.5, (150, 60, 40), 'box'))
    m.append((28, 102, None, 120, 0.3, (130, 120, 110), 'box'))
    m.append((64, 63, None, 900, 0.25, (40, 40, 48), 'box'))
    m.append((40, 65, None, 160, 0.4, (120, 100, 90), 'box'))
    # the north: the black bridge, the idols at the Volcano Cave, the Dragon Cave's crag, the Dragon Tower
    m.append((61, 43, None, 80, 0.8, (24, 22, 22), 'box'))
    m.append((65.6, 44.2, None, 520, 0.4, (60, 30, 30), 'box'))
    m.append((65.6, 46.2, None, 520, 0.4, (60, 30, 30), 'box'))
    m.append((66.2, 45.2, None, 300, 0.5, (14, 10, 10), 'box'))
    m.append((56, 27.5, None, 600, 2.0, (44, 40, 42), 'box'))
    m.append((56, 29.6, None, 260, 0.6, (12, 10, 10), 'box'))
    m.append((29.5, 29.5, 2600, 1800, 1.0, (40, 36, 42), 'cone'))
    m.append((101, 26, None, 700, 0.6, (140, 120, 110), 'box'))      # the Fire Reflector
    m.append((35, 44, 1560, 60, 0.3, (255, 120, 40), 'box'))          # the hot rock
    # the smoke plume over the crater and the lava falling off the north rim
    m.append((FIRESTONE[0], FIRESTONE[1], 5000, 4200, 3.2, (92, 86, 88), 'smoke'))
    for k in range(4):
        m.append((72.0 + k * 0.4, 26.8, 0, 2250, 0.35, (255, 120 - k * 10, 30), 'falls'))
    for x, y, c in trees:
        m.append((x, y, None, 260, 0.2, c, 'tree'))
    return m


BLOCKOUT_FOV = {'view:arrival': 80.0, 'view:signature': 80.0}
BLOCKOUT_PITCH = {'view:arrival': 1.5, 'view:signature': -6.0}  # negative looks down

ANNOTATIONS = {
    'view:arrival': [
        ("dwarves' watch, signal tower", 66, 81, 900),
        ("Sablewing's cave", 76.5, 90.5, 300),
        ('the Firestone Gap', 62, 66, 200),
        ('Mount Firestone, smoking', 88.5, 40.5, 600),
        ('Red Dwarf Range', 50, 61, 200),
    ],
    'view:signature': [
        ('lava falls over the cove wall', 72.5, 26.5, 1300),
        ('Mount Firestone', 88.5, 40.5, 300),
        ('crater, smoke', 88.5, 40.5, 2500),
        ('Fire corner, Reflector', 101, 26, 700),
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
NOT_POI = ('poi:sablewing',)   # an NPC actor: a place for the 6,000 rule, not a POI
POI_ENTRANCES = ('entrance:xd16_mouth', 'entrance:xd17_cleft', 'entrance:xd18_mouth', 'entrance:fd04_door',
                 'entrance:xd05_gate')
DIF_MIX = {0: (1, 0, 0), 1: (0.9, 0.08, 0.02), 2: (0.7, 0.2, 0.1), 3: (0.5, 0.3, 0.2), 4: (0.3, 0.4, 0.3),
           5: (0.1, 0.5, 0.4)}   # tools/xeen/balance.py
LEVELS = {'Xeen Orc': (5, 7, 10), 'Xeen Hydra': (45, 55, 65), 'Xeen Dragon': (60, 66, 75)}
PLACES = ('zone:the_gap', 'zone:dwarf_watch', 'zone:sablewing_cave', 'zone:orc_outpost', 'zone:volcano_mouth',
          'zone:dragon_crag', 'zone:tower_crag', 'zone:lava_island', 'zone:crater', 'zone:fire_corner')
PLACED_LEVEL = {'11593': 55, '11030': 5, '11032': 10}


def census(plan, sketch):
    spots = []      # (label, x, y) in cells, centred
    for p in sketch['points']:
        pid = p['id']
        if pid.startswith('poi:') and pid not in NOT_POI or pid in POI_ENTRANCES:
            spots.append((pid + (f'#{p["index"]}' if 'index' in p else ''), p['at'][0] + 0.5, p['at'][1] + 0.5))
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


def figures_for(plan, sketch, project, height, lava, rim):
    x0, y0, x1, y1 = PLAY
    land = np.zeros((N, N), bool)
    land[y0:y1, x0:x1] = True
    hc = height[RES // 2::RES, RES // 2::RES]
    lc = lava[RES // 2::RES, RES // 2::RES]
    box = land & (hc > 1)
    land &= (hc > 1) & ~lc
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
    dragons = [a['polygon'] for a in sketch['areas'] if a.get('kind', 'encounter') == 'encounter' and a['slot'] == 3]
    north = [a['polygon'] for a in sketch['areas'] if a.get('kind', 'encounter') == 'encounter' and a['slot'] > 1]

    def nearest(polys, at):
        x, y = at[0] + 0.5, at[1] + 0.5
        return int(round(min(poly_dist(p, x, y) for p in polys) * 512, -2))

    def nearest_line(polys, line):
        best = 1e9
        for a, b in zip(line, line[1:]):
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.25))
            for i in range(n + 1):
                t = i / n
                x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                best = min(best, min(poly_dist(p, x, y) for p in polys))
        return int(round(best * 512, -2))
    edge = {k: nearest(fights, pts_[k]) for k in ['entrance:west_road', 'entrance:south_road']}
    roads = {r['link']: r['line'] for r in sketch['roads']}
    buffers = {
        'Sablewing': nearest(fights, pts_['poi:sablewing']),
        "dwarves' watch (chest)": nearest(fights, pts_['poi:watch_chest']),
        'the Gap (junction)': nearest(fights, pts_['junction:gap']),
        'obelisk': nearest(fights, pts_['poi:obelisk']),
        'north monsters from the Gap': nearest(north, pts_['junction:gap']),
        'north monsters from the north road': nearest_line(north, roads['link:north_road']),
        'dragons from the tax road (north track)': nearest_line(dragons, roads['link:north_track']),
        'dragons from the Volcano Cave': nearest(dragons, pts_['entrance:xd16_mouth']),
        'dragons from the X1 arrival': nearest(dragons, pts_['entrance:south_road']),
    }
    comps = census(plan, sketch)
    # places for the 6,000 rule: every point on land (POIs, NPCs, entrances, junctions, landmarks), every encounter
    # area, every placed group
    seed = np.zeros((N, N), bool)
    for p in sketch['points']:
        x, y = p['at']
        if 0 <= x < N and 0 <= y < N and not rim[int((y + .5) * RES), int((x + .5) * RES)]:
            seed[int(y), int(x)] = True
    for a in sketch.get('actors', []):
        seed[int(a['at'][1]), int(a['at'][0])] = True
    seed |= enc
    for d in sketch['districts']:
        if d['space'] in PLACES:
            seed |= poly_mask(d['polygon'], scale=1)
    dist = ndimage.distance_transform_edt(~seed) * 512
    far = float(((dist > 3000) & land).sum() / n_land)
    farthest = int(round(dist[land].max(), -2))
    fy, fx = np.unravel_index(np.argmax(np.where(land, dist, 0)), dist.shape)
    nn = []
    cpts = [c['at'] for c in comps]
    for i, a in enumerate(cpts):
        nn.append(min(math.hypot(a[0] - b[0], a[1] - b[1]) for j, b in enumerate(cpts) if j != i) * 512)
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
    placed = sum(a.get('count', 1) for a in sketch.get('actors', []))
    xp = lambda L: L * (L + 10)
    kill = 0.0
    per_family = {}
    level_mean = {}
    south_xp = 0.0
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
        if a['slot'] == 1:
            south_xp += v
    for act in sketch.get('actors', []):
        v = act.get('count', 1) * xp(PLACED_LEVEL[act['monster']])
        kill += v
        name = {'11593': 'Lava Golem (placed)', '11030': 'Orcs (placed)', '11032': 'Orcs (placed)'}[act['monster']]
        per_family[name] = per_family.get(name, 0) + v
    pois = plan['points_of_interest']
    chests = [p['id'] for p in pois if p['kind'] == 'chest']
    north_cells = int((land[:60, :]).sum())
    return {
        'land_cells': n_land,
        'quiet_share': round(quiet, 3),
        'areas': areas,
        'markers': sum(a['count'] for a in sketch['areas'] if a.get('kind', 'encounter') == 'encounter'),
        'hostiles_markers': marker_hostiles,
        'hostiles_placed': placed,
        'hostiles': marker_hostiles + placed,
        'kill_xp_member': round(kill / 4 / 1000, 1),
        'kill_xp_by_family_member': {k: round(v / 4 / 1000, 1) for k, v in per_family.items()},
        'kill_xp_south_member': round(south_xp / 4 / 1000, 2),
        'mean_level_by_family': level_mean,
        'road_share': round(road_share, 4),
        'lane_share': round(lane_share, 4),
        'first_fight_edges': edge,
        'buffers': buffers,
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
        'entrances': len(POI_ENTRANCES),
        'height_range_points': [min(pts_h), max(pts_h)],
        'height_range_points_inside': [min(inside_pts), max(inside_pts)],
        'height_box_field': [int(round(float(hbox.min()), -1)), int(round(float(hbox.max()), -1))],
        'height_box_span': int(round(float(hbox.max() - hbox.min()), -1)),
        'height_box_low_at': [int(lx_), int(ly_)],
        'height_box_high_at': [int(hx_), int(hy_)],
        'lava_cells_in_box': int((lc & box).sum()),
        'north_land_share': round(north_cells / n_land, 3),
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
    height, lava, rim = build_land(sketch)
    np.save(OUT / 'height.npy', height.astype(np.float32))
    img, trees, bare = colour_land(sketch, height, lava, rim)
    img.save(OUT / 'colour.png')
    figures = figures_for(plan, sketch, project, height, lava, rim)
    (OUT / 'figures.json').write_text(json.dumps(figures, indent=1))
    svg = svg_plan(plan, sketch, img, figures)
    (OUT / 'plan_x7.svg').write_text(svg)
    chrome(OUT / 'plan_x7.svg', OUT / 'plan_x7.png')
    chrome(OUT / 'plan_x7.svg', OUT / 'plan_x7_2x.png', scale=2)
    models = models_for(sketch, plan, trees)
    for view in sketch.get('views', []):
        name = view['id'].split(':')[1]
        blockout(height, bare, view, models, OUT / f'blockout_{name}.png', annotations=ANNOTATIONS.get(view['id']),
                 fov=BLOCKOUT_FOV.get(view['id'], 80.0), lava=lava)
    print(json.dumps({k: v for k, v in figures.items() if k not in ('areas', 'chest_ids', 'poi_components')},
                     indent=1))


if __name__ == '__main__':
    main()
