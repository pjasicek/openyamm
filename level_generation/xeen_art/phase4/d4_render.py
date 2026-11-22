#!/usr/bin/env python3
"""MU-3 drawing, MU-4 blockouts, the plan's measurements and the D3 edge match for D4 Lakeside and Blackfang
(A6, phase 4).

    d4_render.py [--no-blockout]   -> phase4/d4/{colour.png, plan_d4.svg, blockout_<view>.png, measure.json,
                                       edge_d3.json}

Reads the brief devdocs/xeen/briefs/d4/L1/{plan,sketch,project}.yml and, for the edge match, D3's installed
heightmap (assets_dev/worlds/xeen/maps/xeen_d3.odm, read only). Reuses phase2/plan_render.py (the SVG plan) and
phase3/d2_render.py (the amber blockout) without editing them. The land drawn here is the drawing's model of the
sketch, not the studio's build. Nothing here is read by the game or the studio.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True      # leave phase2's and phase3's folders untouched
sys.path.insert(0, str(HERE.parent / 'phase2'))
sys.path.insert(0, str(HERE.parent / 'phase3'))
import plan_render as pr  # noqa: E402
import d2_render as d2r  # noqa: E402

ROOT = pr.ROOT
OUT = HERE / 'd4'
RES, N = pr.RES, pr.N
SIZE = N * RES
LAKE_LEVEL = 1056
BOX = (19, 109)             # the playable square, both axes
RIM_N, RIM_E = 24, 104

BAND_BASE = {'band:shore': 1160, 'band:forest': 1450, 'band:heath': 1700, 'band:uplands': 1900, 'band:crag': 1500,
             'band:peaks': 2500}
GROUND = {   # sRGB per plan space (Darkside: desaturated greens, slate, dry heath; MU-2's D4 row)
    'zone:desert_heath': (150, 136, 104),
    'zone:lakeside_brow': (146, 134, 104),
    'zone:forest_of_peril': (62, 76, 58),
    'zone:west_edge': (104, 112, 82),
    'zone:west_shore': (96, 112, 86),
    'zone:magic_mountain': (118, 116, 112),
    'zone:snow_uplands': (196, 200, 204),
    'zone:rim_corner': (176, 178, 176),
    'zone:north_shore': (126, 128, 106),
    'zone:blackfang_crag': (64, 62, 68),
    'zone:east_shore': (118, 124, 96),
    'zone:rimward_crags': (130, 122, 104),
    'zone:isle': (92, 94, 82),
    'town:lakeside': (138, 132, 116),
    'zone:wizard_camp': (130, 124, 108),
    'zone:leafpoint_grove': (88, 108, 74),
    'zone:ector_clearing': (104, 110, 80),
    'zone:woodcutters_clearing': (110, 108, 86),
    'zone:mirabeth_point': (120, 126, 100),
}
ORDER = ['zone:desert_heath', 'zone:lakeside_brow', 'zone:rimward_crags', 'zone:forest_of_peril', 'zone:west_edge',
         'zone:west_shore', 'zone:magic_mountain', 'zone:snow_uplands', 'zone:rim_corner', 'zone:north_shore',
         'zone:east_shore', 'zone:blackfang_crag', 'zone:isle', 'town:lakeside', 'zone:wizard_camp',
         'zone:leafpoint_grove', 'zone:ector_clearing', 'zone:woodcutters_clearing', 'zone:mirabeth_point']
TREES = {   # space: (trees per cell, colour)
    'zone:forest_of_peril': (0.9, (30, 46, 36)),
    'zone:west_shore': (0.35, (44, 62, 46)),
    'zone:west_edge': (0.25, (40, 56, 42)),
    'zone:magic_mountain': (0.12, (40, 56, 46)),
    'zone:desert_heath': (0.06, (60, 70, 52)),
    'zone:snow_uplands': (0.05, (52, 66, 60)),
    'zone:isle': (0.25, (70, 66, 58)),
    'zone:east_shore': (0.08, (48, 62, 46)),
    'zone:north_shore': (0.06, (48, 62, 46)),
}
CLEAR = ['town:lakeside', 'zone:wizard_camp', 'zone:leafpoint_grove', 'zone:ector_clearing',
         'zone:woodcutters_clearing', 'zone:mirabeth_point', 'zone:lakeside_brow']


def load():
    return pr.load('d4')


def rim_profiles(sketch):
    """The rim strips beyond the square's south and west sides as heights per cell along the side (the drawing's
    reading of the sketch's rim forms: a ridge's crest between its two heights, a level stretch at its height)."""
    south = np.zeros(N)
    west = np.zeros(N)
    for r in sketch['frame']['rim']:
        if r['side'] not in ('south', 'west'):
            continue
        a, b = r.get('span', [0, 128])
        for c in range(int(a), int(b)):
            if r['form'] == 'level':
                v = r['height']
            else:
                lo, hi = r['height']
                v = lo + (hi - lo) * (0.5 + 0.5 * math.sin(c / 3.7 + (1.3 if r['side'] == 'west' else 0.4)))
            (south if r['side'] == 'south' else west)[c] = v
    return south, west


def build_land(sketch):
    """Height (map units) per raster pixel from the sketch's bands, points, ridges, rims, water and roads."""
    height = np.full((SIZE, SIZE), 1500.0)
    for band in sketch['heights']['bands']:
        if band['band'] == 'band:rim_sea':
            continue
        height[pr.poly_mask(band['polygon'])] = BAND_BASE[band['band']]
    yy, xx = np.mgrid[0:SIZE, 0:SIZE] / RES
    height = ndimage.gaussian_filter(height, 3 * RES)
    for point in sketch['heights'].get('points', []):
        px, py = point['at']
        r = 7.0 if point['h'] > 3000 else (5.0 if point['h'] > 2000 else 3.5)
        d = np.hypot(xx - px - 0.5, yy - py - 0.5)
        t = np.clip(1 - d / r, 0, 1)
        w = t * t * (3 - 2 * t)
        height = height * (1 - w) + point['h'] * w
    for ridge in sketch['heights'].get('ridges', []):
        m = pr.line_mask(ridge['line'], ridge.get('width', 2))
        dist = ndimage.distance_transform_edt(~m) / RES
        w = np.clip(1 - dist / (ridge.get('slope', 3) + 1.5), 0, 1)
        height = np.maximum(height, height * (1 - w) + ridge['height'] * w)
    rng = np.random.default_rng(5)
    noise = ndimage.gaussian_filter(rng.normal(size=(SIZE, SIZE)), 3 * RES)
    noise /= np.abs(noise).max() + 1e-6
    rough = ndimage.gaussian_filter(rng.normal(size=(SIZE, SIZE)), 0.6 * RES)
    rough /= np.abs(rough).max() + 1e-6
    masks = pr.space_masks(sketch)
    calm = np.zeros((SIZE, SIZE), bool)
    for s in CLEAR + ['zone:isle']:
        calm |= masks.get(s, calm)
    calm = ndimage.binary_dilation(calm, iterations=RES)
    steep = np.clip((height - 1600) / 1200, 0, 1)
    height += np.where(calm, 0, noise * 140 + rough * (30 + 300 * steep))
    # flat town and camps
    for space, target in [('town:lakeside', None), ('zone:wizard_camp', 2300), ('zone:woodcutters_clearing', 1900),
                          ('zone:leafpoint_grove', 1500), ('zone:ector_clearing', 1450)]:
        m = masks[space]
        soft = ndimage.gaussian_filter(m.astype(float), RES)
        if target is None:
            # Lakeside: 1,090 on the waterfront rising to 1,200 at its south edge
            target = 1090 + np.clip((yy - 82) / 15, 0, 1) * 110
        height = height * (1 - soft) + target * soft
    # the lake: its shores come down to it (not under Blackfang's crag, whose face is a cliff)
    lake_body = next(b for b in sketch['water']['bodies'] if b['id'] == 'water:octopod_lake')
    lake = pr.poly_mask(lake_body['polygon'])
    crag = masks['zone:blackfang_crag']
    dist = ndimage.distance_transform_edt(~lake) / RES
    cap = LAKE_LEVEL + 30 + 150 * dist
    shore = ~lake & ~crag & (dist < 8)
    height[shore] = np.minimum(height[shore], cap[shore])
    # islets inside the lake: the Isle (its band) and the skerries (height points)
    isle = masks['zone:isle']
    islet = isle.copy()
    for point in sketch['heights']['points']:
        note = point.get('notes') or ''
        if 'Skerry' in note:
            px, py = point['at']
            islet |= np.hypot(xx - px - 0.5, yy - py - 0.5) < 0.9
    water = lake & ~islet
    height[lake & islet] = np.maximum(height[lake & islet], LAKE_LEVEL + 30)
    # deep water: the basins (for the colour only)
    deep = water & (ndimage.distance_transform_edt(water) / RES > 4.5)
    height[water] = LAKE_LEVEL
    # the springs' tarn, the Snow River (rapids from 2,270 to the lake) and the outflow
    for body in sketch['water']['bodies']:
        if body['kind'] == 'pond':
            m = pr.poly_mask(body['polygon'])
            height[m] = body['level']
            water |= m
    for river in sketch['water']['rivers']:
        line = river['line']
        m = pr.line_mask(line, river.get('width_cells', 1.5))
        bank = ndimage.binary_dilation(m, iterations=RES) & ~m
        if river.get('level'):
            height[m] = river['level']
        else:
            seg = [math.dist(a, b) for a, b in zip(line, line[1:])]
            total = sum(seg)
            ys, xs = np.nonzero(m | bank)
            pts = np.array(line, float)
            best_t = np.zeros(len(xs))
            best_d = np.full(len(xs), 1e9)
            acc = 0.0
            for (x0, y0), (x1, y1), L in zip(pts, pts[1:], seg):
                dx, dy = x1 - x0, y1 - y0
                px, py = xs / RES, ys / RES
                t = np.clip(((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy), 0, 1)
                d = np.hypot(px - x0 - t * dx, py - y0 - t * dy)
                better = d < best_d
                best_d[better] = d[better]
                best_t[better] = (acc + t * L)[better] / total
                acc += L
            level = 2270 + (LAKE_LEVEL - 2270) * best_t
            on = m[ys, xs]
            height[ys[on], xs[on]] = level[on]
            off = ~on
            height[ys[off], xs[off]] = np.maximum(level[off] + 60, np.minimum(height[ys[off], xs[off]],
                                                                               level[off] + 260))
        water |= m
    # road beds: soften the land under the roads toward their median
    soft = ndimage.gaussian_filter(height, RES)
    for road in sketch.get('roads', []):
        m = pr.line_mask(road['line'], 1.0) & ~water
        height[m] = soft[m]
    # the rim strips south and west (outside the square): from the border's own height out to the frame's form,
    # a ridge's crest about 10 cells out, a level stretch within its `meet` cells
    south, west = rim_profiles(sketch)
    border_s = height[BOX[1] * RES - 1].copy()
    border_w = height[:, BOX[0] * RES].copy()
    sm = yy >= BOX[1]
    k = np.clip((yy - BOX[1]) / 8.0, 0, 1)
    target = south[np.clip(xx.astype(int), 0, N - 1)]
    blend = border_s[None, :] * (1 - k) + target * k
    height[sm] = blend[sm]
    wm = (xx < BOX[0]) & (yy < BOX[1])
    k = np.clip((BOX[0] - xx) / 8.0, 0, 1)
    target = west[np.clip(yy.astype(int), 0, N - 1)]
    blend = border_w[:, None] * (1 - k) + target * k
    height[wm] = blend[wm]
    # the rim strips get the land's swells too (a picture of land, not stripes)
    outside = (xx < BOX[0]) | (yy >= BOX[1])
    smooth = ndimage.gaussian_filter(height, 1.5 * RES) + noise * 180 + rough * 120
    w = ndimage.gaussian_filter(outside.astype(float), RES)
    height = height * (1 - w) + smooth * w
    # the rim: north (y < 24) and east (x >= 104) fall to the stars
    rim = (yy < RIM_N) | (xx >= RIM_E)
    height[rim] = 0
    water &= ~rim
    return height, water, deep, rim


def colour_land(sketch, height, water, deep, rim, trees=True):
    rgb = np.zeros((SIZE, SIZE, 3))
    rgb[:] = (104, 112, 84)
    masks = pr.space_masks(sketch)
    jitter = ndimage.gaussian_filter(np.random.default_rng(8).normal(size=(SIZE, SIZE)), 1.5 * RES)
    jitter /= np.abs(jitter).max() + 1e-6
    for space in ORDER:
        if space in masks:
            soft = ndimage.gaussian_filter(masks[space].astype(float), 1.6 * RES)
            soft = np.clip(soft + jitter * 0.35 * soft * (1 - soft) * 4, 0, 1)[..., None]
            rgb = rgb * (1 - soft) + np.array(GROUND[space]) * soft
    # snow: high ground and the uplands north of y 38
    yy = np.mgrid[0:SIZE, 0:SIZE][0] / RES
    snow = np.clip((height - 2700) / 500, 0, 1)
    snow = np.maximum(snow, np.clip((40 - yy) / 6, 0, 1) * (height > 1500) * 0.9)
    rgb = rgb * (1 - snow[..., None]) + np.array((222, 226, 232)) * snow[..., None]
    for road in sketch.get('roads', []):
        m = pr.line_mask(road['line'], 0.8 if road.get('width') == 'road' else 0.5)
        rgb[m] = (150, 136, 108) if road.get('width') == 'road' else (130, 120, 96)
    gy, gx = np.gradient(height, 512 / RES)
    slope = np.hypot(gx, gy)
    rock = np.clip((slope - 0.42) * 2.2, 0, 1) * (1 - 0.6 * snow)
    rgb = rgb * (1 - rock[..., None]) + np.array((92, 92, 100)) * rock[..., None]
    rgb[water] = (46, 78, 88)
    rgb[deep & water] = (26, 46, 60)
    beach = ndimage.binary_dilation(water, iterations=int(0.6 * RES)) & ~water & ~rim & (height < LAKE_LEVEL + 120)
    rgb[beach] = rgb[beach] * 0.4 + np.array((168, 156, 124)) * 0.6
    light = np.array([-0.55, -0.65, 0.52])
    nx, ny, nz = -gx * 2.2, -gy * 2.2, np.ones_like(gx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    shade = np.clip(0.55 + 0.6 * (nx * light[0] + ny * light[1] + nz * light[2]) / norm, 0.35, 1.15)
    shade[water] = 1.0
    rgb = rgb * shade[..., None]
    stars = np.zeros((SIZE, SIZE, 3))
    stars[:] = (10, 12, 26)
    rng = np.random.default_rng(3)
    for y, x in rng.integers(0, SIZE, size=(2600, 2)):
        stars[y, x] = rng.integers(140, 255)
    rgb[rim] = stars[rim]
    cliff = ndimage.binary_dilation(~rim, iterations=int(1.2 * RES)) & rim
    rgb[cliff] = (84, 80, 92)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    if not trees:
        return img
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    clear = np.zeros((SIZE, SIZE), bool)
    for space in CLEAR:
        if space in masks:
            clear |= masks[space]
    for road in sketch.get('roads', []):
        clear |= pr.line_mask(road['line'], 1.2)
    for space, (density, colour) in TREES.items():
        if space not in masks:
            continue
        ys, xs = np.nonzero(masks[space][::RES, ::RES])
        for cy, cx in zip(ys, xs):
            for _ in range(rng.poisson(density * 2)):
                x, y = (cx + rng.random()) * RES, (cy + rng.random()) * RES
                hy, hx = int(min(y, SIZE - 1)), int(min(x, SIZE - 1))
                if water[hy, hx] or rim[hy, hx] or clear[hy, hx] or height[hy, hx] > 2700:
                    continue
                s = RES * (0.32 + 0.2 * rng.random())
                draw.polygon([(x, y - s * 1.3), (x + s * 0.7, y + s * 0.5), (x - s * 0.7, y + s * 0.5)],
                             fill=colour)
    return img


# ---------------------------------------------------------------- labels for plan_render.svg_plan

KINDS = {
    'entrance:south_road': 'entrance', 'entrance:west_road': 'entrance', 'entrance:lakeside_square': 'entrance',
    'entrance:lakeside_dock': 'entrance', 'entrance:isle_landing': 'entrance',
    'entrance:dd12_door': 'dungeon', 'entrance:dd20_guild': 'dungeon', 'entrance:dd20_shaft': 'dungeon',
    'entrance:dd23_lair': 'dungeon', 'entrance:blackfang_gate': 'dungeon',
    'poi:beached_boat': 'chest', 'poi:roc_nest': 'chest', 'poi:frozen_pilgrim': 'chest',
    'poi:skerry_strongbox': 'chest', 'poi:roc_hunter': 'chest', 'poi:heath_wagon': 'chest',
    'poi:circle_chest': 'chest', 'poi:hunters_hide': 'chest', 'poi:falls_chest': 'chest',
    'poi:gibbet': 'chest', 'poi:naomi': 'npc', 'poi:slibo': 'npc', 'poi:leafpoint': 'npc', 'poi:ector': 'npc',
    'poi:signposts': 'junction', 'junction:well_fork': 'junction', 'junction:ector_fork': 'junction',
    'junction:snow_bridge': 'junction',
    'landmark:blackfang': 'landmark', 'landmark:isle': 'landmark', 'landmark:magic_mountain': 'landmark',
    'landmark:octopod_falls': 'landmark', 'landmark:rapids': 'landmark',
}
NAMES = {
    'entrance:south_road': 'from D3 Sandcaster (x 88)',
    'entrance:west_road': 'from D5 (y 80)',
    'entrance:lakeside_square': '',
    'entrance:lakeside_dock': 'dock (ferry, caravans)',
    'entrance:isle_landing': 'Isle landing',
    'entrance:dd12_door': 'DD-12 Lost Souls (2 leaves)',
    'entrance:dd20_guild': 'DD-20 via the guild (riddle)',
    'entrance:dd20_shaft': 'DD-20 sewer shaft',
    'entrance:dd23_lair': 'DD-23 Gargoyle Lair',
    'entrance:blackfang_gate': "Blackfang's gate (never opens)",
    'junction:well_fork': '', 'junction:ector_fork': '', 'junction:snow_bridge': '',
    'poi:obelisk': 'Obelisk (Gull Knoll)',
    'poi:fountain_magic': "Xanthus' fountain (+SP)",
    'poi:warding_well': 'Magic Resistance well',
    'poi:fountain_resilience': 'Fountain of Great Resilience',
    'poi:woodpile': "Ector's woodpile",
    'poi:cairn': 'cairn (Q-C24)',
    'poi:mirabeth': 'Mirabeth Point',
    'poi:genie_seat': 'genie lamp',
    'poi:genie_skerry': 'genie lamp (skerry)',
    'poi:witches_circle': "Witches' Circle",
    'poi:reed_cauldron': 'cauldron',
    'poi:beached_boat': '"This boat under repair."',
    'poi:roc_nest': 'roc nest', 'poi:frozen_pilgrim': 'frozen pilgrim', 'poi:skerry_strongbox': 'strongbox',
    'poi:roc_hunter': 'roc-hunter', 'poi:heath_wagon': 'wagon', 'poi:circle_chest': '', 'poi:hunters_hide': "hunters' hide", 'poi:falls_chest': '', 'poi:gibbet': 'gibbet',
    'poi:isle_boat': '', 'poi:animal_trap': 'trap', 'poi:signposts': '', 'poi:mirror': 'mirror',
    'poi:naomi': 'Naomi', 'poi:slibo': 'Slibo', 'poi:leafpoint': 'Leafpoint', 'poi:ector': 'Ector',
    'landmark:blackfang': 'CASTLE BLACKFANG', 'landmark:isle': 'ISLE OF LOST SOULS',
    'landmark:magic_mountain': 'MAGIC MOUNTAIN', 'landmark:octopod_falls': 'Octopod Falls',
    'landmark:rapids': 'rapids',
}
OFFSETS = {
    'entrance:south_road': (10, 16, 'start'),
    'entrance:west_road': (4, -14, 'start'),
    'entrance:lakeside_dock': (10, 16, 'start'),
    'entrance:isle_landing': (10, 14, 'start'),
    'entrance:dd12_door': (10, -8, 'start'),
    'entrance:dd20_guild': (-8, -10, 'end'),
    'entrance:dd20_shaft': (-10, 6, 'end'),
    'entrance:dd23_lair': (10, -8, 'start'),
    'entrance:blackfang_gate': (-10, 18, 'end'),
    'poi:obelisk': (-10, 4, 'end'),
    'poi:fountain_magic': (10, -6, 'start'),
    'poi:warding_well': (0, 20, 'middle'),
    'poi:fountain_resilience': (-10, -8, 'end'),
    'poi:woodpile': (10, 4, 'start'),
    'poi:cairn': (10, 4, 'start'),
    'poi:mirabeth': (10, 12, 'start'),
    'poi:genie_seat': (10, -6, 'start'),
    'poi:genie_skerry': (10, -6, 'start'),
    'poi:witches_circle': (-10, 16, 'end'),
    'poi:reed_cauldron': (-10, 4, 'end'),
    'poi:beached_boat': (8, -10, 'start'),
    'poi:skerry_strongbox': (-10, 4, 'end'),
    'poi:roc_hunter': (10, 4, 'start'),
    'poi:mirror': (8, -8, 'start'),
    'poi:naomi': (8, 12, 'start'),
    'poi:slibo': (-10, 4, 'end'),
    'poi:leafpoint': (10, -6, 'start'),
    'poi:ector': (-10, 4, 'end'),
    'landmark:blackfang': (12, -12, 'start'),
    'landmark:isle': (-12, -14, 'end'),
    'landmark:magic_mountain': (12, -12, 'start'),
    'landmark:octopod_falls': (-10, -12, 'end'),
    'landmark:rapids': (-10, 4, 'end'),
}
ENCOUNTERS = {
    'pop:mountain_gargoyles': {'colour': '#8a3c00'},
    'pop:snow_rocs': {'colour': '#c0282d'},
    'pop:rimward_rocs': {'colour': '#c0282d'},
    'pop:heath_rocs': {'colour': '#c0282d'},
    'pop:circle_witches': {'colour': '#8a3cc0'},
    'pop:reed_witches': {'colour': '#8a3cc0'},
    'pop:octopods': {'colour': '#0b5a8a'},
    'pop:octopods_east': {'colour': '#0b5a8a'},
}
CAPTIONS = [
    ('E1 Magic Mountain gargoyles: 32 (30-45)', (44, 27.0), 13, '#5a2400'),
    ('E2 Snow River uplands, rocs: 24 (30-48)', (78, 25.2), 13, '#7a1010'),
    ('E3 Rimward crags: 16', (98, 112.5), 12, '#7a1010'),
    ('E5 the desert edge, rocs: 28 (30-48)', (38, 106.6), 13, '#7a1010'),
    ("E4a Witches' Circle: 8 placed", (50, 96.2), 11.5, '#5a1a80'),
    ('E4b reed witches: 6 placed', (52.5, 62.2), 11.5, '#5a1a80'),
    ('E6 octopods (deep water): 5 placed', (82, 79.6), 12, '#0b3a6a'),
    ('OCTOPOD LAKE (1,056)', (88, 64.6), 15, '#d8eef4'),
    ('THE FOREST OF PERIL', (30, 63), 15, '#eef'),
    ('LAKESIDE', (64, 99.6), 15, '#222'),
    ('Snow River', (63.5, 41.5), 12, '#123'),
    ('the snowfield', (72, 28.6), 12, '#345'),
    ('the world rim: a cliff above the stars', (60, 14), 15, '#ccd'),
    ('rim', (116, 64), 15, '#ccd'),
    ('the bright face glows above the north-east rim (sky)', (88, 9), 12, '#e9c46a'),
    ('to D3 (south edge, x 88)', (88, 125), 12, '#fff'),
    ('to D5 (west edge, y 80)', (9, 78.4), 12, '#fff'),
    ("wizards' camp", (28, 55.4), 11.5, '#222'),
]

# Blockout models: (cell x, cell y, base height or None for the ground, height, half width in cells, colour)
MODELS = [
    # Castle Blackfang on its crag: curtain, keep, towers, bats
    (86, 48, None, 700, 3.4, (48, 48, 58)),
    (86, 47, None, 1500, 1.4, (40, 40, 52)),
    (83, 46.5, None, 1250, 0.7, (44, 44, 56)),
    (89.5, 46.5, None, 1250, 0.7, (44, 44, 56)),
    (84, 50.5, None, 1100, 0.7, (44, 44, 56)),
    (88.5, 50.5, None, 1100, 0.7, (44, 44, 56)),
    (78.5, 53.5, None, 520, 1.2, (52, 50, 58)),         # the gatehouse at the crag's foot
    # the Isle: the ruined round tower, dead trees
    (72, 67, None, 820, 0.45, (90, 88, 84)),
    (72, 73, 1056, 60, 0.3, (110, 96, 74)),               # the Isle's jetty
    # the jetty and the ferry
    (72, 81.5, 1056, 70, 0.35, (120, 108, 84)),
    (71.2, 81.2, 1056, 180, 0.6, (90, 70, 50)),           # the ferry boat, moored behind the signature camera
    # wizards' tents, Leafpoint's tree, the obelisk
    (26.5, 50.5, None, 260, 0.6, (150, 130, 100)),
    (29, 50, None, 260, 0.6, (120, 60, 50)),
    (42, 60.5, None, 1500, 1.4, (52, 70, 46)),
    (57, 80.5, None, 420, 0.2, (150, 150, 140)),
    (94.5, 75.5, None, 260, 0.25, (160, 160, 150)),     # Mirabeth's statue
]

ANNOTATIONS = {
    'view:arrival': [
        ("Lakeside's slate roofs", 72, 89, 300),
        ('ferry jetty', 72, 81, 60),
        ('Isle of Lost Souls, ruined tower', 72, 67, 700),
        ('Castle Blackfang on its crag, bats', 86, 47, 1600),
        ('Magic Mountain, snow (far)', 30, 36, 2500),
        ('road down to Lakeside', 86, 96, 40),
        ('Well Fork, fountain', 87, 96, 80),
        ('lake drains east over the rim', 101, 66, 60),
        ('Rimward crags', 99, 96, 200),
    ],
    'view:signature': [
        ("Isle: ruined round tower, dead trees", 72, 67, 700),
        ('Castle Blackfang, storm of bats', 86, 47, 1600),
        ("sealed gatehouse at the crag's foot", 78, 53, 400),
        ('Snow River rapids, snowfield', 60, 40, 200),
        ('north-east rim: bright face glow (sky)', 100, 32, 900),
        ('deep water: octopods', 80, 58, 0),
        ('east skerry, a lamp', 89, 70, 100),
    ],
}


def house_models(plan, sketch, height):
    buildings = {b['id']: b for s in plan['spaces'] for b in s.get('buildings', []) or []}
    out = []
    for d in sketch['districts']:
        for plot in d.get('plots', []) or []:
            b = buildings[plot['building']]
            front, depth = b['footprint_cells'][(plot.get('index') or 1) - 1]
            wx, wy = (front, depth) if plot['facing'] in 'ns' else (depth, front)
            x, y = plot['at']
            tall = 900 if plot['building'] in ('building:lk_guild', 'building:lk_temple') else 520
            colour = (88, 90, 96) if 'guild' in plot['building'] or 'temple' in plot['building'] else (96, 94, 92)
            out.append((x + wx / 2 - 0.5, y + wy / 2 - 0.5, None, tall, max(wx, wy) / 2, colour))
            out.append((x + wx / 2 - 0.5, y + wy / 2 - 0.5, None, tall + 260, max(wx, wy) / 3, (54, 58, 66)))
    return out


def forest_models(sketch, height, water, rng):
    masks = pr.space_masks(sketch)
    clear = np.zeros((SIZE, SIZE), bool)
    for space in CLEAR:
        if space in masks:
            clear |= masks[space]
    for road in sketch.get('roads', []):
        clear |= pr.line_mask(road['line'], 2.0 if road.get('width') == 'road' else 1.4)
    cameras = [v['at'] for v in sketch['views']]
    out = []
    for space, density in [('zone:forest_of_peril', 0.45), ('zone:west_shore', 0.2), ('zone:west_edge', 0.12),
                           ('zone:magic_mountain', 0.06), ('zone:desert_heath', 0.03), ('zone:isle', 0.15),
                           ('zone:east_shore', 0.05), ('zone:north_shore', 0.04)]:
        ys, xs = np.nonzero(masks[space][::RES, ::RES])
        for cy, cx in zip(ys, xs):
            if rng.random() > density:
                continue
            x, y = cx + rng.random(), cy + rng.random()
            px, py = int(x * RES), int(y * RES)
            if clear[py, px] or water[py, px] or height[py, px] > 2600 or height[py, px] < 10:
                continue
            if any(math.hypot(x - c[0] - 0.5, y - c[1] - 0.5) < 3.0 for c in cameras):
                continue
            g = int(rng.integers(-8, 9))
            dead = space == 'zone:isle'
            col = (70 + g, 64 + g, 56 + g) if dead else (34 + g, 50 + g, 40 + g)
            if dead:
                out.append((x - 0.5, y - 0.5, None, 280 + rng.random() * 200, 0.08 + rng.random() * 0.06, col))
            else:
                out.append((x - 0.5, y - 0.5, None, 600 + rng.random() * 500, 0.35 + rng.random() * 0.2, col))
    return out


# ---------------------------------------------------------------- measurements against MAPS

def poly_distance(poly, x, y):
    best = 1e9
    pts = poly + [poly[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        t = max(0, min(1, ((x - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - x0 - t * dx, y - y0 - t * dy))
    return best


def inside(poly, x, y):
    return bool(pr.poly_mask(poly, scale=4)[int(y * 4), int(x * 4)])


def door_points(plan, sketch):
    buildings = {b['id']: b for s in plan['spaces'] for b in s.get('buildings', []) or []}
    out = []
    for d in sketch['districts']:
        for plot in d.get('plots', []) or []:
            b = buildings[plot['building']]
            front, depth = b['footprint_cells'][(plot.get('index') or 1) - 1]
            wx, wy = (front, depth) if plot['facing'] in 'ns' else (depth, front)
            x, y = plot['at']
            door = {'n': (x + wx / 2, y), 's': (x + wx / 2, y + wy), 'e': (x + wx, y + wy / 2),
                    'w': (x, y + wy / 2)}[plot['facing']]
            out.append((plot['building'] + (f"#{plot['index']}" if plot.get('index') else ''), b['service'], door))
    return out


def census(spots):
    """One point per spot, chained merging within 400 units (D-11.4, D-15): groups of names."""
    parent = list(range(len(spots)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(spots)):
        for j in range(i + 1, len(spots)):
            if math.dist(spots[i][1], spots[j][1]) * 512 <= 400:
                parent[find(i)] = find(j)
    groups = {}
    for i, s in enumerate(spots):
        groups.setdefault(find(i), []).append(s)
    return list(groups.values())


def measure(plan, sketch, project, height, water, rim):
    kinds = {p['id']: p['kind'] for p in plan['points_of_interest']}
    pts = {}
    for p in sketch['points']:
        pts.setdefault(p['id'], []).append(p['at'])
    # land: the playable square above the rims, without water
    small = lambda m: m[RES // 2::RES, RES // 2::RES]
    land = np.zeros((N, N), bool)
    land[BOX[0]:BOX[1], BOX[0]:BOX[1]] = True
    land &= ~small(rim) & ~small(water)
    enc_areas = [a for a in sketch['areas'] if a.get('kind', 'encounter') == 'encounter']
    covered = np.zeros((N, N), bool)
    areas = []
    for a in enc_areas:
        m = pr.poly_mask(a['polygon'], scale=1)
        covered |= m
        cells = int((m & land).sum())
        areas.append({'id': a['id'], 'land_cells': cells, 'big_cells': round(cells / 64, 1),
                      'all_cells': int(m.sum()), 'count': a.get('count', 0)})
    quiet = 1 - (covered & land).sum() / land.sum()
    # hostiles at load
    slots = project['map_stats']['slots']
    avg = {i + 1: sum(s['per_marker']) / 2 for i, s in enumerate(slots)}
    markers = {a['id']: a['count'] for a in enc_areas if a['id'] in ('pop:mountain_gargoyles', 'pop:snow_rocs',
                                                                      'pop:rimward_rocs', 'pop:heath_rocs')}
    by_area = {aid: c * avg[next(a['slot'] for a in enc_areas if a['id'] == aid)] for aid, c in markers.items()}
    placed = [a for a in sketch['actors'] if a.get('hostile')]
    placed_n = sum(a.get('count', 1) for a in placed)
    hostiles = sum(by_area.values()) + placed_n
    # kill XP per member: L(L+10) per monster; marker tiers by Dif (MM7's odds: Dif 1 90/8/2, Dif 2 70/20/10)
    odds = {1: (0.9, 0.08, 0.02), 2: (0.7, 0.2, 0.1)}
    levels = {'Xeen Mountain Gargoyle': (30, 38, 45), 'Xeen Roc': (30, 38, 48), 'Xeen Coven': (32, 40, 50)}
    xp = lambda L: L * (L + 10)
    kill = 0.0
    for aid, n in by_area.items():
        slot = slots[next(a['slot'] for a in enc_areas if a['id'] == aid) - 1]
        o = odds[slot['tier']]
        kill += n * sum(p * xp(L) for p, L in zip(o, levels[slot['monster']]))
    row_level = {'11170': 32, '11171': 40, '11172': 50, '11470': 50, '11471': 60}
    for a in placed:
        kill += a.get('count', 1) * xp(row_level[a['monster']])
    # first fights
    enc_polys = [(a['id'], a['polygon']) for a in enc_areas]
    first = {}
    for e in ('entrance:south_road', 'entrance:west_road', 'entrance:lakeside_square', 'entrance:lakeside_dock',
              'entrance:isle_landing'):
        ex, ey = pts[e][0]
        best = sorted((poly_distance(poly, ex, ey) * 512, aid) for aid, poly in enc_polys)[:2]
        first[e] = [(round(d), n) for d, n in best]
    doors = door_points(plan, sketch)
    door_min = min((poly_distance(poly, x, y) * 512, name, aid) for name, _, (x, y) in doors
                   for aid, poly in enc_polys)
    # POI census (D-20/D-23): devices, chests, dungeon doors, gates, the mirror, service doors; not residences,
    # talking NPCs, hazards, landmarks, junctions or arrivals
    spots = []
    for pid, ats in pts.items():
        if pid.startswith('poi:') and kinds.get(pid) not in ('npc', 'trap'):
            spots += [(pid, tuple(a)) for a in ats]
        elif pid.startswith('entrance:dd') or pid == 'entrance:blackfang_gate':
            spots += [(pid, tuple(a)) for a in ats]
    services = [(name, (x, y)) for name, service, (x, y) in doors if service != 'residence']
    groups = census(spots + services)
    # nearest-neighbour spacing of the census spots (group centres)
    centres = [np.mean([s[1] for s in g], axis=0) for g in groups]
    nn = []
    for i, c in enumerate(centres):
        nn.append(min(math.dist(c, d) for j, d in enumerate(centres) if j != i) * 512)
    # the 6,000 rule (D-11.5): land farther than 6,000 from anything (POIs, doors, NPCs, encounter land)
    anything = np.zeros((N, N), bool)
    for pid, ats in pts.items():
        if pid.startswith(('poi:', 'entrance:')):
            for x, y in ats:
                anything[int(y), int(x)] = True
    for _, _, (x, y) in doors:
        anything[min(int(y), N - 1), min(int(x), N - 1)] = True
    anything |= covered
    dist = ndimage.distance_transform_edt(~anything) * 512
    far = dist * land
    fy, fx = np.unravel_index(int(np.argmax(far)), far.shape)
    wild = float((land & (dist > 3000)).sum() / land.sum())
    # relief inside the box (land)
    box = np.zeros((SIZE, SIZE), bool)
    box[BOX[0] * RES:BOX[1] * RES, BOX[0] * RES:BOX[1] * RES] = True
    landpx = box & ~rim & ~water
    # roads
    roads = np.zeros((SIZE, SIZE), bool)
    lanes = np.zeros((SIZE, SIZE), bool)
    for r in sketch['roads']:
        if r['width'] == 'road':
            roads |= pr.line_mask(r['line'], 1.0)
        else:
            lanes |= pr.line_mask(r['line'], 0.6)
    lake_cells = int(small(pr.poly_mask(next(b for b in sketch['water']['bodies']
                                             if b['id'] == 'water:octopod_lake')['polygon'])).sum())
    chests = [p for p in plan['points_of_interest'] if p['kind'] == 'chest']
    return {
        'land_cells': int(land.sum()), 'lake_cells': lake_cells,
        'water_share_of_box': round(float(small(water)[BOX[0]:BOX[1], BOX[0]:BOX[1]].mean()), 3),
        'quiet_share': round(float(quiet), 3), 'areas': areas,
        'markers': sum(markers.values()), 'hostiles_by_area': by_area, 'placed_hostile': placed_n,
        'hostiles_at_load': round(hostiles, 1), 'kill_xp_per_member': round(kill / 4),
        'height_min_land_box': int(height[landpx].min()), 'height_max_land_box': int(height[landpx].max()),
        'relief_box': int(height[landpx].max() - height[landpx].min()),
        'road_share': round(float((roads & landpx).sum() / landpx.sum()), 3),
        'lane_share': round(float((lanes & landpx & ~roads).sum() / landpx.sum()), 3),
        'first_fight': first,
        'nearest_fight_to_a_town_door': [round(door_min[0]), door_min[1], door_min[2]],
        'poi_spots': len(groups), 'poi_groups': [[s[0] for s in g] for g in groups],
        'poi_spacing_median': round(float(np.median(nn))), 'poi_spacing_min': round(min(nn)),
        'poi_spacing_max': round(max(nn)),
        'service_doors': len(services), 'house_doors': len(doors), 'outdoor_chests': len(chests),
        'dungeon_entrances': sum(1 for p in pts if p.startswith('entrance:dd')),
        'farthest_land_from_anything': [round(float(far.max())), [int(fx), int(fy)]],
        'wild_land_share_over_3000': round(wild, 3),
    }


# ---------------------------------------------------------------- the D3 edge match

def d3_heights():
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_odm_file
    data = parse_odm_file(ROOT / 'assets_dev/worlds/xeen/maps/xeen_d3.odm')
    return np.array(data['payload']['height_map'], int).reshape(N, N) * 32


def edge_match(sketch, height):
    """D3's installed north strip against D4's planned south strip, column by column: D3's border row (y 19) with
    D4's (y 109); and the rows beyond each border (D3 y 0-18 is its picture of D4, D4 y 110-127 its picture of D3)."""
    d3 = d3_heights()
    d4 = height[RES // 2::RES, RES // 2::RES]
    spans = [(r['span'], r['form'], r['height'], r.get('notes', '')) for r in sketch['frame']['rim']
             if r['side'] == 'south']
    rows = {'x': list(range(N)),
            'd3_border_y19': [int(v) for v in d3[19]],
            'd4_border_y109': [int(v) for v in d4[109]],
            'd3_inside_y20_30': [int(v) for v in d3[20:31].mean(axis=0)],
            'd4_inside_y98_108': [int(v) for v in d4[98:109].mean(axis=0)],
            'd3_rim_y0_18': [int(v) for v in d3[0:19].mean(axis=0)],
            'd4_rim_y110_127': [int(v) for v in d4[110:128].mean(axis=0)]}
    table = []
    for (a, b), form, h, notes in spans:
        sl = slice(int(a), int(b))
        b3 = np.array(rows['d3_border_y19'][sl])
        b4 = np.array(rows['d4_border_y109'][sl])
        table.append({'span': [a, b], 'form': form, 'height': h, 'notes': notes,
                      'd3_border_mean': int(b3.mean()), 'd4_border_mean': int(b4.mean()),
                      'mean_abs_diff': int(np.abs(b3 - b4).mean()), 'max_abs_diff': int(np.abs(b3 - b4).max())})
    road = {'d3_at_x88_y19': int(d3[19, 88]), 'd4_at_x88_y109': int(d4[109, 88]), 'd3_edge_spans': (
        "D3 L4 frame.rim north: [0,24] ridge 2600-3400; [24,82] ridge 1500-2000; [82,94] level 1750; "
        "[94,104] ridge 1900-2400; [104,128] level 0")}
    return {'rows': rows, 'spans': table, 'road': road}


def main():
    plan, sketch, project = load()
    OUT.mkdir(exist_ok=True)
    height, water, deep, rim = build_land(sketch)
    img = colour_land(sketch, height, water, deep, rim)
    img.save(OUT / 'colour.png')
    labels = {'kinds': KINDS, 'names': NAMES, 'offsets': OFFSETS,
              'arrows': {'entrance:south_road': True, 'entrance:west_road': True}, 'encounters': ENCOUNTERS,
              'captions': CAPTIONS}
    pr.HERE = HERE            # svg_plan reads <HERE>/<key>/colour.png: point it at phase4
    svg = pr.svg_plan('d4', plan, sketch, project, labels, extra_svg(8, sketch))
    (OUT / 'plan_d4.svg').write_text(svg)
    if '--no-blockout' not in sys.argv:
        bare = colour_land(sketch, height, water, deep, rim, trees=False)
        models = MODELS + house_models(plan, sketch, height) + forest_models(sketch, height, water,
                                                                            np.random.default_rng(21))
        pitch = {'view:arrival': -7.0, 'view:signature': 1.0}
        fovs = {'view:arrival': 76.0, 'view:signature': 60.0}
        for view in sketch['views']:
            name = view['id'].split(':')[1]
            d2r.blockout(height, bare, view, models, OUT / f'blockout_{name}.png', fov=fovs[view['id']],
                         annotations=ANNOTATIONS.get(view['id']), pitch=pitch.get(view['id'], -3.0))
    result = measure(plan, sketch, project, height, water, rim)
    (OUT / 'measure.json').write_text(json.dumps(result, indent=1))
    edge = edge_match(sketch, height)
    (OUT / 'edge_d3.json').write_text(json.dumps(edge, indent=1))
    show = {k: v for k, v in result.items() if k != 'poi_groups'}
    print(json.dumps(show, indent=1))
    for g in result['poi_groups']:
        print('  ', ', '.join(g))
    for s in edge['spans']:
        print('edge', s['span'], s['form'], s['d3_border_mean'], s['d4_border_mean'], s['mean_abs_diff'])
    print('road', edge['road'])


def extra_svg(scale, sketch):
    """The signature camera (plan_render draws only the arrival's), the Isle's ferry line and the bats' storm."""
    s = scale
    parts = []
    for view in sketch['views']:
        if view['id'] != 'view:signature':
            continue
        x, y = view['at']
        lx, ly = view['look']
        ang = math.atan2(ly - y, lx - x)
        dist = math.hypot(lx - x, ly - y)
        p1 = (x + math.cos(ang - math.radians(35)) * dist, y + math.sin(ang - math.radians(35)) * dist)
        p2 = (x + math.cos(ang + math.radians(35)) * dist, y + math.sin(ang + math.radians(35)) * dist)
        col = '#1f6fd1'
        parts.append(f'<polygon points="{pr.pts([(x + .5, y + .5), p1, p2], s)}" fill="{col}" fill-opacity="0.12" '
                     f'stroke="{col}" stroke-width="1.5" stroke-dasharray="6 4"/>')
        parts.append(f'<line x1="{(x + .5) * s}" y1="{(y + .5) * s}" x2="{(lx + .5) * s}" y2="{(ly + .5) * s}" '
                     f'stroke="{col}" stroke-width="2"/>')
        parts.append(f'<circle cx="{(x + .5) * s}" cy="{(y + .5) * s}" r="6" fill="{col}" stroke="#fff" '
                     'stroke-width="1.5"/>')
    # the ferry route (route 420) and the bats over Blackfang
    parts.append(f'<line x1="{72.5 * s}" y1="{82 * s}" x2="{72.5 * s}" y2="{73.5 * s}" stroke="#f4e3b0" '
                 'stroke-width="2" stroke-dasharray="3 4"/>')
    rng = np.random.default_rng(4)
    for _ in range(60):
        a = rng.random() * 2 * math.pi
        r = 2.5 + rng.random() * 4.5
        bx, by = (86.5 + math.cos(a) * r) * s, (48 + math.sin(a) * r * 0.8) * s
        parts.append(f'<path d="M{bx - 3:.1f},{by:.1f} q1.5,-2 3,0 q1.5,-2 3,0" fill="none" stroke="#111" '
                     'stroke-width="1.1"/>')
    # the castle's footprint on the crag (L3 lays it out)
    parts.append(f'<rect x="{82.5 * s}" y="{45 * s}" width="{8 * s}" height="{6.5 * s}" fill="#2a2a34" '
                 'fill-opacity="0.85" stroke="#000" stroke-width="1.2"/>')
    for tx, ty in [(82.5, 45), (90.5, 45), (82.5, 51.5), (90.5, 51.5)]:
        parts.append(f'<circle cx="{tx * s}" cy="{ty * s}" r="{0.9 * s}" fill="#22222c" stroke="#000"/>')
    # the Isle's ruined tower
    parts.append(f'<circle cx="{72.5 * s}" cy="{67.5 * s}" r="{1.0 * s}" fill="#6a6660" stroke="#222"/>')
    return '\n'.join(parts)


if __name__ == '__main__':
    main()
