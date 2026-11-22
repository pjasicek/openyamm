#!/usr/bin/env python3
"""MU-3 drawing, MU-4 blockouts, the plan's measurements and the D4 and D6 edge matches for D5 Desert of Doom
(A6, phase 5).

    d5_render.py [--no-blockout]   -> phase5/d5/{colour.png, plan_d5.svg, blockout_<view>.png, measure.json,
                                       edge_d4.json, edge_d6.json}

Reads the brief devdocs/xeen/briefs/d5/L1/{plan,sketch,project}.yml; for the edges D4's and D2's installed heightmaps
(assets_dev/worlds/xeen/maps/xeen_d4.odm, xeen_d2.odm, read only) and the shared border file phase5/edge_d5_d6.json
(read only). Reuses phase2/plan_render.py (the SVG plan) without editing it; the blockout is phase3/d2_render.py's
amber ray cast, copied here with pyramids, a translucent curtain and a sun placed per view. The land drawn here is the
drawing's model of the sketch, not the studio's build. Nothing here is read by the game or the studio.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True      # leave phase2's folder untouched
sys.path.insert(0, str(HERE.parent / 'phase2'))
import plan_render as pr  # noqa: E402

ROOT = pr.ROOT
OUT = HERE / 'd5'
RES, N = pr.RES, pr.N
SIZE = N * RES
BOX = (19, 109)             # the playable square, both axes
RIM_N = 24
OASIS_LEVEL = 1320

BAND_BASE = {'band:sands': 1350, 'band:doom': 1500, 'band:valley': 1600, 'band:pass': 1750, 'band:scarp': 1900,
             'band:forest': 2700, 'band:highlands': 2800, 'band:hills': 2100}
GROUND = {   # sRGB per plan space (Darkside: amber sand, red-brown stony desert, desaturated greens, slate)
    'zone:perishing_sands': (198, 160, 104),
    'zone:desert_of_doom': (156, 122, 92),
    'zone:east_valley': (118, 118, 84),
    'zone:west_pass': (138, 116, 92),
    'zone:escarpment': (138, 98, 78),
    'zone:quivering_forest': (98, 110, 82),
    'zone:highlands': (120, 122, 108),
    'zone:south_hills': (140, 114, 92),
    'zone:barrier_lee': (104, 104, 104),
    'zone:pyramid_precinct': (200, 164, 108),
    'zone:boulder_field': (172, 146, 108),
    'zone:oasis': (120, 130, 86),
    'zone:shrine_mesa': (166, 118, 86),
    'zone:giants_hold': (128, 118, 98),
    'zone:tower_knoll': (116, 116, 112),
    'zone:bosco_terrace': (128, 124, 116),
    'zone:cyclops_lair': (118, 112, 86),
    'zone:grate_hollow': (150, 128, 100),
}
ORDER = ['zone:south_hills', 'zone:perishing_sands', 'zone:desert_of_doom', 'zone:east_valley', 'zone:west_pass',
         'zone:escarpment', 'zone:quivering_forest', 'zone:highlands', 'zone:barrier_lee', 'zone:oasis',
         'zone:shrine_mesa']
TREES = {   # space: (trees per cell, colour)
    'zone:quivering_forest': (0.9, (150, 156, 110)),      # pale trembling aspens
    'zone:east_valley': (0.22, (40, 56, 42)),             # the last firs of the Forest of Peril
    'zone:highlands': (0.03, (60, 72, 58)),
    'zone:oasis': (0.6, (70, 96, 52)),                    # date palms
}
CLEAR = ['zone:giants_hold', 'zone:tower_knoll', 'zone:bosco_terrace', 'zone:boulder_field', 'zone:grate_hollow',
         'zone:pyramid_precinct', 'zone:cyclops_lair']
FLATS = [('zone:giants_hold', 2700), ('zone:tower_knoll', 3000), ('zone:bosco_terrace', 2650),
         ('zone:boulder_field', 1380), ('zone:grate_hollow', 1450), ('zone:cyclops_lair', 2700),
         ('zone:shrine_mesa', 1900)]
PYRAMID = (64, 86, 6.0, 3600)          # centre x, y, half base (cells), height above the plinth
PLINTH = 1250


def load():
    return pr.load('d5')


# ---------------------------------------------------------------- the neighbours (read only)

def odm_heights(stem):
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_odm_file
    data = parse_odm_file(ROOT / f'assets_dev/worlds/xeen/maps/{stem}.odm')
    return np.array(data['payload']['height_map'], int).reshape(N, N) * 32


def d6_column():
    return np.array(json.loads((HERE / 'edge_d5_d6.json').read_text())['heights_by_y'], float)


def border_targets():
    """The three border lines D5 must carry: east x 109 (D4's x 19), west x 19 (the shared file), south y 109
    (D2's y 19, falling from x 100 to D4's corner value at x 109)."""
    d4 = odm_heights('xeen_d4')
    d2 = odm_heights('xeen_d2')
    east = d4[:, 19].astype(float)
    west = d6_column()
    south = d2[19].astype(float)
    t = np.clip((np.arange(N) - 100) / 9.0, 0, 1)
    south = south * (1 - t) + east[109] * t
    south[110:] = east[109]
    return east, west, south, d4, d2


def west_rim_profile(sketch):
    out = np.zeros(N)
    for r in sketch['frame']['rim']:
        if r['side'] != 'west':
            continue
        a, b = r.get('span', [0, 128])
        for c in range(int(a), int(b)):
            if r['form'] == 'level':
                out[c] = r['height']
            else:
                lo, hi = r['height']
                out[c] = lo + (hi - lo) * (0.5 + 0.5 * math.sin(c / 3.7 + 1.3))
    return out


# ---------------------------------------------------------------- the land model

def build_land(sketch):
    """Height (map units) per raster pixel from the sketch's bands, points, ridges, dunes, water and roads, with the
    three borders carried exactly and the strips beyond them drawn from the neighbours."""
    height = np.full((SIZE, SIZE), 1500.0)
    for band in sketch['heights']['bands']:
        if band['band'] == 'band:rim_sea':
            continue
        height[pr.poly_mask(band['polygon'])] = BAND_BASE[band['band']]
    yy, xx = np.mgrid[0:SIZE, 0:SIZE] / RES
    height = ndimage.gaussian_filter(height, 3 * RES)
    for point in sketch['heights'].get('points', []):
        px, py = point['at']
        r = 6.0 if point['h'] > 3300 else (4.5 if point['h'] > 2200 else 3.5)
        d = np.hypot(xx - px - 0.5, yy - py - 0.5)
        t = np.clip(1 - d / r, 0, 1)
        w = t * t * (3 - 2 * t)
        height = height * (1 - w) + point['h'] * w
    for ridge in sketch['heights'].get('ridges', []):
        m = pr.line_mask(ridge['line'], ridge.get('width', 2))
        dist = ndimage.distance_transform_edt(~m) / RES
        w = np.clip(1 - dist / (ridge.get('slope', 3) + 1.5), 0, 1)
        height = np.maximum(height, height * (1 - w) + ridge['height'] * w)
    masks = pr.space_masks(sketch)
    rng = np.random.default_rng(5)
    noise = ndimage.gaussian_filter(rng.normal(size=(SIZE, SIZE)), 3 * RES)
    noise /= np.abs(noise).max() + 1e-6
    rough = ndimage.gaussian_filter(rng.normal(size=(SIZE, SIZE)), 0.6 * RES)
    rough /= np.abs(rough).max() + 1e-6
    calm = np.zeros((SIZE, SIZE), bool)
    for s, _ in FLATS:
        calm |= masks.get(s, calm)
    calm = ndimage.binary_dilation(calm, iterations=RES)
    steep = np.clip((height - 1800) / 1200, 0, 1)
    sand = ndimage.gaussian_filter(masks['zone:perishing_sands'].astype(float), 1.5 * RES)
    height += np.where(calm, 0, noise * 140 + rough * (30 + 280 * steep) * (1 - 0.8 * sand))
    # dunes: long crests running north-east, the sea of sand only
    phase = (xx * 0.55 + yy * 0.95) / 2.6
    wobble = ndimage.gaussian_filter(rng.normal(size=(SIZE, SIZE)), 4 * RES)
    wobble /= np.abs(wobble).max() + 1e-6
    size_n = ndimage.gaussian_filter(rng.normal(size=(SIZE, SIZE)), 6 * RES)
    size_n = 0.55 + 0.45 * size_n / (np.abs(size_n).max() + 1e-6)
    dune = (np.sin(phase * 2 * np.pi + wobble * 5.0) * 0.5 + 0.5) ** 2.0 * 150 * size_n
    keep = np.zeros((SIZE, SIZE), bool)
    for s in ('zone:pyramid_precinct', 'zone:boulder_field', 'zone:grate_hollow'):
        keep |= masks[s]
    for road in sketch.get('roads', []):
        keep |= pr.line_mask(road['line'], 1.6)
    keepw = ndimage.gaussian_filter(keep.astype(float), RES)
    height += dune * sand * (1 - keepw)
    # the flats: the hold, the knoll, the terrace, the boulder field, the grate's hollow, the lair, the mesa's top
    for space, target in FLATS:
        soft = ndimage.gaussian_filter(masks[space].astype(float), 1.6 * RES)
        height = height * (1 - soft) + target * soft
    # the pyramid's plinth (the pyramid itself is a model)
    cx, cy, half, _ = PYRAMID
    plinth = (np.abs(xx - cx) < half + 1.5) & (np.abs(yy - cy) < half + 1.5)
    soft = ndimage.gaussian_filter(plinth.astype(float), RES)
    height = height * (1 - soft) + PLINTH * soft
    # the oasis pool
    water = np.zeros((SIZE, SIZE), bool)
    for body in sketch['water']['bodies']:
        if body['kind'] == 'pond':
            m = pr.poly_mask(body['polygon'])
            dist = ndimage.distance_transform_edt(~m) / RES
            near = dist < 4
            height[near] = np.minimum(height[near], body['level'] + 20 + 60 * dist[near])
            height[m] = body['level']
            water |= m
    # road beds
    smooth = ndimage.gaussian_filter(height, RES)
    for road in sketch.get('roads', []):
        m = pr.line_mask(road['line'], 1.0) & ~water
        height[m] = smooth[m]
    # the borders, carried exactly and blended in over six cells
    east, west, south, d4, d2 = border_targets()
    up = lambda a: np.interp(np.arange(SIZE) / RES - 0.5, np.arange(N), a)
    eastp, westp, southp = up(east), up(west), up(south)
    de = np.abs(xx - (BOX[1] + 0.5))
    dw = np.abs(xx - (BOX[0] + 0.5))
    ds = np.abs(yy - (BOX[1] + 0.5))
    for dist, target in ((ds, southp[None, :] + 0 * yy), (dw, westp[:, None] + 0 * xx), (de, eastp[:, None] + 0 * xx)):
        w = np.clip(1 - dist / 6.0, 0, 1) ** 1.5
        inside_box = (xx >= BOX[0]) & (xx < BOX[1] + 1) & (yy < BOX[1] + 1)
        height = np.where(inside_box, height * (1 - w) + target * w, height)
    # beyond the borders: D4's own land east, D2's south, the rim forms west
    fx, fy = xx - 0.5, yy - 0.5       # cell coordinates of each pixel's centre
    east_strip = xx >= BOX[1] + 1
    d4_here = ndimage.map_coordinates(d4.astype(float), [np.clip(fy, 0, N - 1), np.clip(fx - 90, 0, N - 1)],
                                      order=1)
    height[east_strip] = d4_here[east_strip]
    south_strip = (yy >= BOX[1] + 1) & ~east_strip
    d2_here = ndimage.map_coordinates(d2.astype(float), [np.clip(fy - 90, 0, N - 1), np.clip(fx, 0, N - 1)],
                                      order=1)
    height[south_strip] = d2_here[south_strip]
    west_strip = (xx < BOX[0]) & (yy < BOX[1] + 1)
    prof = ndimage.gaussian_filter1d(west_rim_profile(sketch), 2.0)
    k = np.clip((BOX[0] - xx) / 8.0, 0, 1)
    blend = westp[:, None] * (1 - k) + up(prof)[:, None] * k
    height[west_strip] = blend[west_strip]
    outside = east_strip | south_strip | west_strip
    soft = ndimage.gaussian_filter(height, 1.0 * RES)
    height = np.where(outside, soft, height)
    # the rim: north of y 24 the stars
    rim = yy < RIM_N
    height[rim] = 0
    water &= ~rim
    return height, water, rim


def colour_land(sketch, height, water, rim, trees=True):
    rgb = np.zeros((SIZE, SIZE, 3))
    rgb[:] = (160, 132, 98)
    masks = pr.space_masks(sketch)
    jitter = ndimage.gaussian_filter(np.random.default_rng(8).normal(size=(SIZE, SIZE)), 1.5 * RES)
    jitter /= np.abs(jitter).max() + 1e-6
    for space in ORDER:
        if space in masks:
            soft = ndimage.gaussian_filter(masks[space].astype(float), 1.6 * RES)
            soft = np.clip(soft + jitter * 0.35 * soft * (1 - soft) * 4, 0, 1)[..., None]
            rgb = rgb * (1 - soft) + np.array(GROUND[space]) * soft
    # the salt pan: the sands' lowest trough
    pan = masks['zone:perishing_sands'] & (height < 1180)
    pan = ndimage.gaussian_filter(pan.astype(float), RES)[..., None]
    rgb = rgb * (1 - pan) + np.array((226, 220, 200)) * pan
    # snow in the highest hollows
    snow = np.clip((height - 3150) / 400, 0, 1) * 0.85
    rgb = rgb * (1 - snow[..., None]) + np.array((222, 226, 232)) * snow[..., None]
    # dry wadis: cracked pale beds from the western hills and the cliffs to the pan
    for line in WADIS:
        m = pr.line_mask(line, 0.5)
        rgb[m] = rgb[m] * 0.5 + np.array((196, 176, 140)) * 0.5
    for road in sketch.get('roads', []):
        m = pr.line_mask(road['line'], 0.8 if road.get('width') == 'road' else 0.5)
        rgb[m] = (176, 150, 112) if road.get('width') == 'road' else (164, 142, 108)
    gy, gx = np.gradient(height, 512 / RES)
    slope = np.hypot(gx, gy)
    rock = np.clip((slope - 0.38) * 2.2, 0, 1) * (1 - 0.6 * snow)
    rgb = rgb * (1 - rock[..., None]) + np.array((124, 88, 72)) * rock[..., None]
    rgb[water] = (46, 88, 92)
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
        clear |= masks.get(space, clear)
    for road in sketch.get('roads', []):
        clear |= pr.line_mask(road['line'], 1.2)
    for space, (density, colour) in TREES.items():
        ys, xs = np.nonzero(masks[space][::RES, ::RES])
        for cy, cx in zip(ys, xs):
            for _ in range(rng.poisson(density * 2)):
                x, y = (cx + rng.random()) * RES, (cy + rng.random()) * RES
                hy, hx = int(min(y, SIZE - 1)), int(min(x, SIZE - 1))
                if water[hy, hx] or rim[hy, hx] or clear[hy, hx] or height[hy, hx] > 3300:
                    continue
                s = RES * (0.32 + 0.2 * rng.random())
                draw.polygon([(x, y - s * 1.3), (x + s * 0.7, y + s * 0.5), (x - s * 0.7, y + s * 0.5)],
                             fill=colour)
    return img


WADIS = [
    [[22, 74], [28, 77], [34, 82], [40, 86], [46, 90], [54, 93]],
    [[34, 62], [40, 64], [46, 66], [52, 66], [56, 67]],
    [[22, 96], [30, 99], [40, 99], [50, 99]],
    [[70, 62], [74, 66], [80, 70], [86, 76], [90, 86], [90, 91]],
]


# ---------------------------------------------------------------- labels for plan_render.svg_plan

KINDS = {
    'entrance:d4_road': 'entrance', 'entrance:d6_pass': 'entrance',
    'entrance:dd15_door': 'dungeon', 'entrance:dd08_door': 'dungeon', 'entrance:dd24_doors': 'dungeon',
    'entrance:dd25_door': 'dungeon', 'entrance:dd18_grate': 'dungeon',
    'poi:lair_hoard': 'chest', 'poi:eyrie_nest': 'chest', 'poi:caravan_wreck': 'chest', 'poi:prospector': 'chest',
    'poi:dwarf_camp': 'chest', 'poi:robbers_camp': 'chest', 'poi:gurodel': 'npc',
    'poi:signposts': 'junction', 'junction:pyramid_fork': 'junction', 'junction:scarp_foot': 'junction',
    'junction:highland_fork': 'junction', 'junction:doom_fork': 'junction',
    'landmark:great_pyramid': 'landmark', 'landmark:barrier': 'landmark', 'landmark:broken_pyramid': 'landmark',
    'landmark:northern_tower': 'landmark', 'landmark:giants_fire': 'landmark',
}
NAMES = {
    'entrance:d4_road': 'from D4 (y 80)',
    'entrance:d6_pass': 'from D6 (y 64)',
    'entrance:dd15_door': 'DD-15 Great Pyramid',
    'entrance:dd08_door': 'DD-08 Northern Tower',
    'entrance:dd24_doors': "DD-24 Giants' Hall (2 leaves)",
    'entrance:dd25_door': "DD-25 Bosco's Hall",
    'entrance:dd18_grate': 'DD-18 tunnel grate',
    'junction:pyramid_fork': '', 'junction:scarp_foot': '', 'junction:highland_fork': '', 'junction:doom_fork': '',
    'poi:obelisk': 'Obelisk',
    'poi:shrine_great_power': 'Shrine of Great Power',
    'poi:fountain_endurance': 'Endurance +2',
    'poi:fountain_energy': 'Energy Resistance',
    'poi:fountain_might': 'Fountain of Might',
    'poi:capstone': 'capstone (obelisk hoard)',
    'poi:lamp_doom': 'genie lamp', 'poi:lamp_sands': 'genie lamp',
    'poi:boulder_sign': 'sign', 'poi:boulders': '',
    'poi:giants_lair': "cyclopes' lair (Destroy?)", 'poi:lair_hoard': '',
    'poi:eyrie_nest': 'eyrie', 'poi:caravan_wreck': 'caravan wreck', 'poi:prospector': 'prospector',
    'poi:dwarf_camp': 'dwarf camp', 'poi:robbers_camp': "robbers' camp", 'poi:munchies': 'munchies',
    'poi:gurodel': 'Gurodel', 'poi:signposts': '',
    'landmark:great_pyramid': 'THE GREAT PYRAMID', 'landmark:barrier': 'PARABOLIC BARRIER',
    'landmark:broken_pyramid': 'broken travel pyramid', 'landmark:northern_tower': '',
    'landmark:giants_fire': '',
}
OFFSETS = {
    'entrance:d4_road': (-8, -14, 'end'),
    'entrance:d6_pass': (6, -14, 'start'),
    'entrance:dd15_door': (10, -12, 'start'),
    'entrance:dd08_door': (0, -12, 'middle'),
    'entrance:dd24_doors': (10, -8, 'start'),
    'entrance:dd25_door': (-10, -8, 'end'),
    'entrance:dd18_grate': (10, 4, 'start'),
    'poi:obelisk': (-8, 16, 'end'),
    'poi:shrine_great_power': (10, 4, 'start'),
    'poi:fountain_endurance': (10, 6, 'start'),
    'poi:fountain_energy': (10, 14, 'start'),
    'poi:fountain_might': (8, 18, 'start'),
    'poi:capstone': (-10, 14, 'end'),
    'poi:lamp_doom': (10, 4, 'start'),
    'poi:lamp_sands': (10, 4, 'start'),
    'poi:boulder_sign': (10, -10, 'start'),
    'poi:giants_lair': (10, 4, 'start'),
    'poi:eyrie_nest': (10, 14, 'start'),
    'poi:caravan_wreck': (10, 4, 'start'),
    'poi:prospector': (10, 4, 'start'),
    'poi:dwarf_camp': (-10, 4, 'end'),
    'poi:robbers_camp': (10, 12, 'start'),
    'poi:munchies': (10, 4, 'start'),
    'poi:gurodel': (10, 14, 'start'),
    'landmark:great_pyramid': (0, 60, 'middle'),
    'landmark:barrier': (0, -16, 'middle'),
    'landmark:broken_pyramid': (12, -8, 'start'),
}
ENCOUNTERS = {
    'pop:sands_lizards': {'colour': '#c0282d'},
    'pop:pyramid_lizards': {'colour': '#c0282d'},
    'pop:cliff_birds': {'colour': '#8a3c00'},
    'pop:doom_birds': {'colour': '#8a3c00'},
    'pop:forest_cyclopes': {'colour': '#8a3cc0'},
}
CAPTIONS = [
    ('E1 Perishing Sands, iguanasaurus: 20 (42-55)', (84, 103.4), 12, '#7a1010'),
    ('E2 pyramid dunes, iguanasaurus: 17.5', (54, 105.8), 12, '#7a1010'),
    ('E3 Griffin Cliffs, rocs and griffins: 22 + 3 placed', (60, 64.6), 12, '#5a2400'),
    ('E4 Quivering Forest, cyclopes: 27.5 (36-62)', (34, 25.9), 12, '#5a1a80'),
    ('E5 Desert of Doom, rocs: 20', (30, 107.2), 12, '#5a2400'),
    ('THE PERISHING SANDS', (86, 72.6), 15, '#5a3a10'),
    ('THE DESERT OF DOOM', (32, 73.2), 15, '#3a2010'),
    ('THE QUIVERING FOREST', (32, 47), 14, '#1e2a14'),
    ('THE NORTHERN HIGHLANDS (giants, quiet)', (93, 37.4), 14, '#223'),
    ("Gurodel's hold", (86, 51.4), 11.5, '#222'),
    ('salt pan', (90, 94.4), 11.5, '#445'),
    ('the Last Water', (44, 84.2), 11.5, '#123'),
    ('boulder field (7 boulders)', (86, 90.6), 11.5, '#222'),
    ('the world rim: a cliff above the stars', (64, 14), 15, '#ccd'),
    ('to D4 (east edge, y 80)', (118, 77.6), 12, '#fff'),
    ('to D6 (west edge, y 64)', (9, 61.6), 12, '#fff'),
    ('Gemstone spurs (D2 beyond, no crossing)', (64, 114), 12, '#fff'),
]

# Blockout models: (cell x, cell y, base height or None for the ground, height, half width in cells, colour, shape)
MODELS = [
    # the Great Pyramid (a triangle face-on) and its gilded capstone
    (64, 86, PLINTH, PYRAMID[3], PYRAMID[2], (196, 164, 112), 'tri'),
    (64, 86, PLINTH + PYRAMID[3] * 0.86, PYRAMID[3] * 0.14, PYRAMID[2] * 0.14, (226, 190, 90), 'tri'),
    (64, 79.6, PLINTH, 420, 0.6, (70, 110, 80), 'box'),                  # the green door's frame
    (72.5, 93, None, 220, 0.4, (150, 120, 96), 'box'),                    # the robbers' tent
    # the broken travel pyramid and its capstone
    (95, 72, None, 900, 1.6, (96, 112, 112), 'tri'),
    (93.6, 74, None, 260, 0.5, (110, 126, 124), 'tri'),
    # the boulders
    *[(bx, by, None, 260, 0.45, (128, 120, 112), 'box') for bx, by in
      [(83, 81), (85, 82), (87, 83), (84, 84), (86, 85), (83, 86), (85, 87)]],
    (86, 80, None, 200, 0.12, (110, 86, 60), 'box'),                      # the sign
    # the Northern Tower and Gurodel's fire smoke
    (69, 38, None, 1300, 0.9, (70, 70, 80), 'box'),
    (86, 46, None, 1600, 0.25, (150, 146, 140), 'box'),
    (86, 41.5, None, 520, 0.8, (60, 46, 36), 'box'),                      # DD-24's great doors
    (61, 46, None, 380, 0.5, (90, 86, 80), 'box'),                        # Bosco's door
    # the obelisk, the shrine's columns
    (46, 72, None, 520, 0.18, (60, 60, 64), 'box'),
    (31, 88, None, 300, 0.9, (190, 170, 140), 'box'),
]


def barrier_models(sketch):
    """The Parabolic Barrier: a frame every 2.5 cells along its arc and the curtain between them (translucent)."""
    from d5_brief import BARRIER
    out = []
    pts = np.array(BARRIER, float)
    seg = np.hypot(*(pts[1:] - pts[:-1]).T)
    total = seg.sum()
    for d in np.arange(1.0, total - 0.5, 2.5):
        i = int(np.searchsorted(np.cumsum(seg), d))
        t = (d - (np.cumsum(seg)[i] - seg[i])) / seg[i]
        x, y = pts[i] + (pts[i + 1] - pts[i]) * t
        out.append((x, y, None, 900, 0.12, (60, 78, 84), 'box'))
        out.append((x, y, None, 640, 1.3, (170, 236, 200, 38), 'box'))
    return out


def tree_models(sketch, height, water, rng):
    masks = pr.space_masks(sketch)
    clear = np.zeros((SIZE, SIZE), bool)
    for space in CLEAR:
        clear |= masks.get(space, clear)
    for road in sketch.get('roads', []):
        clear |= pr.line_mask(road['line'], 2.0 if road.get('width') == 'road' else 1.4)
    cameras = [v['at'] for v in sketch['views']]
    out = []
    for space, density, kind in [('zone:quivering_forest', 0.45, 'aspen'), ('zone:east_valley', 0.16, 'fir'),
                                 ('zone:oasis', 0.5, 'palm'), ('zone:highlands', 0.015, 'fir')]:
        ys, xs = np.nonzero(masks[space][::RES, ::RES])
        for cy, cx in zip(ys, xs):
            if rng.random() > density:
                continue
            x, y = cx + rng.random(), cy + rng.random()
            px, py = int(x * RES), int(y * RES)
            if clear[py, px] or water[py, px] or height[py, px] > 3300 or height[py, px] < 10:
                continue
            if any(math.hypot(x - c[0] - 0.5, y - c[1] - 0.5) < 6.0 for c in cameras):
                continue
            g = int(rng.integers(-8, 9))
            if kind == 'aspen':
                out.append((x - 0.5, y - 0.5, None, 700 + rng.random() * 400, 0.25 + rng.random() * 0.12,
                            (150 + g, 154 + g, 112 + g), 'box'))
            elif kind == 'palm':
                out.append((x - 0.5, y - 0.5, None, 500 + rng.random() * 200, 0.3, (70 + g, 96 + g, 52 + g), 'box'))
            else:
                out.append((x - 0.5, y - 0.5, None, 600 + rng.random() * 500, 0.35 + rng.random() * 0.2,
                            (34 + g, 50 + g, 40 + g), 'box'))
    return out


ANNOTATIONS = {
    'view:arrival': [
        ('Great Pyramid (far, ~21,000)', 64, 86, 3700),
        ('boulder field, sign by the road', 85, 83, 300),
        ('broken travel pyramid', 95, 72, 900),
        ('Parabolic Barrier, faint, on the highlands', 64, 33, 800),
        ('Perishing Sands', 88, 95, 200),
        ('last firs of the Forest of Peril', 103, 76, 400),
    ],
    'view:signature': [
        ('Great Pyramid, gilded capstone', 64, 86, 3700),
        ('green stone door (north face, hidden)', 64, 80, 300),
        ("robbers' tent", 72, 93, 200),
        ('Griffin Cliffs beyond', 62, 56, 600),
        ('Parabolic Barrier (faint)', 70, 34, 900),
        ('dune crests', 70, 96, 100),
    ],
}
SUN = {'view:arrival': (0.40, 0.26), 'view:signature': (0.30, 0.22)}   # (x share of width, height share above horizon)


def blockout(height, colour_img, view, models, out_path, w=1536, h=1024, fov=80.0, annotations=None, pitch=-4.0,
             sun=(0.62, 0.30)):
    """d2_render.blockout's heightfield ray cast with an amber Darkside sky, amber haze, the stars below the rim;
    models are boxes or triangles (pyramids), and a colour with a fourth number is drawn translucent."""
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
    sx0, sy0 = w * sun[0], horizon - h * sun[1]
    yy_, xx_ = np.mgrid[0:h, 0:w]
    glow = np.exp(-((xx_ - sx0) ** 2 + (yy_ - sy0) ** 2) / (2 * 60.0 ** 2))[..., None]
    img = img * (1 - 0.5 * glow) + np.array((255, 236, 200)) * 0.5 * glow
    img[(xx_ - sx0) ** 2 + (yy_ - sy0) ** 2 < 12 ** 2] = (255, 246, 222)
    zs = np.concatenate([np.arange(60, 2000, 12.0), np.arange(2000, 34000, 40.0)])
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
                fog = min(1.0, (zs[k] / 20000.0) ** 1.6) * 0.75
                c = c * (1 - fog) + haze * fog
                img[max(sy, 0):ybuf, sx] = c
                ybuf = max(sy, 0)
                if ybuf == 0:
                    break
        if ybuf > horizon:
            img[int(max(horizon, 0)):ybuf, sx] = (14, 16, 32)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    order = []
    for m in models:
        mx, my = (m[0] + 0.5) * RES, (m[1] + 0.5) * RES
        order.append((math.hypot(mx - cx, my - cy) / unit, m))
    for d, m in sorted(order, key=lambda t: -t[0]):
        mx, my = (m[0] + 0.5) * RES, (m[1] + 0.5) * RES
        a = (math.atan2(my - cy, mx - cx) - yaw + math.pi) % (2 * math.pi) - math.pi
        if abs(a) > math.radians(fov / 2 + 8) or d < 200:
            continue
        z = d * math.cos(a)
        sx = w / 2 + math.tan(a) * focal
        base = height[int(my), int(mx)] if m[2] is None else m[2]
        y0 = horizon - (base + m[3] - eye) / z * focal
        y1 = horizon - (base - eye) / z * focal
        half = m[4] * 512 / z * focal
        fog = min(1.0, (d / 20000.0) ** 1.6) * 0.75
        c = tuple(int(v * (1 - fog) + f * fog) for v, f in zip(m[5][:3], haze))
        alpha = m[5][3] if len(m[5]) > 3 else 255
        layer = Image.new('RGBA', out.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        if m[6] == 'tri':
            dl.polygon([(sx - half, y1), (sx + half, y1), (sx, y0)], fill=c + (alpha,))
            # the shaded right-hand face
            dl.polygon([(sx, y0), (sx + half, y1), (sx + half * 0.35, y1)],
                       fill=tuple(int(v * 0.72) for v in c) + (alpha,))
        else:
            dl.rectangle((sx - half, y0, sx + half, y1), fill=c + (alpha,))
        out = Image.alpha_composite(out, layer)
    out = out.convert('RGB')
    draw = ImageDraw.Draw(out)
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

def poly_distance(poly, x, y):
    best = 1e9
    pts = poly + [poly[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        t = max(0, min(1, ((x - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - x0 - t * dx, y - y0 - t * dy))
    return best


def census(spots):
    """One point per spot, chained merging within 400 units (D-11.4, D-15); spots tagged with a set piece are one
    spot (D-20: one set piece one spot)."""
    parent = list(range(len(spots)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(spots)):
        for j in range(i + 1, len(spots)):
            same_piece = spots[i][2] and spots[i][2] == spots[j][2]
            if same_piece or math.dist(spots[i][1], spots[j][1]) * 512 <= 400:
                parent[find(i)] = find(j)
    groups = {}
    for i, s in enumerate(spots):
        groups.setdefault(find(i), []).append(s)
    return list(groups.values())


SET_PIECE_OF = {'poi:boulders': 'set:enchanted_boulders', 'poi:boulder_sign': 'set:enchanted_boulders'}
LEVELS = {'Xeen Iguanasaurus': (42, 50, 55), 'Xeen Roc': (30, 38, 48), 'Xeen Giant': (36, 50, 62)}
ODDS = {1: (0.9, 0.08, 0.02), 2: (0.7, 0.2, 0.1), 3: (0.5, 0.3, 0.2), 4: (0.3, 0.4, 0.3), 5: (0.1, 0.5, 0.4)}
ROW_LEVEL = {'11562': 48, '11080': 36, '11081': 50, '11082': 62}
PEOPLE_LEVEL = {'11080': 38, '11081': 50, '11082': 58}      # D-47: the People rows 11083-11085 at 38/50/58


def xp(level):
    return level * (level + 10)


def measure(plan, sketch, project, height, water, rim):
    kinds = {p['id']: p['kind'] for p in plan['points_of_interest']}
    pts = {}
    for p in sketch['points']:
        pts.setdefault(p['id'], []).append(p['at'])
    small = lambda m: m[RES // 2::RES, RES // 2::RES]
    masks = pr.space_masks(sketch)
    lee = small(masks['zone:barrier_lee'])
    land = np.zeros((N, N), bool)
    land[BOX[0]:BOX[1], BOX[0]:BOX[1]] = True
    land &= ~small(rim) & ~small(water) & ~lee
    enc_areas = [a for a in sketch['areas'] if a.get('kind', 'encounter') == 'encounter']
    covered = np.zeros((N, N), bool)
    areas = []
    for a in enc_areas:
        m = pr.poly_mask(a['polygon'], scale=1)
        covered |= m
        cells = int((m & land).sum())
        areas.append({'id': a['id'], 'land_cells': cells, 'big_cells': round(cells / 64, 1),
                      'count': a.get('count', 0)})
    quiet = 1 - (covered & land).sum() / land.sum()
    slots = project['map_stats']['slots']
    avg = {i + 1: sum(s['per_marker']) / 2 for i, s in enumerate(slots)}
    by_area = {a['id']: a['count'] * avg[a['slot']] for a in enc_areas}
    placed = [a for a in sketch['actors'] if a.get('hostile')]
    placed_n = sum(a.get('count', 1) for a in placed)
    hostiles = sum(by_area.values()) + placed_n
    kill = 0.0
    by_slot = {}
    for a in enc_areas:
        slot = slots[a['slot'] - 1]
        n = by_area[a['id']]
        v = n * sum(p * xp(L) for p, L in zip(ODDS[slot['tier']], LEVELS[slot['monster']]))
        kill += v
        by_slot[slot['monster']] = by_slot.get(slot['monster'], 0) + v
    for a in placed:
        kill += a.get('count', 1) * xp(ROW_LEVEL[a['monster']])
    people = [a for a in sketch['actors'] if not a.get('hostile') and not a.get('npc')]
    people_n = sum(a['count'] for a in people)
    people_xp = sum(a['count'] * xp(PEOPLE_LEVEL[a['monster']]) for a in people)
    enc_polys = [(a['id'], a['polygon']) for a in enc_areas]
    first = {}
    for e in ('entrance:d4_road', 'entrance:d6_pass', 'entrance:dd18_grate', 'entrance:dd15_door',
              'entrance:dd24_doors', 'entrance:dd25_door', 'entrance:dd08_door'):
        ex, ey = pts[e][0]
        best = sorted((poly_distance(poly, ex, ey) * 512 if not pr.poly_mask(poly, scale=4)[int(ey * 4 + 2),
                                                                                            int(ex * 4 + 2)] else 0,
                       aid) for aid, poly in enc_polys)[:2]
        first[e] = [(round(d), n) for d, n in best]
    # POI census (D-15, D-20): devices, chests, dungeon doors, signposts; the boulder field one set piece;
    # not talking NPCs, hazards, landmarks, junctions or arrivals
    spots = []
    for pid, ats in pts.items():
        if pid.startswith('poi:') and kinds.get(pid) not in ('npc', 'trap'):
            spots += [(pid, tuple(a), SET_PIECE_OF.get(pid)) for a in ats]
        elif pid.startswith('entrance:dd'):
            spots += [(pid, tuple(a), None) for a in ats]
    groups = census(spots)
    per_boulder = len(groups) - 1 + sum(1 for s in spots if s[2])   # if the field counted boulder by boulder
    centres = [np.mean([s[1] for s in g], axis=0) for g in groups]
    nn = [min(math.dist(c, d) for j, d in enumerate(centres) if j != i) * 512 for i, c in enumerate(centres)]
    # the 6,000 rule (D-11.5): land farther than 6,000 from anything (POIs, doors, NPCs, landmarks, encounter land)
    anything = np.zeros((N, N), bool)
    for pid, ats in pts.items():
        if pid.startswith(('poi:', 'entrance:', 'landmark:')):
            for x, y in ats:
                anything[int(y), int(x)] = True
    anything |= covered
    dist = ndimage.distance_transform_edt(~anything) * 512
    far = dist * land
    fy, fx = np.unravel_index(int(np.argmax(far)), far.shape)
    wild = float((land & (dist > 3000)).sum() / land.sum())
    box = np.zeros((SIZE, SIZE), bool)
    box[BOX[0] * RES:BOX[1] * RES, BOX[0] * RES:BOX[1] * RES] = True
    landpx = box & ~rim & ~water & ~masks['zone:barrier_lee']
    roads = np.zeros((SIZE, SIZE), bool)
    lanes = np.zeros((SIZE, SIZE), bool)
    for r in sketch['roads']:
        if r['width'] == 'road':
            roads |= pr.line_mask(r['line'], 1.0)
        else:
            lanes |= pr.line_mask(r['line'], 0.6)
    chests = [p for p in plan['points_of_interest'] if p['kind'] == 'chest']
    return {
        'land_cells': int(land.sum()), 'barrier_lee_cells': int((lee & ~small(rim)).sum()),
        'quiet_share': round(float(quiet), 3), 'areas': areas,
        'markers': sum(a['count'] for a in enc_areas), 'hostiles_by_area': by_area, 'placed_hostile': placed_n,
        'hostiles_at_load': round(hostiles, 1), 'kill_xp_per_member': round(kill / 4),
        'kill_xp_by_slot_per_member': {k: round(v / 4) for k, v in by_slot.items()},
        'people_peaceful': people_n, 'people_war_xp_per_member': round(people_xp / 4),
        'height_min_land_box': int(height[landpx].min()), 'height_max_land_box': int(height[landpx].max()),
        'relief_box': int(height[landpx].max() - height[landpx].min()),
        'road_share': round(float((roads & landpx).sum() / landpx.sum()), 4),
        'lane_share': round(float((lanes & landpx & ~roads).sum() / landpx.sum()), 4),
        'first_fight': first,
        'poi_spots': len(groups), 'poi_spots_if_boulders_counted_singly': per_boulder,
        'poi_groups': [[s[0] for s in g] for g in groups],
        'poi_spacing_median': round(float(np.median(nn))), 'poi_spacing_min': round(min(nn)),
        'poi_spacing_max': round(max(nn)),
        'outdoor_chests': len(chests),
        'dungeon_entrances': sum(1 for p in pts if p.startswith('entrance:dd')),
        'farthest_land_from_anything': [round(float(far.max())), [int(fx), int(fy)]],
        'wild_land_share_over_3000': round(wild, 3),
    }


# ---------------------------------------------------------------- the edge matches

def edge_d4(sketch, height):
    """D4's installed west border column (x 19) against D5's planned east border column (x 109), row by row; and the
    strips beyond each border (D4 x 0-18 is its picture of D5, D5 x 110-127 is D4's own land here)."""
    d4 = odm_heights('xeen_d4')
    d5 = height[RES // 2::RES, RES // 2::RES]
    rows = {'y': list(range(N)),
            'd4_border_x19': [int(v) for v in d4[:, 19]],
            'd5_border_x109': [int(v) for v in d5[:, 109]],
            'd4_inside_x20_30': [int(v) for v in d4[:, 20:31].mean(axis=1)],
            'd5_inside_x98_108': [int(v) for v in d5[:, 98:109].mean(axis=1)],
            'd4_rim_x0_18': [int(v) for v in d4[:, 0:19].mean(axis=1)]}
    table = []
    for r in sketch['frame']['rim']:
        if r['side'] != 'east':
            continue
        a, b = r['span']
        sl = slice(int(a), int(min(b, BOX[1] + 1)))
        if sl.stop <= sl.start:
            continue
        b4 = np.array(rows['d4_border_x19'][sl])
        b5 = np.array(rows['d5_border_x109'][sl])
        table.append({'span': [a, b], 'form': r['form'], 'height': r['height'], 'notes': r.get('notes', ''),
                      'd4_border_mean': int(b4.mean()), 'd5_border_mean': int(b5.mean()),
                      'mean_abs_diff': int(np.abs(b4 - b5).mean()), 'max_abs_diff': int(np.abs(b4 - b5).max())})
    road = {'d4_at_x19_y80': int(d4[80, 19]), 'd5_at_x109_y80': int(d5[80, 109]),
            'd4_edge_spans': "D4 L4 frame.rim west: [0,24] level 0; [24,60] ridge 2800-3600; [60,72] ridge "
                             "1800-2300; [72,88] level 1500; [88,104] ridge 1500-2000; [104,128] ridge 2600-3400"}
    return {'rows': rows, 'spans': table, 'road': road}


def edge_d6(sketch, height):
    """The shared D5/D6 border file (edge_d5_d6.json) against D5's planned west border column (x 19)."""
    target = d6_column()
    d5 = height[RES // 2::RES, RES // 2::RES]
    rows = {'y': list(range(N)), 'shared_x19': [int(v) for v in target],
            'd5_border_x19': [int(v) for v in d5[:, 19]],
            'd5_inside_x20_30': [int(v) for v in d5[:, 20:31].mean(axis=1)],
            'd5_rim_x0_18': [int(v) for v in d5[:, 0:19].mean(axis=1)]}
    table = []
    for r in sketch['frame']['rim']:
        if r['side'] != 'west':
            continue
        a, b = r['span']
        sl = slice(int(a), int(min(b, BOX[1] + 1)))
        if sl.stop <= sl.start:
            continue
        t = target[sl]
        p = np.array(rows['d5_border_x19'][sl])
        table.append({'span': [a, b], 'form': r['form'], 'height': r['height'], 'notes': r.get('notes', ''),
                      'shared_mean': int(t.mean()), 'd5_border_mean': int(p.mean()),
                      'mean_abs_diff': int(np.abs(t - p).mean()), 'max_abs_diff': int(np.abs(t - p).max())})
    return {'rows': rows, 'spans': table,
            'pass': {'shared_y64': int(target[64]), 'd5_x19_y64': int(d5[64, 19]), 'span': [62, 66]}}


def edge_d2(height):
    d2 = odm_heights('xeen_d2')
    d5 = height[RES // 2::RES, RES // 2::RES]
    a, b = d2[19, 19:101].astype(int), d5[109, 19:101].astype(int)
    return {'x': [19, 100], 'mean_abs_diff': int(np.abs(a - b).mean()), 'max_abs_diff': int(np.abs(a - b).max()),
            'd2_mean': int(a.mean()), 'd5_mean': int(b.mean())}


def extra_svg(scale, sketch):
    """The signature camera (plan_render draws only the arrival's), the Barrier's arc, the pyramid's footprint, the
    wadis and the boulders."""
    from d5_brief import BARRIER, PYRAMID as FOOT
    s = scale
    parts = []
    for line in WADIS:
        parts.append(f'<polyline points="{pr.pts(line, s)}" fill="none" stroke="#e8d8b0" stroke-width="2" '
                     'stroke-dasharray="2 3" stroke-opacity="0.9"/>')
    parts.append(f'<polyline points="{pr.pts(BARRIER, s)}" fill="none" stroke="#7fe0b8" stroke-width="7" '
                 'stroke-opacity="0.55"/>')
    parts.append(f'<polyline points="{pr.pts(BARRIER, s)}" fill="none" stroke="#1d5a50" stroke-width="2" '
                 'stroke-dasharray="1 9" stroke-linecap="round"/>')
    parts.append(f'<polygon points="{pr.pts(FOOT, s)}" fill="#c8a468" stroke="#3a2a10" stroke-width="1.5"/>')
    parts.append(f'<line x1="{58 * s}" y1="{80 * s}" x2="{70 * s}" y2="{92 * s}" stroke="#3a2a10" '
                 'stroke-width="1"/>')
    parts.append(f'<line x1="{70 * s}" y1="{80 * s}" x2="{58 * s}" y2="{92 * s}" stroke="#3a2a10" '
                 'stroke-width="1"/>')
    for bx, by in [(83, 81), (85, 82), (87, 83), (84, 84), (86, 85), (83, 86), (85, 87)]:
        parts.append(f'<circle cx="{(bx + .5) * s}" cy="{(by + .5) * s}" r="4.5" fill="#8a8078" stroke="#222" '
                     'stroke-width="1"/>')
    for view in sketch['views']:
        if view['id'] != 'view:signature':
            continue
        x, y = view['at']
        lx, ly = view['look']
        ang = math.atan2(ly - y, lx - x)
        dist = math.hypot(lx - x, ly - y)
        p1 = (x + math.cos(ang - math.radians(30)) * dist, y + math.sin(ang - math.radians(30)) * dist)
        p2 = (x + math.cos(ang + math.radians(30)) * dist, y + math.sin(ang + math.radians(30)) * dist)
        col = '#1f6fd1'
        parts.append(f'<polygon points="{pr.pts([(x + .5, y + .5), p1, p2], s)}" fill="{col}" fill-opacity="0.12" '
                     f'stroke="{col}" stroke-width="1.5" stroke-dasharray="6 4"/>')
        parts.append(f'<line x1="{(x + .5) * s}" y1="{(y + .5) * s}" x2="{(lx + .5) * s}" y2="{(ly + .5) * s}" '
                     f'stroke="{col}" stroke-width="2"/>')
        parts.append(f'<circle cx="{(x + .5) * s}" cy="{(y + .5) * s}" r="6" fill="{col}" stroke="#fff" '
                     'stroke-width="1.5"/>')
    return '\n'.join(parts)


def main():
    sys.path.insert(0, str(HERE))
    plan, sketch, project = load()
    OUT.mkdir(exist_ok=True)
    height, water, rim = build_land(sketch)
    img = colour_land(sketch, height, water, rim)
    img.save(OUT / 'colour.png')
    labels = {'kinds': KINDS, 'names': NAMES, 'offsets': OFFSETS,
              'arrows': {'entrance:d4_road': True, 'entrance:d6_pass': True}, 'encounters': ENCOUNTERS,
              'captions': CAPTIONS}
    pr.HERE = HERE            # svg_plan reads <HERE>/<key>/colour.png: point it at phase5
    svg = pr.svg_plan('d5', plan, sketch, project, labels, extra_svg(8, sketch))
    (OUT / 'plan_d5.svg').write_text(svg)
    if '--no-blockout' not in sys.argv:
        bare = colour_land(sketch, height, water, rim, trees=False)
        models = MODELS + barrier_models(sketch) + tree_models(sketch, height, water, np.random.default_rng(21))
        pitch = {'view:arrival': -3.0, 'view:signature': 2.0}
        fovs = {'view:arrival': 76.0, 'view:signature': 60.0}
        for view in sketch['views']:
            name = view['id'].split(':')[1]
            blockout(height, bare, view, models, OUT / f'blockout_{name}.png', fov=fovs[view['id']],
                     annotations=ANNOTATIONS.get(view['id']), pitch=pitch[view['id']], sun=SUN[view['id']])
    result = measure(plan, sketch, project, height, water, rim)
    result['edge_d2_south'] = edge_d2(height)
    (OUT / 'measure.json').write_text(json.dumps(result, indent=1))
    e4 = edge_d4(sketch, height)
    (OUT / 'edge_d4.json').write_text(json.dumps(e4, indent=1))
    e6 = edge_d6(sketch, height)
    (OUT / 'edge_d6.json').write_text(json.dumps(e6, indent=1))
    show = {k: v for k, v in result.items() if k != 'poi_groups'}
    print(json.dumps(show, indent=1))
    for g in result['poi_groups']:
        print('  ', ', '.join(g))
    for s in e4['spans']:
        print('edge d4', s['span'], s['form'], s['d4_border_mean'], s['d5_border_mean'], s['mean_abs_diff'],
              s['max_abs_diff'])
    for s in e6['spans']:
        print('edge d6', s['span'], s['form'], s['shared_mean'], s['d5_border_mean'], s['mean_abs_diff'],
              s['max_abs_diff'])
    print('road', e4['road'], 'pass', e6['pass'])


if __name__ == '__main__':
    main()
