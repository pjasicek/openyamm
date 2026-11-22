#!/usr/bin/env python3
"""X3 MU-3 drawing and MU-4 blockouts from the L1 brief data (lane A5).

    python3 level_generation/projects/xeen/x3/render.py

Writes output/studio_cal/x3/mockups/: colour.png and height.npy (the land the plan implies), plan_x3.svg and
plan_x3.png (headless Chrome), blockout_arrival.png, blockout_signature.png, figures.json.
The blockout ray caster is A6's (level_generation/xeen_art/phase2/plan_render.py, imported, not changed).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import base64
import io
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x3') / 'mockups'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'level_generation/xeen_art/phase2'))
import x3lib as L  # noqa: E402
import gen_l1 as G  # noqa: E402

RES = L.RES
N = L.N

GROUND = {  # space: sRGB ground colour (swamp, mud, patchy grass, soil, rock)
    'zone:bogwood': (78, 92, 58),
    'zone:north_vale': (112, 122, 72),
    'zone:crow_hills': (88, 96, 66),
    'zone:newcastle_rise': (120, 124, 80),
    'zone:east_meadow': (116, 122, 76),
    'zone:reedbeds': (126, 128, 82),
    'zone:east_ridge': (104, 104, 80),
    'zone:black_fen': (84, 86, 58),
    'zone:gloomwood': (86, 80, 62),
    'zone:drowned_shore': (92, 94, 66),
}
TREES = {  # space: (trees per cell, colour, kind)
    'zone:bogwood': (0.55, (34, 52, 32), 'tree'),
    'zone:gloomwood': (0.45, (92, 82, 70), 'dead'),
    'zone:crow_hills': (0.25, (38, 56, 36), 'tree'),
    'zone:black_fen': (0.10, (48, 66, 40), 'tree'),
    'zone:drowned_shore': (0.10, (70, 70, 56), 'dead'),
    'zone:reedbeds': (0.10, (50, 72, 44), 'tree'),
    'zone:north_vale': (0.05, (44, 64, 40), 'tree'),
    'zone:east_ridge': (0.08, (48, 62, 40), 'tree'),
    'zone:east_meadow': (0.03, (44, 64, 40), 'tree'),
    'zone:newcastle_rise': (0.02, (44, 64, 40), 'tree'),
}
AREA_COLOUR = {'E1': '#c0282d', 'E2': '#d0602a', 'E3': '#7a1a6a', 'E4': '#b03a3a', 'E5': '#e07a1f'}


def colour_land(height, water, rim):
    size = N * RES
    rgb = np.zeros((size, size, 3))
    rgb[:] = (100, 108, 70)
    jitter = ndimage.gaussian_filter(np.random.default_rng(8).normal(size=(size, size)), 1.5 * RES)
    jitter /= np.abs(jitter).max() + 1e-6
    for space, colour in GROUND.items():
        m = L.poly_mask(G.ZONES[space]).astype(float)
        soft = ndimage.gaussian_filter(m, 2.0 * RES)
        soft = np.clip(soft + jitter * 0.35 * soft * (1 - soft) * 4, 0, 1)[..., None]
        rgb = rgb * (1 - soft) + np.array(colour) * soft
    # swamp patches (darker, wet) in the fens
    wet = ndimage.gaussian_filter(np.random.default_rng(4).normal(size=(size, size)), 1.2 * RES)
    fen = L.poly_mask(G.ZONES['zone:black_fen']) | L.poly_mask(G.ZONES['zone:drowned_shore'])
    fen = ndimage.gaussian_filter(fen.astype(float), RES)
    wetm = np.clip((wet - 0.15) * 6, 0, 1) * fen
    rgb = rgb * (1 - wetm[..., None] * 0.45) + np.array((52, 62, 44)) * wetm[..., None] * 0.45
    # town ground and roads
    for poly, col in [(G.TOWN_NIGHTSHADOW, (104, 100, 86)), (G.CAMP, (122, 112, 86)),
                      (G.NEWCASTLE, (150, 146, 128)), (G.ISLET, (110, 108, 96))]:
        m = ndimage.gaussian_filter(L.poly_mask(poly).astype(float), 0.8 * RES)[..., None]
        rgb = rgb * (1 - m) + np.array(col) * m
    # rock where steep or high
    gy, gx = np.gradient(height, 512 / RES)
    slope = np.hypot(gx, gy)
    rock = np.clip((slope - 0.42) * 2.2, 0, 1)
    rock = np.maximum(rock, np.clip((height - 2700) / 600, 0, 0.7))
    rgb = rgb * (1 - rock[..., None]) + np.array((104, 98, 92)) * rock[..., None]
    rgb[water] = (46, 70, 64)
    # hillshade
    light = np.array([-0.55, -0.65, 0.52])
    nx, ny = -gx * 2.2, -gy * 2.2
    nz = np.ones_like(nx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    shade = (nx * light[0] + ny * light[1] + nz * light[2]) / norm
    shade = np.clip(0.55 + 0.6 * shade, 0.35, 1.2)
    rgb = rgb * shade[..., None]
    rgb[water] = (46, 70, 64)
    # mist over Nightshadow (a pale veil)
    mist = ndimage.gaussian_filter(L.poly_mask(G.TOWN_NIGHTSHADOW).astype(float), 3 * RES)
    mist = np.clip(mist * 1.3, 0, 0.55)[..., None]
    rgb = rgb * (1 - mist) + np.array((196, 200, 204)) * mist
    # stars below the rim
    stars = np.zeros((size, size, 3))
    stars[:] = (10, 12, 26)
    rng = np.random.default_rng(3)
    for y, x in rng.integers(0, size, size=(1500, 2)):
        stars[y, x] = rng.integers(140, 255)
    rgb[rim] = stars[rim]
    cliff = ndimage.binary_dilation(~rim, iterations=int(1.0 * RES)) & rim
    rgb[cliff] = (92, 86, 80)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    roads = ndimage.binary_dilation(L.road_mask(), iterations=RES)
    towns = L.poly_mask(G.TOWN_NIGHTSHADOW) | L.poly_mask(G.CAMP) | L.poly_mask(G.NEWCASTLE) | L.poly_mask(G.ISLET)
    for space, (density, colour, kind) in TREES.items():
        m = L.poly_mask(G.ZONES[space])
        ys, xs = np.nonzero(m[::RES, ::RES])
        for cy, cx in zip(ys, xs):
            for _ in range(rng.poisson(density * 2)):
                x = (cx + rng.random()) * RES
                y = (cy + rng.random()) * RES
                hy, hx = int(min(y, size - 1)), int(min(x, size - 1))
                if water[hy, hx] or rim[hy, hx] or roads[hy, hx] or towns[hy, hx] or height[hy, hx] > 2900:
                    continue
                s = RES * (0.35 + 0.2 * rng.random())
                if kind == 'dead':
                    draw.line([(x, y + s * 0.6), (x, y - s * 1.2)], fill=colour, width=2)
                    draw.line([(x, y - s * 0.4), (x + s * 0.7, y - s * 1.0)], fill=colour, width=1)
                    draw.line([(x, y - s * 0.2), (x - s * 0.6, y - s * 0.8)], fill=colour, width=1)
                else:
                    draw.ellipse((x - s * 0.8, y - s * 0.8, x + s * 0.8, y + s * 0.6), fill=colour)
    # reeds along the lagoon's shores
    lag = L.poly_mask(G.LAGOON)
    ring = ndimage.binary_dilation(lag, iterations=RES) & ~lag & ~roads
    ys, xs = np.nonzero(ring[::3, ::3])
    for y, x in zip(ys * 3, xs * 3):
        if rng.random() < 0.25:
            draw.line([(x, y), (x + rng.integers(-1, 2), y - 4)], fill=(148, 150, 88), width=1)
    return img


# ------------------------------------------------------------------ SVG plan

def esc(text):
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def P(points, s):
    return ' '.join(f'{x * s:.1f},{y * s:.1f}' for x, y in points)


SYM = {'entrance': ('#0b6b3a', 'sq'), 'dungeon': ('#111', 'sq'), 'junction': ('#5a4630', 'dot'),
       'device': ('#7a1f6a', 'dot'), 'chest': ('#b8860b', 'diamond'), 'npc': ('#1d5fa8', 'dot'),
       'camp': ('#b1361e', 'tri'), 'landmark': ('#c06000', 'star')}

OFFSETS = {  # label offsets in pixels (dx, dy, anchor)
    'entrance:nightshadow_square': (14, 22, 'start'),
    'entrance:newcastle_gate': (-10, 22, 'end'),
    'entrance:x8_landing': (10, -6, 'start'),
    'entrance:xd13_keep': (12, -10, 'start'),
    'entrance:xd11_tower': (12, 20, 'start'),
    'entrance:xd08_tomb': (-12, 24, 'end'),
    'entrance:xd24_crypt': (50, -16, 'start'),
    'junction:lagoon_cross': (8, -10, 'start'),
    'junction:causeway_fork': (10, -8, 'start'),
    'junction:fen_fork': (0, -14, 'middle'),
    'junction:tomb_fork': (-10, -6, 'end'),
    'poi:obelisk': (10, 4, 'start'),
    'poi:marsh_well': (-10, 4, 'end'),
    'poi:lifeforce_spring': (-10, 4, 'end'),
    'poi:food_trees': (10, 4, 'start'),
    'poi:mirabeth': (-10, 16, 'end'),
    'poi:work_yard': (-10, -6, 'end'),
    'poi:ranger_camp': (12, 4, 'start'),
    'poi:sunken_punt': (-10, 14, 'end'),
    'poi:tax_coffer': (10, 14, 'start'),
    'poi:eel_fisher': (10, 14, 'start'),
    'poi:pilgrim_pack': (-10, 16, 'end'),
    'poi:wreck': (10, 4, 'start'),
    'poi:crow_watchtower': (10, -6, 'start'),
    'poi:sunken_graves': (10, -4, 'start'),
    'poi:garlic_shrine': (10, 4, 'start'),
    'landmark:crow_crown': (12, 4, 'start'),
}
CAPTIONS = [
    ('E1 Bogwood: 22 at load (swamp things, toads; rangers 7)', (32.5, 18), 12.5, '#7a1010'),
    ('E2 Black Fen: 21 (swamp things, toads)', (44, 74.4), 12.5, '#8a3c00'),
    ('E3 Gloomwood: 35 (zombies, ghouls)', (34, 106.6), 12.5, '#5a0a50'),
    ('E4 Drowned Shore: 36 (swamp things, drowned dead; bats 8)', (82, 106.6), 12.5, '#7a1010'),
    ('E5 Crow Hills: 15 (toads)', (88, 18), 12.5, '#8a4a00'),
    ('NIGHTSHADOW', (100.5, 58.5), 15, '#222'),
    ("EBENEZER'S CAMP", (88.5, 49.6), 12, '#222'),
    ('NEWCASTLE (ruin)', (82.5, 28.6), 13, '#222'),
    ('Lifeforce Lagoon', (78, 76.5), 15, '#e8f0ec'),
    ('Lagoon Water', (45.5, 68.6), 11, '#e8f0ec'),
    ('the world rim: a cliff above the stars', (64, 114), 13, '#ccd'),
    ('to X2 (east edge, y 40)', (118, 38.4), 11.5, '#222'),
    ('to X5 (west edge, y 59)', (9.5, 57.6), 11.5, '#222'),
    ('to X4 (north edge, x 50)', (50, 5), 11.5, '#222'),
    ('quiet: the north vale', (53, 51.2), 11, '#1d5a35'),
]


def svg_plan(colour_path, figures, marks, scale=8):
    size = N * scale
    colour = Image.open(colour_path).resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    colour.save(buf, 'JPEG', quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode()
    W = size + 60 + 330
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-30 -60 {W} {size + 90}" width="{W}" '
         f'height="{size + 90}" font-family="DejaVu Sans, sans-serif">',
         f'<rect x="-30" y="-60" width="{W}" height="{size + 90}" fill="#1b1d22"/>',
         f'<image href="data:image/jpeg;base64,{b64}" x="0" y="0" width="{size}" height="{size}"/>',
         '<defs><pattern id="quiet" width="10" height="10" patternUnits="userSpaceOnUse" '
         'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="10" stroke="#2e8b57" '
         'stroke-width="2" stroke-opacity="0.55"/></pattern>'
         '<marker id="arr" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" '
         'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#0b6b3a"/></marker></defs>',
         f'<text x="0" y="-34" font-size="20" font-weight="bold" fill="#eee">X3 Lifeforce Lagoon: MU-3 plan '
         f'(to scale, 128 x 128 cells of 512)</text>']
    # 512-unit grid: fine lines every cell faint, every 8 cells (4,096 blocks) stronger
    for i in range(0, N + 1):
        op = 0.22 if i % 8 == 0 else 0.06
        o.append(f'<line x1="{i * scale}" y1="0" x2="{i * scale}" y2="{size}" stroke="#000" stroke-opacity="{op}"/>')
        o.append(f'<line x1="0" y1="{i * scale}" x2="{size}" y2="{i * scale}" stroke="#000" stroke-opacity="{op}"/>')
    for i in range(0, N + 1, 16):
        o.append(f'<text x="{i * scale}" y="-8" font-size="12" text-anchor="middle" fill="#bbb">{i}</text>')
        o.append(f'<text x="-8" y="{i * scale + 4}" font-size="12" text-anchor="end" fill="#bbb">{i}</text>')
    x0, y0, x1, y1 = L.PLAY
    o.append(f'<rect x="{x0 * scale}" y="{y0 * scale}" width="{(x1 - x0) * scale}" height="{(y1 - y0) * scale}" '
             'fill="none" stroke="#fff" stroke-opacity="0.8" stroke-dasharray="8 6" stroke-width="1.6"/>')
    # quiet areas, then encounter areas (one outline per area key)
    for qid, kind, poly, _ in G.QUIET:
        if qid == 'water:lagoon':
            continue
        o.append(f'<polygon points="{P(poly, scale)}" fill="url(#quiet)" stroke="#2e8b57" stroke-opacity="0.85" '
                 'stroke-width="1.5" stroke-dasharray="4 3"/>')
    done = set()
    for pid, slot, count, key, poly, _ in G.AREAS:
        if key in done:
            continue
        done.add(key)
        c = AREA_COLOUR[key]
        o.append(f'<polygon points="{P(poly, scale)}" fill="{c}" fill-opacity="0.16" stroke="{c}" '
                 'stroke-width="2.4" stroke-opacity="0.95"/>')
    # roads
    for link, line, width, _ in G.ROADS:
        lane = width == 'lane'
        w = 3 if lane else 5
        o.append(f'<polyline points="{P(line, scale)}" fill="none" stroke="#3b2a1a" stroke-width="{w + 2}" '
                 'stroke-opacity="0.6" stroke-linecap="round" stroke-linejoin="round"/>')
        dash = ' stroke-dasharray="7 4"' if lane else ''
        o.append(f'<polyline points="{P(line, scale)}" fill="none" stroke="{"#e0cfa4" if lane else "#cfa564"}" '
                 f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"{dash}/>')
    # structures: the ruin, the tower, the tomb, the crypt
    for poly, fill, label in [([[78.5, 30.5], [85.5, 30.5], [85.5, 36.5], [78.5, 36.5]], '#d8d2c0', None)]:
        o.append(f'<polygon points="{P(poly, scale)}" fill="{fill}" fill-opacity="0.55" stroke="#ece6d4" '
                 'stroke-width="2" stroke-dasharray="5 3"/>')
    o.append(f'<circle cx="{64.5 * scale}" cy="{69.5 * scale}" r="{1.6 * scale}" fill="#50505a" stroke="#ddd" '
             'stroke-width="1.5"/>')
    o.append(f'<ellipse cx="{34 * scale}" cy="{86.5 * scale}" rx="{4 * scale}" ry="{3.5 * scale}" fill="#2a2420" '
             'fill-opacity="0.7" stroke="#888" stroke-width="1.2"/>')
    # plots
    for space in ('town:nightshadow', 'town:ebenezer_camp'):
        for b, idx, at, facing, door_to, kit, house in G.PLOTS[space]:
            fp = L.footprint(b, idx)
            wx, wy = (fp[0], fp[1]) if facing in 'ns' else (fp[1], fp[0])
            x, y = at
            service = b != 'building:nightshadow_houses'
            fill = '#6e3b2a' if service else '#8a6a52'
            if b == 'building:ebenezer_tent':
                fill = '#a8642a'
            o.append(f'<rect x="{x * scale:.1f}" y="{y * scale:.1f}" width="{wx * scale:.1f}" '
                     f'height="{wy * scale:.1f}" fill="{fill}" stroke="#1a100a" stroke-width="1.2"/>')
            dx, dy = L.door_point(b, idx, at, facing)
            o.append(f'<circle cx="{dx * scale:.1f}" cy="{dy * scale:.1f}" r="2.4" fill="#ffd34d" stroke="#2a1a10" '
                     'stroke-width="0.8"/>')
            o.append(f'<text x="{(x + wx / 2) * scale:.1f}" y="{(y + wy / 2) * scale + 3:.1f}" font-size="8" '
                     f'text-anchor="middle" fill="#fff">{house}</text>')
    # indicative markers and placed actors
    for x, y, slot, key in marks:
        o.append(f'<circle cx="{x * scale:.1f}" cy="{y * scale:.1f}" r="3.2" fill="{AREA_COLOUR[key]}" '
                 'stroke="#fff" stroke-width="0.8"/>')
    for m, at, c, *_ in G.ACTORS:
        x, y = at
        o.append(f'<path d="M{x * scale - 4},{y * scale - 4} L{x * scale + 4},{y * scale + 4} M{x * scale - 4},'
                 f'{y * scale + 4} L{x * scale + 4},{y * scale - 4}" stroke="#ff4040" stroke-width="2"/>')
    # cameras
    for v in G.VIEWS:
        x, y = v['at']
        lx, ly = v['look']
        ang = math.atan2(ly - y, lx - x)
        dist = 26
        half = math.radians(40)
        p1 = (x + math.cos(ang - half) * dist, y + math.sin(ang - half) * dist)
        p2 = (x + math.cos(ang + half) * dist, y + math.sin(ang + half) * dist)
        col = '#1f6fd1' if v['id'] == 'view:arrival' else '#d11fa8'
        o.append(f'<polygon points="{P([(x, y), p1, p2], scale)}" fill="{col}" fill-opacity="0.10" stroke="{col}" '
                 'stroke-width="1.6" stroke-dasharray="6 4"/>')
        ex, ey = x + math.cos(ang) * dist, y + math.sin(ang) * dist
        o.append(f'<line x1="{x * scale}" y1="{y * scale}" x2="{ex * scale}" y2="{ey * scale}" stroke="{col}" '
                 'stroke-width="2.2"/>')
        o.append(f'<circle cx="{x * scale}" cy="{y * scale}" r="7" fill="{col}" stroke="#fff" stroke-width="1.8"/>')
        name = 'ARRIVAL VIEW' if v['id'] == 'view:arrival' else 'SIGNATURE VIEW'
        tx, ty = (x + 1.5, y + 3.4) if v['id'] == 'view:arrival' else (73.5, 64.5)
        o.append(f'<text x="{tx * scale}" y="{ty * scale}" font-size="12" font-weight="bold" fill="{col}" '
                 f'stroke="#fff" stroke-width="3" paint-order="stroke" text-anchor="middle">{name}</text>')
    # points and labels
    seen = set()
    for pid, at, facing, kind, label in G.POINTS:
        x, y = at
        cx, cy = x * scale, y * scale
        c, shape = SYM[kind]
        if pid.startswith('poi:signposts'):
            continue
        if shape == 'sq':
            o.append(f'<rect x="{cx - 6}" y="{cy - 6}" width="12" height="12" fill="{c}" stroke="#fff" stroke-width="1.5"/>')
        elif shape == 'diamond':
            o.append(f'<polygon points="{cx},{cy - 7} {cx + 7},{cy} {cx},{cy + 7} {cx - 7},{cy}" fill="{c}" '
                     'stroke="#fff" stroke-width="1.5"/>')
        elif shape == 'tri':
            o.append(f'<polygon points="{cx},{cy - 8} {cx + 7},{cy + 6} {cx - 7},{cy + 6}" fill="{c}" stroke="#fff" '
                     'stroke-width="1.5"/>')
        elif shape == 'star':
            star = []
            for i in range(10):
                r = 9 if i % 2 == 0 else 4
                a = -math.pi / 2 + i * math.pi / 5
                star.append(f'{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}')
            o.append(f'<polygon points="{" ".join(star)}" fill="{c}" stroke="#fff" stroke-width="1.2"/>')
        else:
            r = 4 if pid.startswith('poi:sundials') else 5
            o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{c}" stroke="#fff" stroke-width="1.5"/>')
        if kind == 'entrance' and pid in ('entrance:east_road', 'entrance:west_road', 'entrance:north_road'):
            dx, dy = {'n': (0, -1), 's': (0, 1), 'e': (1, 0), 'w': (-1, 0)}[facing]
            o.append(f'<line x1="{cx - dx * 28}" y1="{cy - dy * 28}" x2="{cx - dx * 9}" y2="{cy - dy * 9}" '
                     'stroke="#0b6b3a" stroke-width="4" marker-end="url(#arr)"/>')
        if not label or (pid, label) in seen:
            continue
        seen.add((pid, label))
        dx, dy, anchor = OFFSETS.get(pid, (9, 4, 'start'))
        o.append(f'<text x="{cx + dx}" y="{cy + dy}" font-size="12" text-anchor="{anchor}" fill="#111" '
                 f'stroke="#fff" stroke-width="3.2" paint-order="stroke" stroke-linejoin="round">{esc(label)}</text>')
    for text, (x, y), fs, col in CAPTIONS:
        halo = '#000' if col.startswith('#e') or col.startswith('#c') else '#fff'
        o.append(f'<text x="{x * scale}" y="{y * scale}" font-size="{fs}" font-style="italic" font-weight="bold" '
                 f'text-anchor="middle" fill="{col}" stroke="{halo}" stroke-width="3" stroke-opacity="0.7" '
                 f'paint-order="stroke">{esc(text)}</text>')
    # scale bar
    bx, by = 4 * scale, (N - 5) * scale
    o.append(f'<rect x="{bx - 8}" y="{by - 26}" width="{10 * scale + 220}" height="40" fill="#000" fill-opacity="0.6"/>')
    for i in range(10):
        o.append(f'<rect x="{bx + i * scale}" y="{by - 3}" width="{scale}" height="6" '
                 f'fill="{"#fff" if i % 2 == 0 else "#888"}"/>')
    o.append(f'<text x="{bx + 10 * scale + 8}" y="{by + 5}" font-size="13" fill="#fff">5,120 units (10 cells of 512)</text>')
    o.append(f'<text x="{bx}" y="{by - 10}" font-size="12" fill="#fff">fine grid 512 units; bold grid 4,096 (blocks)</text>')
    # legend panel on the right
    lx = size + 18
    rows = [
        ('sq', '#0b6b3a', 'arrival (edge, mirror, Town Portal, X8 fall)'),
        ('sq', '#111', 'dungeon door (XD-08, -11, -13, -24)'),
        ('diamond', '#b8860b', 'chest (with a reason)'),
        ('dot', '#7a1f6a', 'device (obelisk, well, spring, sundial...)'),
        ('tri', '#b1361e', 'camp'),
        ('dot', '#1d5fa8', 'NPC actor (Mirabeth)'),
        ('dot', '#5a4630', 'signposted fork'),
        ('star', '#c06000', 'landmark'),
        ('rect', '#6e3b2a', 'service house (A4 id)'),
        ('rect', '#8a6a52', 'residence (A4 id)'),
        ('mk', '#c0282d', 'spawn marker (indicative spot)'),
        ('x', '#ff4040', 'placed hostiles (rangers, bats)'),
        ('area', '#c0282d', 'encounter area (E1-E5)'),
        ('quiet', '#2e8b57', 'quiet / keep-clear land'),
        ('road', '#cfa564', 'road (1 cell); dashed: lane'),
        ('cam', '#1f6fd1', 'MU-4 camera, 80-degree view'),
    ]
    o.append(f'<text x="{lx}" y="14" font-size="15" font-weight="bold" fill="#eee">Legend</text>')
    for i, (shape, c, text) in enumerate(rows):
        y = 40 + i * 26
        if shape == 'sq':
            o.append(f'<rect x="{lx}" y="{y - 6}" width="12" height="12" fill="{c}" stroke="#fff"/>')
        elif shape == 'diamond':
            o.append(f'<polygon points="{lx + 6},{y - 7} {lx + 13},{y} {lx + 6},{y + 7} {lx - 1},{y}" fill="{c}" stroke="#fff"/>')
        elif shape == 'tri':
            o.append(f'<polygon points="{lx + 6},{y - 8} {lx + 13},{y + 6} {lx - 1},{y + 6}" fill="{c}" stroke="#fff"/>')
        elif shape == 'star':
            o.append(f'<circle cx="{lx + 6}" cy="{y}" r="7" fill="{c}" stroke="#fff"/>')
        elif shape == 'rect':
            o.append(f'<rect x="{lx}" y="{y - 6}" width="14" height="12" fill="{c}" stroke="#1a100a"/>')
        elif shape == 'mk':
            o.append(f'<circle cx="{lx + 6}" cy="{y}" r="3.5" fill="{c}" stroke="#fff"/>')
        elif shape == 'x':
            o.append(f'<path d="M{lx + 2},{y - 4} L{lx + 10},{y + 4} M{lx + 2},{y + 4} L{lx + 10},{y - 4}" stroke="{c}" stroke-width="2"/>')
        elif shape == 'area':
            o.append(f'<rect x="{lx}" y="{y - 7}" width="16" height="14" fill="{c}" fill-opacity="0.2" stroke="{c}" stroke-width="2"/>')
        elif shape == 'quiet':
            o.append(f'<rect x="{lx}" y="{y - 7}" width="16" height="14" fill="url(#quiet)" stroke="{c}" stroke-dasharray="4 3"/>')
        elif shape == 'road':
            o.append(f'<line x1="{lx}" y1="{y}" x2="{lx + 16}" y2="{y}" stroke="{c}" stroke-width="5"/>')
        elif shape == 'cam':
            o.append(f'<circle cx="{lx + 6}" cy="{y}" r="6" fill="{c}" stroke="#fff"/>')
        else:
            o.append(f'<circle cx="{lx + 6}" cy="{y}" r="5" fill="{c}" stroke="#fff"/>')
        o.append(f'<text x="{lx + 24}" y="{y + 4}" font-size="12" fill="#ddd">{esc(text)}</text>')
    y = 40 + len(rows) * 26 + 14
    lines = [
        'Heights: lagoon 860, fens 900-1,000,',
        'Nightshadow 1,000, camp 1,020, Newcastle',
        "1,750, Crow's Crown 3,450; rim cliff to 0.",
        'Dashed white: the playable square',
        '(cells 19-109; land and trees run on',
        'to the map edge).',
        '',
        f"Hostiles at load {figures['hostiles']}: {figures['markers']} markers",
        f"(slots 2-3 / 2-4 / 2-3) + {figures['placed']} placed.",
        f"Quiet land {figures['quiet_cell_share']:.0%} of cells, "
        f"{figures['quiet_block_share']:.0%} of blocks.",
        f"Roads {figures['road_share']} % of land.",
    ]
    for i, t in enumerate(lines):
        o.append(f'<text x="{lx}" y="{y + i * 17}" font-size="12" fill="#ccc">{esc(t)}</text>')
    o.append('</svg>')
    return '\n'.join(o)


def chrome_png(svg_path, png_path, width, height):
    cmd = ['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
           f'--window-size={width},{height}', f'--screenshot={png_path}', f'file://{svg_path}']
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)


# ------------------------------------------------------------------ blockouts

MODELS = [  # (cell x, cell y, base or None, height, half width cells, colour)
    (64.5, 69.5, None, 2600, 0.8, (70, 70, 78)),        # Tower of High Magic
    (64.5, 69.5, None, 900, 1.6, (84, 80, 76)),         # the islet's rock and the tower's base
    (82, 33.5, None, 260, 3.5, (196, 190, 172)),        # Newcastle ruin (broken walls)
    (79, 31, None, 520, 0.6, (186, 180, 164)),          # a broken corner tower
    (86.5, 42.2, None, 330, 1.0, (178, 120, 60)),       # Ebenezer's tent
    (89.2, 45.7, None, 380, 0.75, (140, 132, 116)),     # the camp shrine
    (99.5, 70, None, 420, 6.0, (70, 66, 62)),           # Nightshadow roofs
    (95.5, 71.5, None, 1100, 0.4, (66, 62, 60)),        # the temple's spire
    (34, 86.5, None, 300, 3.0, (40, 36, 34)),           # the tomb mound
    (98, 25.5, None, 500, 0.5, (110, 104, 96)),         # fallen watchtower
]
ANNOTATIONS = {
    'view:arrival': [
        ("Ebenezer's camp: tent, shrine, fire", 87, 43.5, 300),
        ('Newcastle ruin on its rise', 82, 33.5, 300),
        ('Lagoon Cross signpost', 94, 42.5, 120),
        ('Tower of High Magic (islet)', 64.5, 69.5, 2400),
        ('lagoon', 74, 62, 40),
        ('mist over Nightshadow', 93, 62, 400),
        ('Crow Hills', 92, 30, 200),
    ],
    'view:signature': [
        ('Tower of High Magic', 64.5, 69.5, 2300),
        ('causeway', 64, 61, 60),
        ("Mirabeth's rock", 84.6, 81, 80),
        ('Nightshadow in mist', 98, 70, 500),
        ('temple spire', 95.5, 71.5, 1000),
        ('east ridge', 112, 70, 0),
    ],
}


def main():
    import plan_render as PR
    OUT.mkdir(parents=True, exist_ok=True)
    plan, sketch = L.data()
    height, water, rim = L.build_land(sketch)
    np.save(OUT / 'height.npy', height.astype(np.float32))
    figures, marks = L.measure(plan, sketch, height, water, rim)
    (OUT / 'figures.json').write_text(json.dumps({k: v for k, v in figures.items()}, indent=1, default=list))
    (OUT / 'markers.json').write_text(json.dumps([list(m) for m in marks]))
    img = colour_land(height, water, rim)
    img.save(OUT / 'colour.png')
    svg = svg_plan(OUT / 'colour.png', figures, marks)
    (OUT / 'plan_x3.svg').write_text(svg)
    chrome_png(OUT / 'plan_x3.svg', OUT / 'plan_x3_full.png', 128 * 8 + 60 + 330, 128 * 8 + 90)
    big = Image.open(OUT / 'plan_x3_full.png').convert('RGB')
    big.resize((1600, round(1600 * big.height / big.width)), Image.LANCZOS).save(OUT / 'plan_x3.png')
    for v in G.VIEWS:
        view = dict(v, pitch=-3.0)
        name = v['id'].split(':')[1]
        PR.blockout(height, img, view, MODELS, OUT / f'blockout_{name}.png', fov=80.0,
                    annotations=ANNOTATIONS[v['id']])
    print(figures['summary'])


if __name__ == '__main__':
    main()
