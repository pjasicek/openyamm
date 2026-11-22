#!/usr/bin/env python3
"""MU-3 drawing, MU-4 blockouts and the plan's measurements for D1 Castleview Vale (A6, phase 3).

    d1_render.py          -> phase3/d1/{colour.png, plan_d1.svg, plan_d1.png, blockout_<view>.png, measure.json}

Reads the brief devdocs/xeen/briefs/d1/L1/{plan,sketch,project}.yml. Reuses phase2/plan_render.py (the SVG plan) without
editing it: its module folder is pointed at phase3 for the colour picture. The land, its colours and the blockout's
amber sky are D1's own here. Nothing here is read by the game or the studio.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True      # leave phase2's folder untouched
sys.path.insert(0, str(HERE.parent / 'phase2'))
import plan_render as pr  # noqa: E402

pr.HERE = HERE            # svg_plan reads HERE/<key>/colour.png
OUT = HERE / 'd1'
RES = pr.RES
N = pr.N
BRIEF = pr.ROOT / 'devdocs/xeen/briefs/d1/L1'

BAND_BASE = {'band:rim_sea': 0, 'band:vale': 1080, 'band:rise': 1500, 'band:hills': 2300}
GROUND = {   # sRGB per plan space: Darkside's desaturated greens, slate and dry grass (WORLD_DESIGN 4, MU-2 D1 row)
    'wild:north_hills': (124, 116, 100),
    'wild:gemstone_foothills': (132, 124, 104),
    'wild:siege_lines': (138, 130, 98),
    'wild:sardaj_lands': (142, 138, 100),
    'wild:east_road_camp': (140, 132, 100),
    'wild:dark_grove': (74, 86, 62),
    'wild:west_heath': (138, 126, 104),
    'zone:gemsmiths_row': (146, 136, 112),
    'zone:kalindra_rise': (136, 144, 108),
    'zone:luna_grove': (120, 140, 98),
    'zone:rim_headland': (128, 140, 100),
    'zone:melon_field': (122, 108, 72),
    'wild:south_meadows': (150, 148, 100),
    'wild:south_bank': (126, 138, 98),
    'zone:pyramid_knoll': (134, 138, 104),
    'zone:gate_yard': (150, 140, 116),
    'town:castleview': (168, 162, 152),
}
DEFAULT_GROUND = (124, 138, 96)
TREES = {  # space: (trees per cell, colour)
    'wild:dark_grove': (0.75, (34, 48, 36)),
    'wild:west_heath': (0.05, (70, 84, 60)),
    'zone:luna_grove': (0.6, (150, 160, 130)),
    'wild:south_bank': (0.08, (70, 90, 60)),
    'wild:south_meadows': (0.04, (70, 90, 60)),
    'wild:sardaj_lands': (0.04, (70, 84, 60)),
    'wild:east_road_camp': (0.05, (70, 84, 60)),
    'zone:kalindra_rise': (0.05, (70, 90, 60)),
    'wild:gemstone_foothills': (0.08, (66, 80, 58)),
}
TOWN_POLY = [[51, 47], [55, 44], [71, 44], [75, 47], [76, 55], [74, 62], [70, 65], [56, 65], [52, 62], [49, 55]]


def load():
    read = lambda name: yaml.safe_load((BRIEF / name).read_text())
    return read('plan.yml'), read('sketch.yml'), read('project.yml')


def build_land(sketch):
    """Height (map units) per raster pixel from the sketch's bands, points, ridges, cliffs and water (drawings only)."""
    size = N * RES
    height = np.full((size, size), 1080.0)
    for band in sketch['heights']['bands']:
        if band['band'] == 'band:rim_sea':
            continue
        height[pr.poly_mask(band['polygon'])] = BAND_BASE[band['band']]
    height = ndimage.gaussian_filter(height, 3 * RES)
    yy, xx = np.mgrid[0:size, 0:size] / RES
    for point in sketch['heights'].get('points', []):
        px, py = point['at']
        r = 7.0 if point['h'] > 2400 else 3.5
        d = np.hypot(xx - px - 0.5, yy - py - 0.5)
        t = np.clip(1 - d / r, 0, 1)
        w = t ** 2 * (3 - 2 * t)
        height = height * (1 - w) + point['h'] * w
    for ridge in sketch['heights'].get('ridges', []):
        m = pr.line_mask(ridge['line'], ridge.get('width', 2))
        dist = ndimage.distance_transform_edt(~m) / RES
        w = np.clip(1 - dist / (ridge.get('slope', 3) + 2), 0, 1)
        height = np.maximum(height, height * (1 - w) + ridge['height'] * w)
    rng = np.random.default_rng(7)
    noise = ndimage.gaussian_filter(rng.normal(size=(size, size)), 3 * RES)
    noise /= np.abs(noise).max() + 1e-6
    rough = ndimage.gaussian_filter(rng.normal(size=(size, size)), 0.6 * RES)
    rough /= np.abs(rough).max() + 1e-6
    town = pr.poly_mask(TOWN_POLY)
    calm = ndimage.binary_dilation(town, iterations=3 * RES)
    steep = np.clip((height - 1700) / 1200, 0, 1)
    height += np.where(calm, 0, noise * 140 + rough * (30 + 300 * steep))
    soft = ndimage.gaussian_filter(town.astype(float), RES)
    height = height * (1 - soft) + 1150 * soft
    # Kalindra's south cliff and the mill gorge: the cliffs as steps down to the river side
    water = np.zeros((size, size), bool)
    acid = np.zeros((size, size), bool)
    for body in sketch['water']['bodies']:
        if body['id'] == 'water:rim_sea':
            continue
        m = pr.poly_mask(body['polygon'])
        height[m] = body['level']
        acid |= m
    for river in sketch['water']['rivers']:
        m = pr.line_mask(river['line'], river.get('width_cells', 2))
        bank = ndimage.binary_dilation(m, iterations=int(1.5 * RES))
        gorge = pr.poly_mask([[76, 38], [86, 38], [86, 52], [76, 52]])
        level = 830
        near = ndimage.gaussian_filter(m.astype(float), 1.2 * RES)
        height = height * (1 - np.clip(near * 1.6, 0, 1)) + (level + 40) * np.clip(near * 1.6, 0, 1)
        height[bank] = np.minimum(height[bank], level + 140)
        deep = ndimage.binary_dilation(m, iterations=int(0.6 * RES)) & gorge
        height[deep] = level - 40
        height[m] = level
        water |= m
    rim = pr.poly_mask([[0, 0], [24, 0], [24, 104], [128, 104], [128, 128], [0, 128]])
    height[rim] = 0
    return height, water, acid, rim


def colour_land(sketch, height, water, acid, rim, trees=True):
    size = N * RES
    rgb = np.zeros((size, size, 3))
    rgb[:] = DEFAULT_GROUND
    masks = pr.space_masks(sketch)
    jitter = ndimage.gaussian_filter(np.random.default_rng(8).normal(size=(size, size)), 1.5 * RES)
    jitter /= np.abs(jitter).max() + 1e-6
    for space, colour in GROUND.items():
        if space not in masks:
            continue
        soft = ndimage.gaussian_filter(masks[space].astype(float), 1.5 * RES)
        soft = np.clip(soft + jitter * 0.35 * soft * (1 - soft) * 4, 0, 1)[..., None]
        rgb = rgb * (1 - soft) + np.array(colour) * soft
    gy, gx = np.gradient(height, 512 / RES)
    slope = np.hypot(gx, gy)
    rock = np.clip((slope - 0.40) * 2.2, 0, 1)
    rock = np.maximum(rock, np.clip((height - 2600) / 600, 0, 0.7))
    rgb = rgb * (1 - rock[..., None]) + np.array((108, 104, 104)) * rock[..., None]
    light = np.array([-0.55, -0.65, 0.52])
    nx, ny = -gx * 2.2, -gy * 2.2
    norm = np.sqrt(nx * nx + ny * ny + 1)
    shade = (nx * light[0] + ny * light[1] + light[2]) / norm
    rgb = rgb * np.clip(0.55 + 0.6 * shade, 0.35, 1.15)[..., None]
    rgb[water] = (60, 86, 92)
    rgb[acid] = (120, 150, 60)
    stars = np.zeros((size, size, 3))
    stars[:] = (10, 12, 26)
    rng = np.random.default_rng(3)
    for y, x in rng.integers(0, size, size=(2200, 2)):
        stars[y, x] = rng.integers(140, 255)
    rgb[rim] = stars[rim]
    cliff = ndimage.binary_dilation(~rim, iterations=int(1.2 * RES)) & rim
    rgb[cliff] = (92, 88, 96)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    if not trees:
        return img
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    for space, (density, colour) in TREES.items():
        if space not in masks:
            continue
        ys, xs = np.nonzero(masks[space][::RES, ::RES])
        for cy, cx in zip(ys, xs):
            for _ in range(rng.poisson(density * 2)):
                x, y = (cx + rng.random()) * RES, (cy + rng.random()) * RES
                hy, hx = int(min(y, size - 1)), int(min(x, size - 1))
                if water[hy, hx] or acid[hy, hx] or rim[hy, hx] or height[hy, hx] > 2500:
                    continue
                s = RES * (0.35 + 0.25 * rng.random())
                draw.ellipse((x - s * 0.7, y - s * 0.7, x + s * 0.7, y + s * 0.7), fill=colour)
    return img


# ---------------------------------------------------------------- labels for plan_render.svg_plan

KINDS = {
    'entrance:east_road': 'entrance', 'entrance:north_road': 'entrance', 'entrance:castleview_pyramid': 'entrance',
    'entrance:castleview_square': 'entrance', 'entrance:castleview_temple': 'entrance',
    'entrance:castleview_stables': 'entrance', 'entrance:kalindra_gate': 'entrance', 'entrance:north_gate': 'entrance',
    'entrance:lucio_jetty': 'entrance',
    'entrance:dd01_hatch': 'dungeon', 'entrance:dd02_tower': 'dungeon', 'entrance:dd03_gate': 'dungeon',
    'entrance:dd04_burrow': 'dungeon', 'entrance:dd05_rope': 'dungeon', 'entrance:dd05_door': 'dungeon',
    'entrance:dd10a_adit': 'dungeon', 'entrance:grove_rope': 'dungeon',
    'poi:burned_mill': 'chest', 'poi:shipwreck': 'chest', 'poi:besiegers_camp': 'chest', 'poi:heretic_pack': 'chest',
    'poi:webbed_pack': 'chest', 'poi:runaway_chest': 'chest', 'poi:storage_numbers': 'chest',
    'poi:storage_letters': 'chest',
    'poi:sardaj_camp': 'camp',
    'poi:joe_stall': 'npc', 'poi:justine_camp': 'npc', 'poi:yog': 'npc', 'poi:luna': 'npc',
    'poi:signposts': 'junction',
    'landmark:castleview_walls': 'landmark', 'landmark:ellinger_tower': 'landmark', 'landmark:pyramid': 'landmark',
    'landmark:grove_tree': 'landmark', 'landmark:western_tower': 'landmark', 'landmark:kalindra': 'landmark',
    'landmark:broken_bridge': 'landmark', 'landmark:falls': 'landmark', 'landmark:sardaj_horn': 'landmark',
}
for j in ['gate_fork', 'mill_fork', 'east_bridge', 'east_fork', 'pond_fork', 'west_fork', 'heath_fork', 'south_fork',
          'shrine_fork']:
    KINDS['junction:' + j] = 'junction'

NAMES = {
    'entrance:east_road': 'from D2 (east road, y 60)',
    'entrance:north_road': 'from D6 (mountain road, x 64)',
    'entrance:castleview_pyramid': 'ARRIVAL: pyramid from Vertigo',
    'entrance:kalindra_gate': 'Kalindra gate (TP)',
    'entrance:north_gate': 'North gate (pass)',
    'entrance:dd01_hatch': 'DD-01 sewer',
    'entrance:dd02_tower': 'DD-02 Ellinger',
    'entrance:dd03_gate': 'DD-03 Castle Kalindra (ghost)',
    'entrance:dd04_burrow': 'DD-04 burrow',
    'entrance:dd05_rope': "DD-05 heretics' rope (N wall)",
    'entrance:dd05_door': 'DD-05 front door',
    'entrance:dd10a_adit': 'DD-10 mines (west)',
    'entrance:grove_rope': 'rope to the sky (D7)',
    'entrance:lucio_jetty': "Lucio's Jetty (wall top, M30)",
    'junction:gate_fork': 'Gate fork', 'junction:east_bridge': 'East Bridge', 'junction:west_fork': 'West fork',
    'junction:south_fork': 'South fork', 'junction:heath_fork': 'Heath fork',
    'poi:obelisk': 'Obelisk (DIG)',
    'poi:gate_notice': "Mayor's notice",
    'poi:joe_stall': "Joe's stall + sign",
    'poi:justine_camp': "Justine's camp (passes)",
    'poi:broken_bridge': 'cut rope bridge',
    'poi:burned_mill': 'burned mill',
    'poi:acid_pond': 'Acid Pond',
    'poi:sardaj_camp': 'Sardaj camp (Yog)',
    'poi:luna': "Luna's grove",
    'poi:falista_hut': "Falista's hut",
    'poi:prayer_shrine': 'Prayer shrine (+10 stats)',
    'poi:shipwreck': "Castaway's wreck",
    'poi:might_well': 'Well of Might (+2 perm.)',
    'poi:melon_patch': 'Wild melons (3)',
    'poi:melon_field': "Pip's melon field (1)",
    'poi:besiegers_camp': "Besiegers' camp, trebuchet",
    'poi:wayside_shrine': 'Wayside shrine',
    'poi:edge_stone': 'Edge Stone',
    'poi:west_well': 'Old west well',
    'poi:bottle': 'Bottle message',
    'poi:falls': 'the falls',
    'landmark:western_tower': 'WESTERN TOWER',
    'landmark:kalindra': 'CASTLE KALINDRA (ghost)',
    'landmark:sardaj_horn': 'Sardaj Horn 3,600',
}

OFFSETS = {
    'entrance:castleview_pyramid': (12, -12, 'start'),
    'entrance:north_road': (12, 4, 'start'),
    'entrance:east_road': (0, -16, 'middle'),
    'entrance:kalindra_gate': (12, 4, 'start'),
    'entrance:north_gate': (10, 16, 'start'),
    'entrance:dd03_gate': (-10, 20, 'end'),
    'entrance:dd04_burrow': (12, -4, 'start'),
    'entrance:dd05_rope': (10, -8, 'start'),
    'entrance:dd05_door': (-10, 16, 'end'),
    'entrance:dd10a_adit': (10, -6, 'start'),
    'entrance:grove_rope': (-10, 20, 'end'),
    'entrance:lucio_jetty': (-10, 4, 'end'),
    'entrance:dd02_tower': (-4, 22, 'middle'),
    'entrance:dd01_hatch': (10, 12, 'start'),
    'junction:gate_fork': (10, -8, 'start'),
    'junction:east_bridge': (-6, 18, 'end'),
    'junction:west_fork': (-10, -8, 'end'),
    'junction:south_fork': (10, -6, 'start'),
    'junction:heath_fork': (-10, 4, 'end'),
    'junction:pond_fork': (-8, -8, 'end'),
    'poi:gate_notice': (-10, 2, 'end'),
    'poi:joe_stall': (10, -6, 'start'),
    'poi:justine_camp': (-10, 4, 'end'),
    'poi:broken_bridge': (14, 4, 'start'),
    'poi:burned_mill': (12, 10, 'start'),
    'poi:acid_pond': (10, -6, 'start'),
    'poi:west_well': (-10, 14, 'end'),
    'poi:heretic_pack': (-10, 4, 'end'),
    'poi:edge_stone': (10, 4, 'start'),
    'poi:prayer_shrine': (-10, 4, 'end'),
    'poi:falista_hut': (-10, 4, 'end'),
    'poi:falls': (10, -4, 'start'),
    'poi:wayside_shrine': (-6, -10, 'end'),
    'landmark:kalindra': (0, -26, 'middle'),
    'landmark:western_tower': (-10, -6, 'end'),
    'landmark:grove_tree': (10, -6, 'start'),
}

ARROWS = {'entrance:east_road': True, 'entrance:north_road': True}

ENCOUNTERS = {
    'pop:siege_north': {'colour': '#c0282d'}, 'pop:east_road_camp': {'colour': '#c0282d'},
    'pop:grove_arachnoids': {'colour': '#8a1c5a'}, 'pop:grove_electrapedes': {'colour': '#8a1c5a'},
    'pop:west_heath': {'colour': '#8a1c5a'}, 'pop:centipede_meadows': {'colour': '#b05a00'},
    'pop:foothills': {'colour': '#b05a00'},
}

CAPTIONS = [
    ('E1 Siege lines: 27 gremlins (14-22)', (71, 25.2), 13, '#7a1010'),
    ("E2 Besiegers' camp: 24 gremlins", (94, 76.5), 13, '#7a1010'),
    ('E3 Dark Grove: 21 arachnoids + 7 electrapedes', (46.5, 29.8), 13, '#5a0a3a'),
    ('E3 West heath: 18 arachnoids', (31.5, 58.6), 13, '#5a0a3a'),
    ('E4 Centipede meadows: 25 crawlers (16-26)', (84, 104.8), 13, '#7a3a00'),
    ('E5 Foothills: 13 crawlers', (103, 53.4), 13, '#7a3a00'),
    ('CASTLEVIEW', (63, 66.8), 17, '#222'),
    ('Sardaj lands (quiet)', (90, 33), 12, '#234'),
    ('the Vale Water', (64, 81.5), 13, '#123'),
    ('south bank (quiet)', (44, 101), 12, '#234'),
    ('the world rim:', (11, 52), 13, '#ccd'),
    ('a cliff above', (11, 54), 13, '#ccd'),
    ('the stars', (11, 56), 13, '#ccd'),
    ('the world rim', (80, 112), 13, '#ccd'),
    ('to D6 (north edge, x 64)', (64, 3), 12, '#222'),
    ('mill gorge', (85, 51), 12, '#123'),
]

# Blockout models: (cell x, cell y, base height or None for the ground, height, half width in cells, colour)
WALL = (104, 102, 98)


def wall_models():
    out = []
    pts = TOWN_POLY + [TOWN_POLY[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) * 2))
        for i in range(n):
            t = (i + 0.5) / n
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 1150, 560, 0.32, WALL))
        out.append((x1, y1, 1150, 780, 0.6, (96, 94, 92)))       # a square tower at each corner
    out.append((63, 44, 1150, 900, 1.3, (92, 90, 88)))            # the gatehouse
    return out


def house_models(plan, sketch):
    buildings = {}
    for space in plan['spaces']:
        for b in space.get('buildings', []) or []:
            buildings[b['id']] = b
    out = []
    for d in sketch['districts']:
        for plot in d.get('plots', []) or []:
            b = buildings[plot['building']]
            front, depth = b['footprint_cells'][(plot.get('index') or 1) - 1]
            wx, wy = (front, depth) if plot['facing'] in 'ns' else (depth, front)
            x, y = plot['at']
            big = b['service'] not in ('residence',)
            out.append((x + wx / 2, y + wy / 2, None, 700 if big else 520, max(wx, wy) / 2, (78, 76, 80)))
    return out


def models(plan, sketch):
    out = wall_models() + house_models(plan, sketch)
    out += [
        (71, 47.5, None, 1700, 1.0, (64, 60, 66)),                 # Ellinger's tower
        (71.5, 59, None, 1000, 1.5, (84, 82, 86)),                 # the temple
        (60, 36, None, 450, 1.7, (150, 136, 108)),                 # the travel pyramid, stepped
        (60, 36, None, 750, 1.1, (150, 136, 108)),
        (60, 36, None, 1000, 0.5, (150, 136, 108)),
        (79.4, 43, 1100, 320, 0.12, (70, 56, 40)),                 # the cut bridge's posts
        (82.6, 43, 1100, 320, 0.12, (70, 56, 40)),
        (79, 46.4, None, 520, 0.8, (52, 42, 36)),                  # the burned mill
        (47, 35, None, 2700, 0.9, (36, 44, 34)),                   # the great tree
        (31, 33, None, 2300, 0.9, (52, 50, 58)),                   # the Western Tower
        (40, 70, None, 1300, 2.6, (206, 206, 222)),                # Castle Kalindra, the ghost (pale)
        (40, 70.5, None, 1900, 1.0, (206, 206, 222)),              # its keep
        (36.5, 66.5, None, 1600, 0.7, (210, 210, 226)),
        (43.5, 66.5, None, 1500, 0.7, (210, 210, 226)),
        (36.5, 74, None, 1500, 0.7, (210, 210, 226)),
        (43.5, 74, None, 1500, 0.7, (210, 210, 226)),
        (66, 41, None, 260, 0.5, (120, 80, 50)),                   # Joe's stall
        (57, 41, None, 220, 0.5, (110, 100, 80)),                  # Justine's lean-to
        (88, 25, None, 300, 2.0, (130, 108, 80)),                  # the Sardaj tents
        (96, 63, None, 700, 0.6, (90, 70, 50)),                    # the wrecked trebuchet
        (52, 90, None, 380, 0.4, (160, 150, 130)),                 # the prayer shrine
    ]
    # the besiegers' stakes and mantlets in a broken ring 5-7 cells off the north and east walls
    for ang in range(200, 361, 9):
        a = math.radians(ang)
        out.append((63 + math.cos(a) * 15, 54 + math.sin(a) * 13, None, 160, 0.12, (90, 72, 50)))
    return out


ANNOTATIONS = {
    'view:arrival': [
        ('north gate, gatehouse', 63, 44, 900),
        ('low walls, square towers', 56, 45, 600),
        ("Ellinger's tower", 71, 47.5, 1700),
        ('cut rope bridge over the gorge', 81, 43, 200),
        ('burned mill', 79, 46.4, 500),
        ("besiegers' trenches, stakes", 69, 41.5, 100),
        ("Joe's stall", 66, 41, 260),
        ('the Vale Water in its gorge', 81, 50, 0),
        ('Sardaj lands beyond', 92, 40, 300),
    ],
    'view:signature': [
        ('Castle Kalindra: a translucent ghost', 40, 70, 2000),
        ('the great tree, a rope into the sky', 47, 35, 2700),
        ('Castleview walls', 63, 62, 600),
        ('the Vale Water below the rise', 45, 81, 0),
        ("castaway's wreck", 53, 83, 100),
        ('Dark Grove', 44, 38, 300),
        ('Western Tower', 31, 33, 2300),
    ],
}


def extra_svg(scale, sketch):
    s = scale
    out = []
    # Castleview's walls, the gatehouse and the towers
    pts = ' '.join(f'{x * s},{y * s}' for x, y in TOWN_POLY)
    out.append(f'<polygon points="{pts}" fill="none" stroke="#3a3836" stroke-width="5" stroke-linejoin="round"/>')
    for x, y in TOWN_POLY:
        out.append(f'<rect x="{x * s - 5}" y="{y * s - 5}" width="10" height="10" fill="#4a4846" stroke="#ddd"/>')
    out.append(f'<rect x="{62.2 * s}" y="{43.4 * s}" width="{1.6 * s}" height="{1.2 * s}" fill="#4a4846" stroke="#fff" stroke-width="1.5"/>')
    # Lucio's jetty on the wall top
    out.append(f'<rect x="{46 * s}" y="{54.7 * s}" width="{3.5 * s}" height="{0.6 * s}" fill="#8a6a3a" stroke="#3a2a10"/>')
    # Ellinger's tower, the Western Tower, the great tree, the ghost castle
    out.append(f'<circle cx="{71 * s}" cy="{47.5 * s}" r="{1.1 * s}" fill="#4a4652" stroke="#fff" stroke-width="1.5"/>')
    out.append(f'<circle cx="{31.5 * s}" cy="{33.5 * s}" r="{1.2 * s}" fill="#3e3a46" stroke="#fff" stroke-width="1.5"/>')
    out.append(f'<circle cx="{47.5 * s}" cy="{35.5 * s}" r="{1.6 * s}" fill="#22301f" stroke="#e8d27a" stroke-width="2"/>')
    ghost = [[35.5, 65.5], [44.5, 65.5], [44.5, 75], [35.5, 75]]
    out.append(f'<polygon points="{" ".join(f"{x * s},{y * s}" for x, y in ghost)}" fill="#e8e8ff" fill-opacity="0.45" '
               'stroke="#7a5aa8" stroke-width="2.5" stroke-dasharray="7 4"/>')
    for x, y in ghost:
        out.append(f'<circle cx="{x * s}" cy="{y * s}" r="{0.9 * s}" fill="#e8e8ff" fill-opacity="0.6" stroke="#7a5aa8" stroke-dasharray="3 2"/>')
    # the cut rope bridge
    out.append(f'<line x1="{79.6 * s}" y1="{43.5 * s}" x2="{80.6 * s}" y2="{43.5 * s}" stroke="#3b2a1a" stroke-width="4"/>')
    out.append(f'<line x1="{81.6 * s}" y1="{43.5 * s}" x2="{82.6 * s}" y2="{43.5 * s}" stroke="#3b2a1a" stroke-width="4"/>')
    out.append(f'<text x="{81.1 * s}" y="{43.5 * s + 5}" font-size="16" text-anchor="middle" fill="#c00" font-weight="bold">x</text>')
    # the East Bridge
    out.append(f'<rect x="{79.6 * s}" y="{59.9 * s}" width="{2.8 * s}" height="{1.2 * s}" fill="#9a958a" stroke="#333"/>')
    # MU-4 cameras
    for view in sketch['views']:
        x, y = view['at']
        if 'arrival' in view['id']:      # plan_render draws this camera's cone
            out.append(f'<text x="{(x + .5) * s - 12}" y="{(y + .5) * s - 10}" font-size="12.5" fill="#0b3d8a" '
                       'font-weight="bold" text-anchor="end" stroke="#fff" stroke-width="3" paint-order="stroke">'
                       'MU-4 (a)</text>')
            continue
        lx, ly = view['look']
        ang = math.atan2(ly - y, lx - x)
        dist = min(math.hypot(lx - x, ly - y), 28)
        half = math.radians(37)
        p1 = (x + math.cos(ang - half) * dist, y + math.sin(ang - half) * dist)
        p2 = (x + math.cos(ang + half) * dist, y + math.sin(ang + half) * dist)
        poly = ' '.join(f'{(px + .5) * s:.1f},{(py + .5) * s:.1f}' for px, py in [(x, y), p1, p2])
        out.append(f'<polygon points="{poly}" fill="#1f6fd1" fill-opacity="0.10" stroke="#1f6fd1" stroke-width="1.5" '
                   'stroke-dasharray="6 4"/>')
        out.append(f'<circle cx="{(x + .5) * s}" cy="{(y + .5) * s}" r="7" fill="#1f6fd1" stroke="#fff" stroke-width="1.5"/>')
        label = 'MU-4 (a) arrival' if 'arrival' in view['id'] else 'MU-4 (b) signature view'
        out.append(f'<text x="{(x + .5) * s + 10}" y="{(y + .5) * s + 18}" font-size="12.5" fill="#0b3d8a" '
                   f'font-weight="bold" stroke="#fff" stroke-width="3" paint-order="stroke">{label}</text>')
    return '\n'.join(out)


# ---------------------------------------------------------------- the blockout, with Darkside's amber sky

def blockout(height, colour_img, view, model_list, out_path, w=1536, h=1024, fov=78.0, annotations=None):
    """plan_render.blockout with an amber sky and haze (xeendark1): a heightfield ray cast, models as blocks."""
    size = height.shape[0]
    col = np.asarray(colour_img.convert('RGB')).astype(float)
    cx, cy = (view['at'][0] + 0.5) * RES, (view['at'][1] + 0.5) * RES
    eye = height[int(cy), int(cx)] + view.get('height', 180)
    lx, ly = (view['look'][0] + 0.5) * RES, (view['look'][1] + 0.5) * RES
    yaw = math.atan2(ly - cy, lx - cx)
    pitch = math.radians(view.get('pitch', -3.0))
    unit = RES / 512.0
    haze = np.array((214, 168, 112))
    img = np.zeros((h, w, 3))
    for yy in range(h):
        t = yy / h
        img[yy, :] = np.array((120, 104, 104)) * (1 - t) + np.array((236, 176, 104)) * t
    focal = (w / 2) / math.tan(math.radians(fov / 2))
    horizon = h / 2 + focal * math.tan(pitch)
    zs = np.concatenate([np.arange(60, 2000, 12.0), np.arange(2000, 32000, 40.0)])
    for sx in range(w):
        a = yaw + math.atan2(sx - w / 2, focal)
        dx, dy = math.cos(a), math.sin(a)
        corr = math.cos(a - yaw)
        ybuf = h
        last = 1000.0
        rx, ry = cx + dx * zs * unit, cy + dy * zs * unit
        inside = (rx >= 0) & (rx < size - 1) & (ry >= 0) & (ry < size - 1)
        for k in np.nonzero(inside)[0]:
            ix, iy = int(rx[k]), int(ry[k])
            fx, fy = rx[k] - ix, ry[k] - iy
            hgt = (height[iy, ix] * (1 - fx) * (1 - fy) + height[iy, ix + 1] * fx * (1 - fy)
                   + height[iy + 1, ix] * (1 - fx) * fy + height[iy + 1, ix + 1] * fx * fy)
            sy = int(horizon - (hgt - eye) / (zs[k] * corr) * focal)
            last = hgt
            if sy < ybuf:
                c = col[iy, ix] if hgt > 1 else np.array((14, 16, 32))
                fog = min(1.0, (zs[k] / 18000.0) ** 1.5) * 0.8
                c = c * (1 - fog) + haze * fog
                img[max(sy, 0):ybuf, sx] = c
                ybuf = max(sy, 0)
                if ybuf == 0:
                    break
        if ybuf > horizon:      # past the map: the stars beyond the rim, else the land going on into the haze
            img[int(max(horizon, 0)):ybuf, sx] = (14, 16, 32) if last <= 1 else haze * 0.85 + np.array((60, 70, 40)) * 0.15
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(out)
    # the small pale sun, low in the amber band
    sun = (int(w * 0.18), int(horizon - 230))
    draw.ellipse((sun[0] - 16, sun[1] - 16, sun[0] + 16, sun[1] + 16), fill=(255, 238, 200))
    order = []
    for m in model_list:
        mx, my = (m[0] + 0.5) * RES, (m[1] + 0.5) * RES
        order.append((math.hypot(mx - cx, my - cy) / unit, m))
    for d, m in sorted(order, key=lambda t: -t[0]):
        mx, my = (m[0] + 0.5) * RES, (m[1] + 0.5) * RES
        a = (math.atan2(my - cy, mx - cx) - yaw + math.pi) % (2 * math.pi) - math.pi
        if abs(a) > math.radians(fov / 2 + 5) or d < 200:
            continue
        z = d * math.cos(a)
        sx = w / 2 + math.tan(a) * focal
        base = height[int(min(my, size - 1)), int(min(mx, size - 1))] if m[2] is None else m[2]
        y0 = horizon - (base + m[3] - eye) / z * focal
        y1 = horizon - (base - eye) / z * focal
        half = m[4] * 512 / z * focal
        fog = min(1.0, (d / 18000.0) ** 1.5) * 0.8
        c = tuple(int(v * (1 - fog) + f * fog) for v, f in zip(m[5], haze))
        draw.rectangle((sx - half, y0, sx + half, y1), fill=c)
    for label, ax, ay, rise in annotations or []:
        mx, my = (ax + 0.5) * RES, (ay + 0.5) * RES
        a = (math.atan2(my - cy, mx - cx) - yaw + math.pi) % (2 * math.pi) - math.pi
        if abs(a) > math.radians(fov / 2):
            continue
        z = math.hypot(mx - cx, my - cy) / unit * math.cos(a)
        sx = w / 2 + math.tan(a) * focal
        base = height[int(min(my, size - 1)), int(min(mx, size - 1))] + rise
        sy = horizon - (base - eye) / z * focal
        draw.ellipse((sx - 9, sy - 9, sx + 9, sy + 9), outline=(220, 30, 30), width=4)
        draw.text((sx + 12, sy - 12), label, fill=(200, 20, 20), font=pr.FONT)
    out.save(out_path)


# ---------------------------------------------------------------- measurements against MAPS

def inside(poly, x, y):
    return bool(pr.poly_mask(poly, scale=1)[int(y), int(x)]) if 0 <= x < N and 0 <= y < N else False


def poly_distance(poly, x, y):
    best = 1e9
    pts = poly + [poly[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        t = max(0, min(1, ((x - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - x0 - t * dx, y - y0 - t * dy))
    return best


def measure(plan, sketch, height):
    points = {}
    for p in sketch['points']:
        points.setdefault(p['id'], []).append(p['at'])
    land = np.zeros((N, N), bool)
    land[19:110, 24:110] = True                        # the playable square on land (the rim west of x 24, south of y 104)
    land[104:, :] = False
    river = pr.line_mask(sketch['water']['rivers'][0]['line'], 2.5, scale=1)
    acid = pr.poly_mask(sketch['water']['bodies'][1]['polygon'], scale=1)
    land &= ~river & ~acid
    enc = np.zeros((N, N), bool)
    areas = []
    for a in sketch['areas']:
        if a.get('kind', 'encounter') == 'encounter':
            m = pr.poly_mask(a['polygon'], scale=1)
            enc |= m
            areas.append({'id': a['id'], 'cells': int((m & land).sum()), 'big_cells': round((m & land).sum() / 64, 1),
                          'markers': a.get('count', 1)})
    quiet = 1 - (enc & land).sum() / land.sum()
    roads = np.zeros((N * 2, N * 2), bool)
    for r in sketch['roads']:
        if r['link'] in ('link:guild_row', 'link:west_lane', 'link:back_lane'):
            continue
        roads |= pr.line_mask(r['line'], 1.0 if r['width'] != 'lane' else 0.6, scale=2)
    land2 = np.kron(land, np.ones((2, 2), bool))
    road_share = (roads & land2).sum() / land2.sum()
    enc_polys = [a['polygon'] for a in sketch['areas'] if a.get('kind', 'encounter') == 'encounter']
    firsts = {}
    planned = {'entrance:castleview_pyramid': [64, 34], 'entrance:north_road': [67, 27], 'entrance:east_road': [98, 58]}
    for e, mk in planned.items():
        ex, ey = points[e][0]
        edge = min(poly_distance(p, ex, ey) for p in enc_polys)
        firsts[e] = {'nearest_area_edge': round(edge * 512), 'planned_marker': round(math.hypot(mk[0] - ex, mk[1] - ey) * 512)}
    # town arrivals: the nearest encounter area must be at least 2,500 away
    for e in ['entrance:castleview_square', 'entrance:castleview_temple', 'entrance:castleview_stables',
              'entrance:kalindra_gate']:
        ex, ey = points[e][0]
        firsts[e] = {'nearest_area_edge': round(min(poly_distance(p, ex, ey) for p in enc_polys) * 512)}
    # the town buffer: house doors to the nearest encounter area
    door_min = 1e9
    for d in sketch['districts']:
        if d['space'] != 'town:castleview':
            continue
        for plot in d['plots']:
            x, y = plot['at']
            door_min = min(door_min, min(poly_distance(p, x + 1, y + 1) for p in enc_polys))
    # POI census: one point per spot, chained merging within 400 units (D-11.4, D-15)
    def census(spots):
        spots = [(x * 512, y * 512) for x, y in spots]
        parent = list(range(len(spots)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i in range(len(spots)):
            for j in range(i + 1, len(spots)):
                if math.dist(spots[i], spots[j]) <= 400:
                    parent[find(i)] = find(j)
        return len({find(i) for i in range(len(spots))})
    devices = []
    for pid, ats in points.items():
        if pid.startswith('poi:') or pid.startswith('entrance:dd') or pid in ('entrance:grove_rope',):
            devices += [tuple(a) for a in ats]
    service_doors = []
    services = {b['id'] for s in plan['spaces'] for b in s.get('buildings', []) or [] if b['service'] != 'residence'}
    for d in sketch['districts']:
        for plot in d.get('plots', []) or []:
            if plot['building'] in services:
                b = next(b for s in plan['spaces'] for b in s.get('buildings', []) or [] if b['id'] == plot['building'])
                front, depth = b['footprint_cells'][0]
                wx, wy = (front, depth) if plot['facing'] in 'ns' else (depth, front)
                x, y = plot['at']
                door = {'n': (x + wx / 2, y), 's': (x + wx / 2, y + wy), 'e': (x + wx, y + wy / 2),
                        'w': (x, y + wy / 2)}[plot['facing']]
                service_doors.append(door)
    plots = sum(len(d.get('plots', []) or []) for d in sketch['districts'])
    town_plots = sum(len(d.get('plots', []) or []) for d in sketch['districts'] if d['space'] == 'town:castleview')
    hostiles = {'pop:siege_north': 9 * 2.5 + 4, 'pop:east_road_camp': 7 * 2.5 + 7, 'pop:grove_arachnoids': 7 * 3,
                'pop:grove_electrapedes': 3 * 2.5, 'pop:west_heath': 6 * 3, 'pop:centipede_meadows': 10 * 2.5,
                'pop:foothills': 5 * 2.5}
    result = {
        'land_cells': int(land.sum()), 'quiet_share': round(float(quiet), 3), 'areas': areas,
        'markers': sum(a['markers'] for a in areas), 'hostiles_by_area': hostiles,
        'hostiles_at_load': round(sum(hostiles.values())),
        'height_min': int(height[~pr.poly_mask([[0, 0], [24, 0], [24, 104], [128, 104], [128, 128], [0, 128]])].min()),
        'height_max': int(height.max()), 'road_share': round(float(road_share), 3), 'first_fight': firsts,
        'town_door_to_nearest_area': round(door_min * 512),
        'poi_devices': census(devices), 'poi_with_service_doors': census(devices + service_doors),
        'service_doors': len(service_doors), 'plots': plots, 'town_plots': town_plots,
    }
    return result


def main():
    plan, sketch, project = load()
    OUT.mkdir(exist_ok=True)
    height, water, acid, rim = build_land(sketch)
    img = colour_land(sketch, height, water, acid, rim)
    img.save(OUT / 'colour.png')
    labels = {'kinds': KINDS, 'names': NAMES, 'offsets': OFFSETS, 'arrows': ARROWS, 'encounters': ENCOUNTERS,
              'captions': CAPTIONS}
    svg = pr.svg_plan('d1', plan, sketch, project, labels, extra_svg(8, sketch))
    (OUT / 'plan_d1.svg').write_text(svg)
    model_list = models(plan, sketch)
    if '--no-blockout' not in sys.argv:
        bare = colour_land(sketch, height, water, acid, rim, trees=False)
        for view in sketch['views']:
            name = view['id'].split(':')[1]
            blockout(height, bare, view, model_list, OUT / f'blockout_{name}.png', fov=78.0,
                     annotations=ANNOTATIONS.get(view['id']))
    result = measure(plan, sketch, height)
    (OUT / 'measure.json').write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))


if __name__ == '__main__':
    main()
