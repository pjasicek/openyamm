#!/usr/bin/env python3
"""MU-3 plan drawing and MU-4 blockout views for D2 Sprite Forest and Ogre Pass (A6, phase 3), from its studio brief.

    d2_render.py        # reads devdocs/xeen/briefs/d2/L1/{plan,sketch,project}.yml

Writes into phase3/d2/: colour.png (the land the plan implies, for the drawings only), plan_d2.svg (+ plan_d2.png),
blockout_<view>.png (Codex's composition reference). Reuses phase2/plan_render.py (its SVG plan) without editing it;
the land, the colours and the blockout's amber sky are D2's own here. Nothing here is read by the game or the studio.
"""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True   # nothing written into phase2/ (shared)
sys.path.insert(0, str(HERE.parent / 'phase2'))
import plan_render as pr  # noqa: E402

OUT = HERE / 'd2'
RES, N = pr.RES, pr.N
RIM_Y = 106

GROUND = {  # sRGB per plan space, drawn over the default forest floor
    'zone:range': (112, 112, 120),
    'zone:foothills': (128, 128, 104),
    'zone:ogre_pass': (138, 124, 96),
    'zone:spur_crags': (110, 108, 108),
    'zone:whispering_glades': (92, 112, 78),
    'zone:east_descent': (126, 124, 96),
    'zone:west_edge': (96, 116, 78),
    'zone:sprite_forest': (70, 92, 64),
    'zone:troll_country': (78, 84, 60),
    'zone:southern_woods': (66, 84, 62),
    'town:sprite_village': (104, 122, 82),
    'zone:bark_glade': (96, 110, 76),
    'zone:fruit_clearing': (110, 116, 80),
    'zone:tower_clearing': (106, 112, 84),
    'zone:mine_mouth': (130, 118, 100),
    'zone:pass_saddle': (140, 126, 100),
}
ORDER = ['zone:range', 'zone:foothills', 'zone:ogre_pass', 'zone:east_descent', 'zone:whispering_glades',
         'zone:west_edge', 'zone:sprite_forest', 'zone:troll_country', 'zone:southern_woods', 'zone:spur_crags',
         'town:sprite_village', 'zone:bark_glade', 'zone:fruit_clearing', 'zone:tower_clearing', 'zone:mine_mouth',
         'zone:pass_saddle']
BAND_BASE = {'band:low': 1000, 'band:mid': 1450, 'band:high': 1900, 'band:peaks': 3000}
TREES = {  # space: (trees per cell, colour)
    'zone:sprite_forest': (0.85, (34, 56, 40)),
    'zone:troll_country': (0.75, (38, 52, 36)),
    'zone:southern_woods': (0.8, (30, 50, 38)),
    'zone:whispering_glades': (0.3, (40, 62, 44)),
    'zone:west_edge': (0.22, (40, 62, 44)),
    'zone:foothills': (0.08, (44, 64, 50)),
    'zone:east_descent': (0.1, (44, 64, 50)),
    'zone:ogre_pass': (0.04, (44, 64, 50)),
}
CLEAR = ['town:sprite_village', 'zone:bark_glade', 'zone:fruit_clearing', 'zone:tower_clearing', 'zone:mine_mouth',
         'zone:pass_saddle', 'zone:brink', 'zone:shrine_glade', 'zone:east_meadow']


def build_land(sketch):
    """Height (map units) per raster pixel from the sketch's bands, points, ridges, cliffs and the brook."""
    size = N * RES
    height = np.full((size, size), 1000.0)
    for band in sketch['heights']['bands']:
        if band['band'] == 'band:rim_sea':
            continue
        height[pr.poly_mask(band['polygon'])] = BAND_BASE[band['band']]
    height = ndimage.gaussian_filter(height, 4 * RES)
    yy, xx = np.mgrid[0:size, 0:size] / RES
    for point in sketch['heights'].get('points', []):
        px, py = point['at']
        r = 7.0 if point['h'] > 3000 else (5.0 if point['h'] > 1800 else 4.0)
        d = np.hypot(xx - px - 0.5, yy - py - 0.5)
        t = np.clip(1 - d / r, 0, 1)
        w = t * t * (3 - 2 * t)
        height = height * (1 - w) + point['h'] * w
    for ridge in sketch['heights'].get('ridges', []):
        m = pr.line_mask(ridge['line'], ridge.get('width', 2))
        dist = ndimage.distance_transform_edt(~m) / RES
        w = np.clip(1 - dist / (ridge.get('slope', 3) + 1.5), 0, 1)
        height = np.maximum(height, height * (1 - w) + ridge['height'] * w)
    # the north rim: the range's crest outside the square, crags with peaks
    rng = np.random.default_rng(5)
    crest = 3400 + 900 * (0.5 + 0.5 * np.sin(xx / 7.0 + 1.3) * np.cos(xx / 3.1))
    north = np.clip((19 - yy) / 10, 0, 1)
    height = np.maximum(height, height * (1 - north) + crest * north)
    noise = ndimage.gaussian_filter(rng.normal(size=(size, size)), 3 * RES)
    noise /= np.abs(noise).max() + 1e-6
    rough = ndimage.gaussian_filter(rng.normal(size=(size, size)), 0.6 * RES)
    rough /= np.abs(rough).max() + 1e-6
    calm = np.zeros((size, size), bool)
    for d in sketch.get('districts', []):
        if d['space'] in CLEAR:
            calm |= pr.poly_mask(d['polygon'])
    calm = ndimage.binary_dilation(calm, iterations=2 * RES)
    steep = np.clip((height - 1500) / 1200, 0, 1)
    height += np.where(calm, 0, noise * 160 + rough * (40 + 300 * steep))
    for d in sketch.get('districts', []):
        if d['space'] in ('town:sprite_village', 'zone:bark_glade', 'zone:pass_saddle'):
            m = pr.poly_mask(d['polygon'])
            target = {'town:sprite_village': 980, 'zone:bark_glade': 1000, 'zone:pass_saddle': 2050}[d['space']]
            soft = ndimage.gaussian_filter(m.astype(float), RES)
            height = height * (1 - soft) + target * soft
    # road beds: soften the land under the roads toward their median
    for road in sketch.get('roads', []):
        m = pr.line_mask(road['line'], 1.2)
        soft = ndimage.gaussian_filter(height, RES)
        height[m] = soft[m]
    water = np.zeros((size, size), bool)
    for river in sketch.get('water', {}).get('rivers', []):
        m = pr.line_mask(river['line'], river.get('width_cells', 1.5))
        bank = ndimage.binary_dilation(m, iterations=RES)
        height[bank] -= 60
        height[m] -= 120
        water |= m
    rim = yy >= RIM_Y
    height[rim] = 0
    return height, water, rim


def colour_land(sketch, height, water, rim):
    size = N * RES
    rgb = np.zeros((size, size, 3))
    rgb[:] = (72, 92, 64)
    masks = pr.space_masks(sketch)
    jitter = ndimage.gaussian_filter(np.random.default_rng(8).normal(size=(size, size)), 1.5 * RES)
    jitter /= np.abs(jitter).max() + 1e-6
    for space in ORDER:
        if space in masks:
            soft = ndimage.gaussian_filter(masks[space].astype(float), 2.0 * RES)
            soft = np.clip(soft + jitter * 0.35 * soft * (1 - soft) * 4, 0, 1)[..., None]
            rgb = rgb * (1 - soft) + np.array(GROUND[space]) * soft
    for road in sketch.get('roads', []):
        m = pr.line_mask(road['line'], 0.8 if road.get('width') == 'road' else 0.5)
        rgb[m] = (150, 128, 96) if road.get('width') == 'road' else (132, 118, 90)
    gy, gx = np.gradient(height, 512 / RES)
    slope = np.hypot(gx, gy)
    rock = np.clip((slope - 0.40) * 2.2, 0, 1)
    rock = np.maximum(rock, np.clip((height - 2600) / 600, 0, 0.8))
    rgb = rgb * (1 - rock[..., None]) + np.array((96, 98, 108)) * rock[..., None]
    rgb[water] = (58, 96, 104)
    light = np.array([-0.55, -0.65, 0.52])
    nx, ny, nz = -gx * 2.2, -gy * 2.2, np.ones_like(gx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    shade = np.clip(0.55 + 0.6 * (nx * light[0] + ny * light[1] + nz * light[2]) / norm, 0.35, 1.15)
    rgb = rgb * shade[..., None]
    stars = np.zeros((size, size, 3))
    stars[:] = (10, 12, 26)
    rng = np.random.default_rng(3)
    for y, x in rng.integers(0, size, size=(2200, 2)):
        stars[y, x] = rng.integers(140, 255)
    rgb[rim] = stars[rim]
    cliff = ndimage.binary_dilation(~rim, iterations=int(1.2 * RES)) & rim
    rgb[cliff] = (92, 86, 96)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    clear = np.zeros((size, size), bool)
    for space in CLEAR:
        if space in masks:
            clear |= masks[space]
    for space, (density, colour) in TREES.items():
        if space not in masks:
            continue
        ys, xs = np.nonzero(masks[space][::RES, ::RES])
        for cy, cx in zip(ys, xs):
            for _ in range(rng.poisson(density * 2)):
                x, y = (cx + rng.random()) * RES, (cy + rng.random()) * RES
                hy, hx = int(min(y, size - 1)), int(min(x, size - 1))
                if water[hy, hx] or rim[hy, hx] or clear[hy, hx] or height[hy, hx] > 2600:
                    continue
                s = RES * (0.35 + 0.2 * rng.random())
                draw.ellipse((x - s * 0.8, y - s * 0.8, x + s * 0.8, y + s * 0.8), fill=colour)
    # glowing caps: teal dots along the brook and in the glades
    for _ in range(420):
        x, y = rng.random() * size, rng.random() * size
        hy, hx = int(y), int(x)
        forest = any(masks.get(s, np.zeros(1, bool))[hy, hx] for s in ('zone:sprite_forest', 'zone:whispering_glades',
                                                                       'zone:bark_glade', 'town:sprite_village'))
        if forest and not rim[hy, hx] and rng.random() < 0.6:
            draw.ellipse((x - 1.1, y - 1.1, x + 1.1, y + 1.1), fill=(120, 230, 210))
    # crystal veins in the range: violet and teal flecks
    for _ in range(500):
        x, y = rng.random() * size, rng.random() * 22 * RES
        if height[int(y), int(x)] > 2600:
            c = (186, 120, 236) if rng.random() < 0.6 else (110, 220, 220)
            draw.line((x, y, x + 3, y - 4), fill=c, width=2)
    return img


# ---------------------------------------------------------------- labels for plan_render.svg_plan

KINDS = {
    'entrance:west_road': 'entrance', 'entrance:east_road': 'entrance',
    'entrance:dd09_door': 'dungeon', 'entrance:dd11a_hole': 'dungeon', 'entrance:dd11b_hole': 'dungeon',
    'entrance:dd11c_hole': 'dungeon', 'entrance:dd13_west': 'dungeon', 'entrance:dd13_east': 'dungeon',
    'entrance:dd06_door': 'dungeon', 'entrance:dd10b_adit': 'dungeon',
    'poi:treehouse_chest': 'chest', 'poi:kramer_wagon': 'chest', 'poi:dead_adventurer': 'chest',
    'poi:thieves_drop': 'chest', 'poi:pot_of_gold': 'chest',
    'poi:graalg': 'npc',
    'poi:signposts': 'junction', 'junction:forest_fork': 'junction', 'junction:bark_glade': 'junction',
    'junction:south_fork': 'junction', 'junction:pass_saddle': 'junction',
    'landmark:great_tree': 'landmark', 'landmark:range': 'landmark', 'landmark:west_fort': 'camp',
    'landmark:east_fort': 'camp', 'landmark:southern_tower': 'landmark', 'landmark:sprite_falls': 'landmark',
}
NAMES = {
    'entrance:west_road': 'from D1 Castleview Vale',
    'entrance:east_road': 'from D3 Sandcaster',
    'entrance:dd09_door': 'DD-09 Temple of Bark (door in the trunk)',
    'entrance:dd11a_hole': 'DD-11A troll hole',
    'entrance:dd11b_hole': 'DD-11B troll hole',
    'entrance:dd11c_hole': 'DD-11C troll hole (Hobstadt)',
    'entrance:dd13_west': 'DD-13 west fort (ogres)',
    'entrance:dd13_east': 'DD-13 east fort (ogres)',
    'entrance:dd06_door': 'DD-06 Southern Tower',
    'entrance:dd10b_adit': 'DD-10B Gemstone Mines (east adit)',
    'junction:forest_fork': 'Forest Fork',
    'junction:bark_glade': 'Bark Glade',
    'junction:south_fork': 'South Fork',
    'junction:pass_saddle': '',
    'poi:obelisk': 'Obelisk (BENEATH)',
    'poi:shrine_elements': 'Shrine of the Elements',
    'poi:forbidden_fruit': 'Forbidden Fruit hut',
    'poi:genie_lamp': 'Genie lamp (ledge)',
    'poi:pot_of_gold': "Leprechaun's pot (hidden)",
    'poi:graalg': 'Graalg, parley fire',
    'poi:treehouse_chest': '',
    'poi:kramer_wagon': "Kramer's wagon",
    'poi:crystal_seam': 'Crystal seam',
    'poi:fairy_ring': 'Fairy ring',
    'poi:dead_adventurer': '',
    'poi:thieves_drop': "Thieves' drop",
    'poi:brink_bench': 'The Brink',
    'landmark:great_tree': 'THE GREAT TREE',
    'landmark:west_fort': '',
    'landmark:east_fort': '',
    'landmark:southern_tower': '',
    'landmark:sprite_falls': 'Sprite Falls',
    'landmark:range': '',
}
OFFSETS = {
    'entrance:west_road': (4, -14, 'start'),
    'entrance:east_road': (-4, -14, 'end'),
    'entrance:dd09_door': (-10, -10, 'end'),
    'entrance:dd13_west': (-10, -10, 'end'),
    'entrance:dd13_east': (10, 16, 'start'),
    'entrance:dd06_door': (10, -6, 'start'),
    'entrance:dd10b_adit': (10, 14, 'start'),
    'entrance:dd11c_hole': (10, 4, 'start'),
    'junction:forest_fork': (-6, 18, 'end'),
    'junction:bark_glade': (10, -8, 'start'),
    'junction:south_fork': (10, 4, 'start'),
    'poi:graalg': (8, -12, 'start'),
    'poi:obelisk': (-10, 4, 'end'),
    'poi:kramer_wagon': (-8, 16, 'middle'),
    'poi:fairy_ring': (-10, 4, 'end'),
    'poi:pot_of_gold': (-10, -8, 'end'),
    'poi:brink_bench': (10, -6, 'start'),
    'landmark:great_tree': (12, 18, 'start'),
    'landmark:west_fort': (-12, -6, 'end'),
    'landmark:east_fort': (12, 14, 'start'),
    'landmark:sprite_falls': (-10, 4, 'end'),
}
ENCOUNTERS = {
    'pop:foothill_wolves': {'colour': '#c0282d'},
    'pop:west_sprites': {'colour': '#8a3cc0'},
    'pop:glade_sprites': {'colour': '#8a3cc0'},
    'pop:trolls': {'colour': '#c0282d'},
    'pop:woods_wolves': {'colour': '#c0282d'},
}
CAPTIONS = [
    ('E1 Gemstone foothills: 30 (wolves 16-28)', (38, 25.5), 13, '#7a1010'),
    ('E2 sprites, west: 10 (10-14)', (24, 81.2), 12, '#5a1a80'),
    ('E2 Whispering Glades: 14 (10-18)', (57, 64.6), 12, '#5a1a80'),
    ('E3 Troll country: 30 (18-38)', (68, 72.6), 13, '#7a1010'),
    ('E5 Southern Woods: 29 (16-22)', (101, 61), 13, '#7a1010'),
    ('E4 OGRE PASS: 22 placed (18-30)', (80, 29), 13, '#8a3c00'),
    ("SHARLA'S VILLAGE", (29.5, 98.6), 14, '#222'),
    ('THE GEMSTONE RANGE (crystal-veined crags to 4,400)', (64, 9), 15, '#eee'),
    ('THE SPRITE FOREST', (24, 102), 15, '#eef'),
    ('Glimmerbrook', (54.5, 57), 12, '#123'),
    ('the world rim: a cliff above the stars', (64, 112), 13, '#ccd'),
    ('to D1 (west edge, y 60)', (9, 58.4), 12, '#fff'),
    ('to D3 (east edge, y 44)', (118, 42.4), 12, '#fff'),
    ('Southern Tower', (95, 77.6), 12, '#222'),
    ('Gemstone Spur', (79, 53), 12, '#eee'),
]

# Blockout models: (cell x, cell y, base height or None for the ground, height, half width in cells, colour)
MODELS = [
    (42, 78, None, 2800, 0.9, (74, 58, 44)),          # the great tree's trunk
    (42, 78, 3100, 1500, 4.0, (40, 66, 50)),          # its crown
    (72, 34, None, 380, 2.4, (104, 80, 56)),          # west fort palisade
    (72, 33, None, 800, 0.9, (88, 66, 46)),           # west fort blockhouse
    (87, 45, None, 380, 2.4, (104, 80, 56)),          # east fort palisade
    (87, 46, None, 800, 0.9, (88, 66, 46)),           # east fort blockhouse
    (79, 36, None, 900, 0.12, (150, 150, 150)),       # Graalg's smoke
    (95, 81, None, 2300, 0.8, (70, 80, 100)),         # the Southern Tower
    (36, 51, None, 420, 0.2, (150, 150, 140)),        # obelisk
    (26.5, 84.5, None, 1500, 1.2, (80, 62, 46)),      # Sharla's trunk
    (26.5, 84.5, 2300, 900, 3.0, (44, 70, 52)),
    (33, 83.5, None, 1300, 0.9, (80, 62, 46)),        # the guild's trunk
    (33, 83.5, 2100, 800, 2.4, (44, 70, 52)),
    (23.5, 89, None, 1200, 0.9, (80, 62, 46)),
    (34.5, 89.5, None, 1200, 0.9, (80, 62, 46)),
    (28.5, 93.5, None, 1200, 0.9, (80, 62, 46)),
    (34, 31, None, 260, 0.5, (60, 50, 40)),           # the adit's timber frame
]

ANNOTATIONS = {
    'view:arrival': [
        ('great tree of Bark (crown over the canopy)', 42, 78, 3800),
        ('Forest Fork, signpost', 32, 60, 60),
        ('forest track into the Sprite Forest', 36, 65, 60),
        ('caravan road toward the pass', 40, 56, 60),
        ('foothills, obelisk knoll', 36, 51, 400),
        ('western glades (sprites)', 26, 72, 60),
        ('Gemstone Range, crystal crags', 44, 12, 0),
    ],
    'view:pass': [
        ('west fort on its knoll', 72, 34, 600),
        ('caravan road climbing', 70, 40, 60),
        ("saddle: Graalg's fire, smoke", 79, 36, 400),
        ('east fort on its knoll beyond', 87, 45, 600),
        ('Gemstone Spur crags', 80, 26, 0),
        ('range: crystal-veined peaks', 88, 12, 0),
        ("Kramer's burned wagon", 59, 46, 60),
        ('Whispering Glades below', 66, 52, 60),
    ],
    'view:village': [
        ('great tree trunk', 42, 78, 1200),
        ("Sharla's treehouse", 26.5, 84.5, 1200),
        ('Light Guild trunk', 33, 83.5, 1000),
        ('village green', 29, 89, 30),
    ],
}


def forest_models(sketch, height, rng):
    """Tree blocks for the blockout's forest canopy (composition only): none on roads, clearings or by a camera."""
    masks = pr.space_masks(sketch)
    clear = np.zeros_like(next(iter(masks.values())))
    for space in CLEAR:
        if space in masks:
            clear |= masks[space]
    for road in sketch.get('roads', []):
        clear |= pr.line_mask(road['line'], 2.5 if road.get('width') == 'road' else 1.6)
    cameras = [v['at'] for v in sketch['views']]
    out = []
    for space, density in [('zone:sprite_forest', 0.45), ('zone:troll_country', 0.4), ('zone:southern_woods', 0.4),
                           ('zone:whispering_glades', 0.18), ('zone:west_edge', 0.14), ('zone:foothills', 0.05),
                           ('zone:east_descent', 0.05)]:
        ys, xs = np.nonzero(masks[space][::RES, ::RES])
        for cy, cx in zip(ys, xs):
            if rng.random() > density:
                continue
            x, y = cx + rng.random(), cy + rng.random()
            px, py = int(x * RES), int(y * RES)
            if clear[py, px] or y >= RIM_Y - 0.5 or height[py, px] > 2400:
                continue
            if any(math.hypot(x - c[0] - 0.5, y - c[1] - 0.5) < 3.5 for c in cameras):
                continue
            g = rng.integers(-8, 9)
            out.append((x - 0.5, y - 0.5, None, 700 + rng.random() * 500, 0.45 + rng.random() * 0.2,
                        (38 + g, 60 + g, 44 + g)))
    return out


def blockout(height, colour_img, view, models, out_path, w=1536, h=1024, fov=80.0, annotations=None, pitch=-4.0):
    """plan_render's heightfield ray cast with an amber Darkside sky, amber haze and the stars below the rim."""
    size = height.shape[0]
    col = np.asarray(colour_img.convert('RGB')).astype(float)
    cx, cy = (view['at'][0] + 0.5) * RES, (view['at'][1] + 0.5) * RES
    eye = height[int(cy), int(cx)] + view.get('height', 180)
    lx, ly = (view['look'][0] + 0.5) * RES, (view['look'][1] + 0.5) * RES
    yaw = math.atan2(ly - cy, lx - cx)
    unit = RES / 512.0
    img = np.zeros((h, w, 3))
    haze = np.array((214, 168, 112))
    for yy in range(h):
        t = yy / h
        img[yy, :] = (150 + 80 * t, 120 + 60 * t, 96 + 30 * t)
    focal = (w / 2) / math.tan(math.radians(fov / 2))
    horizon = h / 2 + focal * math.tan(math.radians(pitch))
    # the pale small sun, low over the range
    sx0, sy0 = w * 0.62, horizon - h * 0.30
    yy_, xx_ = np.mgrid[0:h, 0:w]
    glow = np.exp(-((xx_ - sx0) ** 2 + (yy_ - sy0) ** 2) / (2 * 60.0 ** 2))[..., None]
    img = img * (1 - 0.5 * glow) + np.array((255, 236, 200)) * 0.5 * glow
    img[(xx_ - sx0) ** 2 + (yy_ - sy0) ** 2 < 12 ** 2] = (255, 246, 222)
    zs = np.concatenate([np.arange(60, 2000, 12.0), np.arange(2000, 32000, 40.0)])
    for sx in range(w):
        a = yaw + math.atan2(sx - w / 2, focal)
        dx, dy = math.cos(a), math.sin(a)
        corr = math.cos(a - yaw)
        ybuf = h
        rx, ry = cx + dx * zs * unit, cy + dy * zs * unit
        inside = (rx >= 0) & (rx < size - 1) & (ry >= 0) & (ry < size - 1)
        for k in np.nonzero(inside)[0]:
            ix, iy = int(rx[k]), int(ry[k])
            fx, fy = rx[k] - ix, ry[k] - iy
            hgt = (height[iy, ix] * (1 - fx) * (1 - fy) + height[iy, ix + 1] * fx * (1 - fy)
                   + height[iy + 1, ix] * (1 - fx) * fy + height[iy + 1, ix + 1] * fx * fy)
            sy = int(horizon - (hgt - eye) / (zs[k] * corr) * focal)
            if sy < ybuf:
                c = col[iy, ix] if hgt > 1 else np.array((14, 16, 32))
                fog = min(1.0, (zs[k] / 18000.0) ** 1.6) * 0.8
                c = c * (1 - fog) + haze * fog
                img[max(sy, 0):ybuf, sx] = c
                ybuf = max(sy, 0)
                if ybuf == 0:
                    break
        if ybuf > horizon:
            img[int(max(horizon, 0)):ybuf, sx] = (14, 16, 32)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(out)
    order = []
    for m in models:
        mx, my = (m[0] + 0.5) * RES, (m[1] + 0.5) * RES
        order.append((math.hypot(mx - cx, my - cy) / unit, m))
    for d, m in sorted(order, key=lambda t: -t[0]):
        mx, my = (m[0] + 0.5) * RES, (m[1] + 0.5) * RES
        a = (math.atan2(my - cy, mx - cx) - yaw + math.pi) % (2 * math.pi) - math.pi
        if abs(a) > math.radians(fov / 2 + 5) or d < 200:
            continue
        z = d * math.cos(a)
        sx = w / 2 + math.tan(a) * focal
        base = height[int(my), int(mx)] if m[2] is None else m[2]
        y0 = horizon - (base + m[3] - eye) / z * focal
        y1 = horizon - (base - eye) / z * focal
        half = m[4] * 512 / z * focal
        fog = min(1.0, (d / 18000.0) ** 1.6) * 0.8
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


def extra_svg(scale, sketch):
    """The ogres' placed area, the pass camera (plan_render draws only the arrival's) and the village inset frame."""
    s = scale
    parts = [f'<polygon points="{pr.pts([[60, 30], [98, 30], [100, 48], [60, 47]], s)}" fill="#e07a1f" '
             'fill-opacity="0.10" stroke="#e07a1f" stroke-width="2.4" stroke-dasharray="10 5"/>']
    for view in sketch['views']:
        if view['id'] != 'view:pass':
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
    # the brook's bridges
    for bx, by in [(51, 48), (48, 70)]:
        parts.append(f'<rect x="{(bx - 0.2) * s}" y="{(by - 0.6) * s}" width="{1.4 * s}" height="{1.2 * s}" '
                     'fill="#8a6a3a" stroke="#2a1a10" stroke-width="1"/>')
    return '\n'.join(parts)


def main():
    plan, sketch, project = pr.load('d2')
    OUT.mkdir(exist_ok=True)
    height, water, rim = build_land(sketch)
    img = colour_land(sketch, height, water, rim)
    img.save(OUT / 'colour.png')
    labels = {'kinds': KINDS, 'names': NAMES, 'offsets': OFFSETS, 'arrows': {'entrance:west_road': True,
              'entrance:east_road': True}, 'encounters': ENCOUNTERS, 'captions': CAPTIONS}
    pr.HERE = HERE            # svg_plan reads <HERE>/<key>/colour.png: point it at phase3
    svg = pr.svg_plan('d2', plan, sketch, project, labels, extra_svg(8, sketch))
    (OUT / 'plan_d2.svg').write_text(svg)
    rng = np.random.default_rng(21)
    models = MODELS + forest_models(sketch, height, rng)
    pitches = {'view:arrival': -2.0, 'view:pass': -1.0, 'view:village': -3.0}
    for view in sketch['views']:
        name = view['id'].split(':')[1]
        blockout(height, img, view, models, OUT / f'blockout_{name}.png', fov=80.0,
                 annotations=ANNOTATIONS.get(view['id']), pitch=pitches.get(view['id'], -4.0))
    print('heights', int(height[~rim].min()), int(height.max()), 'written to', OUT)


if __name__ == '__main__':
    main()
