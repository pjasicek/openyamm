#!/usr/bin/env python3
"""MU-3 drawing, MU-4 blockouts, the plan's measurements and the two edge matches for D6 The Forbidden Zone
(A6, phase 5).

    d6_render.py [--no-blockout]   -> phase5/d6/{colour.png, plan_d6.svg, blockout_<view>.png, measure.json,
                                       edge_d1.json, edge_d5.json}

Reads the brief devdocs/xeen/briefs/d6/L1/{plan,sketch,project}.yml, D1's installed heightmap
(assets_dev/worlds/xeen/maps/xeen_d1.odm, read only) and the shared D5/D6 border phase5/edge_d5_d6.json (read only).
Reuses phase2/plan_render.py (the SVG plan) and phase3/d2_render.py (the amber blockout) without editing them. The
land drawn here is the drawing's model of the sketch, not the studio's build. Nothing here is read by the game.
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
OUT = HERE / 'd6'
RES, N = pr.RES, pr.N
SIZE = N * RES
BOX = (19, 109)             # the playable square, both axes
RIM_N, RIM_W = 24, 24
BORDER = 109

BAND_BASE = {'band:lava': 1700, 'band:waste': 1800, 'band:plateau': 2100, 'band:field': 2000, 'band:town': 1680,
             'band:peaks': 2500, 'band:ridge': 2400}
GROUND = {   # sRGB per plan space (MU-2's D6 row: volcanic gravel, lava crust, grey cracked mud, cliffs, flagstone)
    'zone:ash_waste': (124, 120, 116),
    'zone:west_waste': (112, 104, 98),
    'zone:ancient_field': (98, 100, 100),
    'zone:pod_lake_shore': (62, 56, 54),
    'zone:south_peaks': (92, 88, 86),
    'zone:east_peaks': (92, 88, 86),
    'zone:east_ridge': (82, 80, 82),
    'zone:pass_east': (118, 112, 104),
    'zone:griffin_pass': (112, 106, 98),
    'zone:mountain_road': (110, 104, 96),
    'zone:ash_fork_flats': (134, 128, 120),
    'zone:bone_road': (128, 122, 114),
    'zone:freeda_camp': (124, 114, 100),
    'zone:alamar_plateau': (56, 56, 62),
    'zone:alamar_approach': (72, 72, 78),
    'zone:hot_spring': (96, 100, 104),
    'zone:obelisk_knoll': (78, 76, 78),
    'zone:archer_camp': (124, 110, 90),
    'zone:pod_crust': (44, 40, 40),
    'town:necropolis': (118, 114, 110),
    'zone:np_square': (150, 146, 140),
}
ORDER = ['zone:ash_waste', 'zone:west_waste', 'zone:ancient_field', 'zone:pod_lake_shore', 'zone:south_peaks',
         'zone:east_peaks', 'zone:east_ridge', 'zone:pass_east', 'zone:griffin_pass', 'zone:mountain_road',
         'zone:ash_fork_flats', 'zone:bone_road', 'zone:freeda_camp', 'zone:alamar_plateau', 'zone:alamar_approach',
         'zone:hot_spring', 'zone:obelisk_knoll', 'zone:archer_camp', 'zone:pod_crust', 'town:necropolis',
         'zone:np_square']
CLEAR = ['town:necropolis', 'zone:hot_spring', 'zone:obelisk_knoll', 'zone:archer_camp', 'zone:freeda_camp',
         'zone:griffin_pass', 'zone:np_square']
RIVER_LEVELS = {'water:burning_channel': (1550, 1450), 'water:slag_run': (1550, 1480),
                'water:north_falls': (1550, 1500)}
LAVA = np.array((236, 104, 28))
LAVA_HOT = np.array((255, 196, 80))


def d1_heights():
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_odm_file
    data = parse_odm_file(ROOT / 'assets_dev/worlds/xeen/maps/xeen_d1.odm')
    return np.array(data['payload']['height_map'], int).reshape(N, N) * 32


def d5_column():
    return np.array(json.loads((HERE / 'edge_d5_d6.json').read_text())['heights_by_y'], float)


def rim_profiles(sketch):
    """The strips beyond the south and east borders as heights per cell along the side (the drawing's reading of the
    sketch's rim forms)."""
    south = np.zeros(N)
    east = np.zeros(N)
    for r in sketch['frame']['rim']:
        if r['side'] not in ('south', 'east'):
            continue
        a, b = r.get('span', [0, 128])
        for c in range(int(a), int(b)):
            if r['form'] == 'level':
                v = r['height']
            else:
                lo, hi = r['height']
                v = lo + (hi - lo) * (0.5 + 0.5 * math.sin(c / 3.7 + (1.3 if r['side'] == 'east' else 0.4)))
            (south if r['side'] == 'south' else east)[c] = v
    return south, east


def build_land(sketch):
    """Height (map units) per raster pixel from the sketch's bands, points, ridges, cliffs, lava, roads and the two
    shared borders."""
    height = np.full((SIZE, SIZE), 1800.0)
    for band in sketch['heights']['bands']:
        if band['band'] == 'band:rim_sea':
            continue
        height[pr.poly_mask(band['polygon'])] = BAND_BASE[band['band']]
    yy, xx = np.mgrid[0:SIZE, 0:SIZE] / RES
    height = ndimage.gaussian_filter(height, 3 * RES)
    border = [p for p in sketch['heights']['points'] if p['at'][0] >= BORDER or p['at'][1] >= BORDER]
    for point in sketch['heights'].get('points', []):
        if point in border:
            continue
        px, py = point['at']
        r = 6.0 if point['h'] > 2900 else (4.5 if point['h'] > 2200 else 3.5)
        d = np.hypot(xx - px - 0.5, yy - py - 0.5)
        t = np.clip(1 - d / r, 0, 1)
        w = t * t * (3 - 2 * t)
        height = height * (1 - w) + point['h'] * w
    for ridge in sketch['heights'].get('ridges', []):
        m = pr.line_mask(ridge['line'], ridge.get('width', 2))
        dist = ndimage.distance_transform_edt(~m) / RES
        w = np.clip(1 - dist / (ridge.get('slope', 3) + 1.5), 0, 1)
        height = np.maximum(height, height * (1 - w) + ridge['height'] * w)
    rng = np.random.default_rng(6)
    noise = ndimage.gaussian_filter(rng.normal(size=(SIZE, SIZE)), 3 * RES)
    noise /= np.abs(noise).max() + 1e-6
    rough = ndimage.gaussian_filter(rng.normal(size=(SIZE, SIZE)), 0.6 * RES)
    rough /= np.abs(rough).max() + 1e-6
    masks = pr.space_masks(sketch)
    calm = np.zeros((SIZE, SIZE), bool)
    for s in CLEAR + ['zone:pod_crust', 'zone:alamar_approach']:
        calm |= masks.get(s, calm)
    calm = ndimage.binary_dilation(calm, iterations=RES)
    steep = np.clip((height - 1900) / 1100, 0, 1)
    height += np.where(calm, 0, noise * 140 + rough * (40 + 320 * steep))
    # flat town and camps
    for space, target in [('town:necropolis', 1650), ('zone:hot_spring', 1800), ('zone:obelisk_knoll', 2050),
                          ('zone:archer_camp', 1950), ('zone:freeda_camp', 1800), ('zone:alamar_approach', None)]:
        m = masks[space]
        soft = ndimage.gaussian_filter(m.astype(float), RES)
        if target is None:     # the approach: a ramp from 1,800 at its foot to 2,050 at the gate
            target = 1800 + np.clip((63 - yy) / 7, 0, 1) * 250
        height = height * (1 - soft) + target * soft
    # Alamar's mesa: a cliff into the moat (keep the plateau high right to its edge)
    plateau = masks['zone:alamar_plateau'] & ~masks['zone:alamar_approach']
    height[plateau] = np.maximum(height[plateau], 2050)
    # the lava: shores come down to it, except the mesa's cliffs
    lava = np.zeros((SIZE, SIZE), bool)
    for body in sketch['water']['bodies']:
        if body['id'] == 'water:rim_sea':
            continue
        m = pr.poly_mask(body['polygon'])
        dist = ndimage.distance_transform_edt(~m) / RES
        cap = body['level'] + 40 + 160 * dist
        shore = ~m & ~plateau & (dist < 7)
        height[shore] = np.minimum(height[shore], cap[shore])
        islet = np.zeros_like(m)
        for point in sketch['heights']['points']:
            if 'islet' in (point.get('notes') or ''):
                px, py = point['at']
                islet |= np.hypot(xx - px - 0.5, yy - py - 0.5) < 0.9
        height[m & islet] = np.maximum(height[m & islet], body['level'] + 60)
        height[m & ~islet] = body['level']
        lava |= m & ~islet
    for river in sketch['water']['rivers']:
        line = river['line']
        m = pr.line_mask(line, river.get('width_cells', 1.5))
        bank = ndimage.binary_dilation(m, iterations=RES) & ~m
        a, b = RIVER_LEVELS[river['id']]
        seg = [math.dist(p, q) for p, q in zip(line, line[1:])]
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
        level = a + (b - a) * best_t
        on = m[ys, xs]
        height[ys[on], xs[on]] = level[on]
        off = ~on
        height[ys[off], xs[off]] = np.maximum(level[off] + 50, np.minimum(height[ys[off], xs[off]], level[off] + 240))
        lava |= m
    # road beds: soften the land under the roads toward their median
    soft = ndimage.gaussian_filter(height, RES)
    for road in sketch.get('roads', []):
        m = pr.line_mask(road['line'], 1.0) & ~lava
        height[m] = soft[m]
    # the shared borders: D1's installed row at y 109 and the D5 file's column at x 109, blended over 6 cells
    # inward; the strips beyond them run out to the sketch's rim forms
    d1 = d1_heights()
    row = d1[19].astype(float)
    col = d5_column()
    ci = np.clip(xx.astype(int), 0, N - 1)
    ri = np.clip(yy.astype(int), 0, N - 1)
    k = np.clip((yy - (BORDER - 6)) / 6.0, 0, 1)
    k = k * k * (3 - 2 * k)
    height = height * (1 - k) + row[ci] * k
    k = np.clip((xx - (BORDER - 6)) / 6.0, 0, 1)
    k = k * k * (3 - 2 * k)
    corner = np.clip((yy - (BORDER - 4)) / 4.0, 0, 1)     # D1's row wins in the shared corner
    target = col[ri] * (1 - corner) + row[ci] * corner
    height = height * (1 - k) + target * k
    south, east = rim_profiles(sketch)
    beyond_s = yy >= BORDER + 1
    t = np.clip((yy - BORDER - 1) / 8.0, 0, 1)
    height[beyond_s] = (row[ci] * (1 - t) + south[ci] * t)[beyond_s]
    beyond_e = xx >= BORDER + 1
    t = np.clip((xx - BORDER - 1) / 8.0, 0, 1)
    height[beyond_e] = (col[ri] * (1 - t) + east[ri] * t)[beyond_e]
    outside = beyond_s | beyond_e
    smooth = ndimage.gaussian_filter(height, 1.5 * RES) + noise * 160 + rough * 110
    w = ndimage.gaussian_filter(outside.astype(float), RES) * outside
    height = height * (1 - w) + smooth * w
    # the border cells themselves carry the shared values exactly (the drawing's sampling points)
    for x in range(N):
        height[BORDER * RES:(BORDER + 1) * RES, x * RES:(x + 1) * RES] = row[x]
    for y in range(BORDER - 3):
        height[y * RES:(y + 1) * RES, BORDER * RES:(BORDER + 1) * RES] = col[y]
    # the rims: north (y < 24) and west (x < 24) fall to the stars
    rim = (yy < RIM_N) | (xx < RIM_W)
    height[rim] = 0
    lava &= ~rim
    return height, lava, rim


def colour_land(sketch, height, lava, rim):
    rgb = np.zeros((SIZE, SIZE, 3))
    rgb[:] = (110, 104, 98)
    masks = pr.space_masks(sketch)
    jitter = ndimage.gaussian_filter(np.random.default_rng(8).normal(size=(SIZE, SIZE)), 1.5 * RES)
    jitter /= np.abs(jitter).max() + 1e-6
    for space in ORDER:
        if space in masks:
            soft = ndimage.gaussian_filter(masks[space].astype(float), 1.6 * RES)
            soft = np.clip(soft + jitter * 0.35 * soft * (1 - soft) * 4, 0, 1)[..., None]
            rgb = rgb * (1 - soft) + np.array(GROUND[space]) * soft
    # ash: lighter grey streaks on the flats; dark basalt high up
    ash = np.clip(jitter * 1.4, 0, 1) * (height < 2200)
    rgb = rgb * (1 - 0.25 * ash[..., None]) + np.array((168, 162, 156)) * 0.25 * ash[..., None]
    for road in sketch.get('roads', []):
        m = pr.line_mask(road['line'], 0.8 if road.get('width') == 'road' else 0.5)
        flag = road.get('surface') == 'road_flagstone'
        rgb[m] = (170, 166, 156) if flag else ((150, 138, 118) if road.get('width') == 'road' else (128, 118, 102))
    gy, gx = np.gradient(height, 512 / RES)
    slope = np.hypot(gx, gy)
    rock = np.clip((slope - 0.38) * 2.2, 0, 1)
    rgb = rgb * (1 - rock[..., None]) + np.array((58, 56, 60)) * rock[..., None]
    # lava: hot cores, darker crusted edges, a red glow on the ground round it
    dist_in = ndimage.distance_transform_edt(lava) / RES
    core = np.clip(dist_in / 2.5, 0, 1)
    lava_rgb = LAVA[None, None, :] * (1 - core[..., None]) + LAVA_HOT[None, None, :] * core[..., None]
    crack = np.clip(ndimage.gaussian_filter(np.random.default_rng(12).normal(size=(SIZE, SIZE)), 0.8 * RES) * 6, -1, 1)
    lava_rgb = lava_rgb * (1 - 0.35 * np.clip(-crack, 0, 1))[..., None] + np.array((60, 20, 10)) * \
        (0.35 * np.clip(-crack, 0, 1))[..., None]
    rgb[lava] = lava_rgb[lava]
    dist_out = ndimage.distance_transform_edt(~lava) / RES
    glow = np.clip(1 - dist_out / 2.0, 0, 1) * ~lava
    rgb = rgb * (1 - 0.45 * glow[..., None]) + np.array((150, 50, 24)) * 0.45 * glow[..., None]
    light = np.array([-0.55, -0.65, 0.52])
    nx, ny, nz = -gx * 2.2, -gy * 2.2, np.ones_like(gx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    shade = np.clip(0.55 + 0.6 * (nx * light[0] + ny * light[1] + nz * light[2]) / norm, 0.35, 1.15)
    shade[lava] = 1.0
    rgb = rgb * shade[..., None]
    stars = np.zeros((SIZE, SIZE, 3))
    stars[:] = (10, 12, 26)
    rng = np.random.default_rng(3)
    for y, x in rng.integers(0, SIZE, size=(2600, 2)):
        stars[y, x] = rng.integers(140, 255)
    rgb[rim] = stars[rim]
    cliff = ndimage.binary_dilation(~rim, iterations=int(1.2 * RES)) & rim
    rgb[cliff] = (78, 72, 78)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    # Ancient metal surfacing in the field: short plates and spars of teal steel
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(11)
    field = masks['zone:ancient_field']
    ys, xs = np.nonzero(field[::RES, ::RES])
    for cy, cx in zip(ys, xs):
        if rng.random() > 0.16:
            continue
        x, y = (cx + rng.random()) * RES, (cy + rng.random()) * RES
        if rim[int(min(y, SIZE - 1)), int(min(x, SIZE - 1))]:
            continue
        a = rng.random() * math.pi
        L = RES * (0.6 + rng.random() * 1.6)
        draw.line([(x - math.cos(a) * L, y - math.sin(a) * L), (x + math.cos(a) * L, y + math.sin(a) * L)],
                  fill=(74, 112, 116), width=max(2, int(RES * 0.35)))
    # dead black trees, few, round Necropolis and on the Bone Road
    for space, density in [('zone:bone_road', 0.08), ('zone:ash_fork_flats', 0.03), ('zone:west_waste', 0.02)]:
        ys, xs = np.nonzero(masks[space][::RES, ::RES])
        for cy, cx in zip(ys, xs):
            if rng.random() > density:
                continue
            x, y = (cx + rng.random()) * RES, (cy + rng.random()) * RES
            draw.line([(x, y), (x, y - RES * 0.9)], fill=(30, 26, 26), width=2)
    return img


# ---------------------------------------------------------------- labels for plan_render.svg_plan

KINDS = {
    'entrance:south_road': 'entrance', 'entrance:east_pass': 'entrance', 'entrance:necropolis_gate': 'entrance',
    'entrance:np_gate': 'dungeon', 'entrance:dd17_gate': 'dungeon', 'entrance:fd01_stair': 'dungeon',
    'entrance:dd16_hatch': 'dungeon', 'entrance:dd22_hatch': 'dungeon', 'entrance:dd21_stair': 'dungeon',
    'entrance:dd10c_adit': 'dungeon',
    'poi:archers_chest': 'chest', 'poi:griffin_nest': 'chest', 'poi:prospector': 'chest', 'poi:ancient_locker': 'chest',
    'poi:pilgrim_cart': 'chest', 'poi:spring_pilgrim': 'chest',
    'poi:ambrose': 'npc', 'poi:freeda': 'npc', 'poi:mine_mouths': 'junction',
    'poi:fork_signpost': 'junction', 'poi:zone_sign': 'junction', 'junction:ash_fork': 'junction',
    'junction:bone_fork': 'junction',
    'landmark:alamar': 'landmark', 'landmark:corak_pod': 'landmark', 'landmark:sheltem_pod': 'landmark',
    'landmark:necropolis': 'landmark', 'landmark:north_falls': 'landmark', 'landmark:west_falls': 'landmark',
    'landmark:broken_pyramid': 'landmark', 'landmark:cinder_cone': 'landmark', 'landmark:ridge_tower': 'landmark',
}
NAMES = {
    'entrance:south_road': 'from D1 Castleview (x 64)',
    'entrance:east_pass': 'from D5 (y 64)',
    'entrance:necropolis_gate': '',
    'entrance:np_gate': 'Necropolis gate (pass)',
    'entrance:dd17_gate': 'DD-17 Castle Alamar (2 leaves)',
    'entrance:fd01_stair': '',
    'entrance:dd16_hatch': "DD-16 Corak's hatch",
    'entrance:dd22_hatch': "DD-22 Sheltem's pod (sealed)",
    'entrance:dd21_stair': 'DD-21 sewer stair',
    'entrance:dd10c_adit': 'DD-10C north adit',
    'junction:ash_fork': 'Ash Fork', 'junction:bone_fork': 'Bone Fork',
    'poi:obelisk': 'Obelisk',
    'poi:fountain_resilience': 'Fountain of Super Resilience',
    'poi:warding_well': 'Well of Warding',
    'poi:books': 'Books of the Dead',
    'poi:skull': '', 'poi:mirror': 'mirror + skull', 'poi:barrel': 'barrel',
    'poi:genie_pinnacle': 'genie lamp', 'poi:genie_islet': 'genie (islet)', 'poi:genie_crag': 'genie lamp',
    'poi:archers_chest': '', 'poi:griffin_nest': 'griffin nest', 'poi:prospector': 'prospector',
    'poi:ancient_locker': 'Ancient locker', 'poi:pilgrim_cart': "pilgrim's cart", 'poi:spring_pilgrim': '',
    'poi:fork_signpost': '', 'poi:zone_sign': '"The Forbidden Zone."',
    'poi:ambrose': 'Ambrose + griffin', 'poi:freeda': 'Freeda', 'poi:mine_mouths': 'mines',
    'landmark:alamar': 'CASTLE ALAMAR', 'landmark:corak_pod': "CORAK'S POD",
    'landmark:sheltem_pod': "SHELTEM'S POD", 'landmark:necropolis': '',
    'landmark:north_falls': 'lava falls', 'landmark:west_falls': 'lava falls',
    'landmark:broken_pyramid': 'broken pyramid', 'landmark:cinder_cone': 'cinder cone', 'landmark:ridge_tower': 'watchtower',
}
OFFSETS = {
    'entrance:south_road': (10, 16, 'start'),
    'entrance:east_pass': (-6, 22, 'end'),
    'entrance:np_gate': (10, 4, 'start'),
    'entrance:dd17_gate': (10, 18, 'start'),
    'entrance:dd16_hatch': (-8, 18, 'end'),
    'entrance:dd22_hatch': (10, 16, 'start'),
    'entrance:dd21_stair': (10, 16, 'start'),
    'entrance:dd10c_adit': (10, 18, 'start'),
    'junction:ash_fork': (-10, 4, 'end'),
    'junction:bone_fork': (-10, -8, 'end'),
    'poi:obelisk': (10, 4, 'start'),
    'poi:fountain_resilience': (10, -8, 'start'),
    'poi:warding_well': (-10, 16, 'end'),
    'poi:books': (-4, -10, 'end'),
    'poi:mirror': (10, 2, 'start'),
    'poi:barrel': (-8, 14, 'end'),
    'poi:genie_pinnacle': (10, 4, 'start'),
    'poi:genie_islet': (-10, -6, 'end'),
    'poi:genie_crag': (10, 4, 'start'),
    'poi:griffin_nest': (10, -6, 'start'),
    'poi:prospector': (-10, 4, 'end'),
    'poi:ancient_locker': (10, 4, 'start'),
    'poi:pilgrim_cart': (-10, -6, 'end'),
    'poi:zone_sign': (-8, -12, 'end'),
    'poi:ambrose': (-10, 4, 'end'),
    'poi:freeda': (10, 4, 'start'),
    'poi:mine_mouths': (0, -10, 'middle'),
    'landmark:alamar': (14, -14, 'start'),
    'landmark:corak_pod': (14, -10, 'start'),
    'landmark:sheltem_pod': (14, -10, 'start'),
    'landmark:north_falls': (10, 16, 'start'),
    'landmark:west_falls': (12, 16, 'start'),
    'landmark:broken_pyramid': (10, 14, 'start'),
}
ENCOUNTERS = {
    'pop:field_gazers': {'colour': '#c0282d'},
    'pop:alamar_robots': {'colour': '#1f7a8a'},
    'pop:lava_dwellers': {'colour': '#e07a1f'},
    'pop:west_griffins': {'colour': '#8a3c00'},
    'pop:east_griffins': {'colour': '#8a3c00'},
    'pop:archers': {'colour': '#8a3cc0'},
}

# Blockout models: (cell x, cell y, base height or None for the ground, height, half width in cells, colour)
MODELS = [
    # Castle Alamar on its mesa: curtain, keep, four towers, energy-field pylons on the approach
    (51, 46, None, 650, 5.0, (54, 70, 74)),
    (51, 45, None, 1500, 1.8, (44, 62, 66)),
    (46.5, 41.5, None, 1150, 0.9, (48, 64, 70)),
    (55.5, 41.5, None, 1150, 0.9, (48, 64, 70)),
    (46.5, 50.5, None, 1050, 0.9, (48, 64, 70)),
    (55.5, 50.5, None, 1050, 0.9, (48, 64, 70)),
    (51, 51.5, None, 760, 1.4, (58, 74, 78)),           # the gatehouse
    (48.5, 57, None, 520, 0.15, (90, 210, 230)),         # energy pylons in pairs on the approach
    (53.5, 57, None, 520, 0.15, (90, 210, 230)),
    (48.5, 60, None, 520, 0.15, (90, 210, 230)),
    (53.5, 60, None, 520, 0.15, (90, 210, 230)),
    # Escape Pod 1 nose-up in the lava, its hatch's crust; Escape Pod 2 upright in its crater
    (72, 67, 1450, 1700, 0.55, (110, 70, 52)),            # the pod's hull standing nose-up out of the lava
    (72, 67, 1450, 2000, 0.3, (126, 82, 60)),             # its nose
    (73.5, 69, 1450, 250, 0.9, (60, 44, 40)),             # the crust and the hatch
    (78, 38, None, 1100, 0.9, (80, 92, 96)),
    # Ambrose's tent and the griffin's rock, Freeda's tent, the archers' tents
    (60.5, 94.5, None, 220, 0.6, (140, 120, 90)),
    (62.5, 95, None, 380, 0.4, (120, 96, 60)),
    (100, 69, None, 220, 0.5, (130, 110, 84)),
    (33, 85.5, None, 240, 0.6, (120, 96, 70)),
    (35.5, 86.5, None, 240, 0.6, (120, 96, 70)),
    (33.5, 87.5, None, 240, 0.6, (120, 96, 70)),
    # the obelisk, the broken pyramid
    (30, 62, None, 420, 0.2, (150, 150, 140)),
    (84, 98, None, 520, 1.6, (128, 124, 110)),
]

ANNOTATIONS = {
    'view:arrival': [
        ('Castle Alamar on its mesa, lit windows, energy fields', 51, 46, 1500),
        ("Corak's pod nose-up in the lava lake", 72, 67, 1500),
        ('Northern Lava Falls at the rim', 45, 25, 100),
        ('Ancient field: metal surfacing', 84, 42, 200),
        ('Ash Fork', 66, 85, 60),
        ('road down from Griffin Pass', 65, 91, 40),
        ('Obelisk Knoll, west rim', 30, 62, 400),
        ("archers' camp", 34, 86, 240),
    ],
    'view:signature': [
        ("Corak's pod, nose-up, hull glowing", 72, 67, 1500),
        ('the hatch on the crust', 74, 70, 300),
        ('Castle Alamar: lit windows, energy fields', 51, 46, 1500),
        ('energy pylons on the approach', 51, 58, 520),
        ('lava moat round the mesa', 57, 39, 0),
        ('genie islet', 66, 63, 60),
    ],
}


def house_models(plan, sketch):
    buildings = {b['id']: b for s in plan['spaces'] for b in s.get('buildings', []) or []}
    out = []
    for d in sketch['districts']:
        for plot in d.get('plots', []) or []:
            b = buildings[plot['building']]
            front, depth = b['footprint_cells'][(plot.get('index') or 1) - 1]
            wx, wy = (front, depth) if plot['facing'] in 'ns' else (depth, front)
            x, y = plot['at']
            tall = 900 if plot['building'] in ('building:np_guild', 'building:np_temple') else 520
            colour = (88, 88, 92) if 'houses' not in plot['building'] else (104, 100, 96)
            out.append((x + wx / 2 - 0.5, y + wy / 2 - 0.5, None, tall, max(wx, wy) / 2, colour))
            out.append((x + wx / 2 - 0.5, y + wy / 2 - 0.5, None, tall + 240, max(wx, wy) / 3, (60, 60, 66)))
    # the walls: blocks every 2 cells along the outline, towers at the corners and the gatehouse
    x0, y0, x1, y1 = 82, 74, 100, 90
    for x in np.arange(x0, x1 + 0.1, 2.0):
        out.append((x, y0, None, 700, 1.0, (96, 94, 92)))
        out.append((x, y1, None, 700, 1.0, (96, 94, 92)))
    for y in np.arange(y0, y1 + 0.1, 2.0):
        out.append((x0, y, None, 700, 1.0, (96, 94, 92)))
        out.append((x1, y, None, 700, 1.0, (96, 94, 92)))
    for cx, cy in [(x0, y0), (x1, y0), (x0, y1), (x1, y1), (89.5, y0), (92.5, y0)]:
        out.append((cx, cy, None, 1000, 0.8, (84, 82, 82)))
    return out


def metal_models(sketch, height, rng):
    """Ancient plates and spars standing out of the field (thin slabs), for the blockout only."""
    masks = pr.space_masks(sketch)
    out = []
    ys, xs = np.nonzero(masks['zone:ancient_field'][::RES, ::RES])
    for cy, cx in zip(ys, xs):
        if rng.random() > 0.05:
            continue
        x, y = cx + rng.random(), cy + rng.random()
        if height[int(y * RES), int(x * RES)] < 10:
            continue
        out.append((x - 0.5, y - 0.5, None, 200 + rng.random() * 500, 0.2 + rng.random() * 0.5, (70, 100, 104)))
    return out


# ---------------------------------------------------------------- measurements against MAPS

def poly_distance(poly, x, y):
    best = 1e9
    pts = poly + [poly[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        t = max(0, min(1, ((x - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - x0 - t * dx, y - y0 - t * dy))
    if pr.poly_mask(poly, scale=4)[min(int(y * 4), N * 4 - 1), min(int(x * 4), N * 4 - 1)]:
        return 0.0
    return best


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


ODDS = {1: (0.9, 0.08, 0.02), 2: (0.7, 0.2, 0.1), 3: (0.5, 0.3, 0.2), 4: (0.3, 0.4, 0.3), 5: (0.1, 0.5, 0.4)}
LEVELS = {'Xeen Eye': (40, 50, 65), 'Xeen Roc': (30, 38, 48), 'Xeen Robot': (50, 62, 75)}
# placed actors' levels in ACTORS order (the archers stand in for A2's requested tiers 44 and 50)
PLACED_LEVELS = [55, 55, 62, 55, 62, 55, 62, 44, 50]
MARKER_AREAS = ('pop:field_gazers', 'pop:alamar_robots', 'pop:west_griffins', 'pop:east_griffins')


def xp(level):
    return level * (level + 10)


def measure(plan, sketch, project, height, lava, rim):
    kinds = {p['id']: p['kind'] for p in plan['points_of_interest']}
    pts = {}
    for p in sketch['points']:
        pts.setdefault(p['id'], []).append(p['at'])
    small = lambda m: m[RES // 2::RES, RES // 2::RES]
    land = np.zeros((N, N), bool)
    land[BOX[0]:BOX[1], BOX[0]:BOX[1]] = True
    land &= ~small(rim) & ~small(lava)
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
    slots = project['map_stats']['slots']
    avg = {i + 1: sum(s['per_marker']) / 2 for i, s in enumerate(slots)}
    by_id = {a['id']: a for a in enc_areas}
    by_area = {aid: by_id[aid]['count'] * avg[by_id[aid]['slot']] for aid in MARKER_AREAS}
    placed = [a for a in sketch['actors'] if a.get('hostile')]
    placed_n = sum(a.get('count', 1) for a in placed)
    hostiles = sum(by_area.values()) + placed_n
    kill = 0.0
    kill_by = {}
    for aid, n in by_area.items():
        slot = slots[by_id[aid]['slot'] - 1]
        o = ODDS[slot['tier']]
        v = n * sum(p * xp(L) for p, L in zip(o, LEVELS[slot['monster']]))
        kill += v
        kill_by[aid] = round(v / 4)
    placed_xp = sum(a.get('count', 1) * xp(L) for a, L in zip(placed, PLACED_LEVELS))
    kill += placed_xp
    kill_by['placed'] = round(placed_xp / 4)
    # first fights: the nearest encounter polygon (markers or placed camps) from each arrival
    enc_polys = [(a['id'], a['polygon']) for a in enc_areas]
    first = {}
    for e in ('entrance:south_road', 'entrance:east_pass', 'entrance:necropolis_gate'):
        ex, ey = pts[e][0]
        best = sorted((poly_distance(poly, ex + 0.5, ey + 0.5) * 512, aid) for aid, poly in enc_polys)[:2]
        first[e] = [(round(d), n) for d, n in best]
    doors = door_points(plan, sketch)
    door_min = min((poly_distance(poly, x, y) * 512, name, aid) for name, _, (x, y) in doors
                   for aid, poly in enc_polys)
    # Ambrose's camp and the hatch's crust: distance to the nearest fight
    camps = {}
    for pid in ('poi:ambrose', 'entrance:dd16_hatch', 'entrance:dd10c_adit', 'poi:freeda'):
        x, y = pts[pid][0]
        camps[pid] = sorted((round(poly_distance(poly, x + 0.5, y + 0.5) * 512), aid) for aid, poly in enc_polys)[0]
    # POI census (D-15/D-20): devices, chests, dungeon doors, gates, the mirror, service doors; not residences,
    # talking NPCs, dressing, landmarks, junctions or arrivals
    spots = []
    for pid, ats in pts.items():
        if pid.startswith('poi:') and kinds.get(pid) not in ('npc', 'trap', 'dressing'):
            spots += [(pid, (a[0] + 0.5, a[1] + 0.5)) for a in ats]
        elif pid.startswith(('entrance:dd', 'entrance:fd')) or pid == 'entrance:np_gate':
            spots += [(pid, (a[0] + 0.5, a[1] + 0.5)) for a in ats]
    services = [(name, (x, y)) for name, service, (x, y) in doors if service != 'residence']
    groups = census(spots + services)
    centres = [np.mean([s[1] for s in g], axis=0) for g in groups]
    nn = [min(math.dist(c, d) for j, d in enumerate(centres) if j != i) * 512 for i, c in enumerate(centres)]
    # the 6,000 rule (D-11.5): land farther than 6,000 from anything (POIs, doors, NPCs, landmarks, encounter land)
    anything = np.zeros((N, N), bool)
    for pid, ats in pts.items():
        if pid.startswith(('poi:', 'entrance:', 'landmark:')):
            for x, y in ats:
                anything[min(int(y), N - 1), min(int(x), N - 1)] = True
    for _, _, (x, y) in doors:
        anything[min(int(y), N - 1), min(int(x), N - 1)] = True
    anything |= covered
    dist = ndimage.distance_transform_edt(~anything) * 512
    far = dist * land
    fy, fx = np.unravel_index(int(np.argmax(far)), far.shape)
    wild = float((land & (dist > 3000)).sum() / land.sum())
    box = np.zeros((SIZE, SIZE), bool)
    box[BOX[0] * RES:BOX[1] * RES, BOX[0] * RES:BOX[1] * RES] = True
    landpx = box & ~rim & ~lava
    roads = np.zeros((SIZE, SIZE), bool)
    lanes = np.zeros((SIZE, SIZE), bool)
    for r in sketch['roads']:
        if r['width'] == 'road':
            roads |= pr.line_mask(r['line'], 1.0)
        else:
            lanes |= pr.line_mask(r['line'], 0.6)
    lava_cells = {b['id']: int(small(pr.poly_mask(b['polygon'])).sum()) for b in sketch['water']['bodies']
                  if b['id'] != 'water:rim_sea'}
    chests = [p for p in plan['points_of_interest'] if p['kind'] == 'chest']
    # view distances (signature: the pod and the keep from the camera)
    views = {}
    for v in sketch['views']:
        x, y = v['at']
        views[v['id']] = {'to_alamar': round(math.dist((x, y), (51, 46)) * 512),
                          'to_pod': round(math.dist((x, y), (72, 67)) * 512)}
    return {
        'land_cells': int(land.sum()), 'lava_cells': lava_cells,
        'lava_share_of_box': round(float(small(lava)[BOX[0]:BOX[1], BOX[0]:BOX[1]].mean()), 3),
        'quiet_share': round(float(quiet), 3), 'areas': areas,
        'markers': sum(by_id[a]['count'] for a in MARKER_AREAS), 'hostiles_by_area': by_area,
        'placed_hostile': placed_n, 'hostiles_at_load': round(hostiles, 1),
        'kill_xp_per_member': round(kill / 4), 'kill_xp_by_area_per_member': kill_by,
        'height_min_land_box': int(height[landpx].min()), 'height_max_land_box': int(height[landpx].max()),
        'relief_box': int(height[landpx].max() - height[landpx].min()),
        'road_share': round(float((roads & landpx).sum() / landpx.sum()), 3),
        'lane_share': round(float((lanes & landpx & ~roads).sum() / landpx.sum()), 3),
        'first_fight': first,
        'nearest_fight_to_a_town_door': [round(door_min[0]), door_min[1], door_min[2]],
        'nearest_fight_to': camps,
        'poi_spots': len(groups), 'poi_groups': [[s[0] for s in g] for g in groups],
        'poi_spacing_median': round(float(np.median(nn))), 'poi_spacing_min': round(min(nn)),
        'poi_spacing_max': round(max(nn)),
        'service_doors': len(services), 'house_doors': len(doors), 'outdoor_chests': len(chests),
        'dungeon_entrances': sum(1 for p in pts if p.startswith(('entrance:dd', 'entrance:fd'))),
        'farthest_land_from_anything': [round(float(far.max())), [int(fx), int(fy)]],
        'wild_land_share_over_3000': round(wild, 3),
        'views': views,
    }


# ---------------------------------------------------------------- the edge matches

def edge_d1(sketch, height):
    """D1's installed border row (y 19) against D6's planned border row (y 109), x 0-127, and the strips beyond each
    border (D1 y 0-18 is its picture of D6; D6 y 110-127 its picture of D1)."""
    d1 = d1_heights()
    d6 = height[RES // 2::RES, RES // 2::RES]
    rows = {'x': list(range(N)),
            'd1_border_y19': [int(v) for v in d1[19]],
            'd6_border_y109': [int(v) for v in d6[BORDER]],
            'd1_inside_y20_30': [int(v) for v in d1[20:31].mean(axis=0)],
            'd6_inside_y98_108': [int(v) for v in d6[98:109].mean(axis=0)],
            'd1_rim_y0_18': [int(v) for v in d1[0:19].mean(axis=0)],
            'd6_rim_y110_127': [int(v) for v in d6[110:128].mean(axis=0)]}
    spans = [(r['span'], r['form'], r['height'], r.get('notes', '')) for r in sketch['frame']['rim']
             if r['side'] == 'south']
    table = []
    for (a, b), form, h, notes in spans:
        sl = slice(int(a), int(b))
        b1 = np.array(rows['d1_border_y19'][sl])
        b6 = np.array(rows['d6_border_y109'][sl])
        table.append({'span': [a, b], 'form': form, 'height': h, 'notes': notes,
                      'd1_border_mean': int(b1.mean()), 'd6_border_mean': int(b6.mean()),
                      'mean_abs_diff': int(np.abs(b1 - b6).mean()), 'max_abs_diff': int(np.abs(b1 - b6).max())})
    road = {'d1_at_x64_y19': int(d1[19, 64]), 'd6_at_x64_y109': int(d6[BORDER, 64]),
            'd1_edge_spans': "D1 L4 frame.rim north: [0,24] level 0; [24,59] ridge 2600-3400; [59,70] level 2000; "
                             "[70,128] ridge 2800-3600 (D1's picture of D6)"}
    return {'rows': rows, 'spans': table, 'road': road}


def edge_d5(sketch, height):
    """The shared file's column (edge_d5_d6.json heights_by_y) against D6's planned border column (x 109)."""
    col = d5_column()
    d6 = height[RES // 2::RES, RES // 2::RES]
    rows = {'y': list(range(N)), 'file_x109': [int(v) for v in col], 'd6_border_x109': [int(v) for v in d6[:, BORDER]],
            'd6_inside_x98_108': [int(v) for v in d6[:, 98:109].mean(axis=1)],
            'd6_rim_x110_127': [int(v) for v in d6[:, 110:128].mean(axis=1)]}
    spans = [(r['span'], r['form'], r['height'], r.get('notes', '')) for r in sketch['frame']['rim']
             if r['side'] == 'east']
    table = []
    for (a, b), form, h, notes in spans:
        sl = slice(int(a), int(min(b, BORDER + 1)))
        f = np.array(rows['file_x109'][sl])
        p = np.array(rows['d6_border_x109'][sl])
        table.append({'span': [a, b], 'form': form, 'height': h, 'notes': notes,
                      'file_mean': int(f.mean()), 'd6_border_mean': int(p.mean()),
                      'mean_abs_diff': int(np.abs(f - p).mean()), 'max_abs_diff': int(np.abs(f - p).max())})
    diff = np.abs(np.array(rows['file_x109']) - np.array(rows['d6_border_x109']))
    pas = {'file_y62_66': rows['file_x109'][62:67], 'd6_y62_66': rows['d6_border_x109'][62:67],
           'corner_y106_109': {'file': rows['file_x109'][106:110], 'd6': rows['d6_border_x109'][106:110],
                               'd1_x109_y19': int(d1_heights()[19, BORDER])},
           'cells_differing_y0_105': int((diff[:106] > 0).sum())}
    return {'rows': rows, 'spans': table, 'pass': pas}


def extra_svg(scale, sketch):
    """The signature camera, Alamar's footprint and the ruin's stair, the pods, Necropolis's walls, the griffin's
    flight line."""
    s = scale
    parts = []
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
    # Castle Alamar's footprint (L3 lays it out): curtain, four towers, keep, gatehouse; the pylons
    parts.append(f'<rect x="{46 * s}" y="{41 * s}" width="{10 * s}" height="{10 * s}" fill="#2c3e42" '
                 'fill-opacity="0.9" stroke="#000" stroke-width="1.2"/>')
    parts.append(f'<rect x="{49.5 * s}" y="{43.5 * s}" width="{3 * s}" height="{3 * s}" fill="#1c2c30" stroke="#000"/>')
    for tx, ty in [(46, 41), (56, 41), (46, 51), (56, 51)]:
        parts.append(f'<rect x="{(tx - 1) * s}" y="{(ty - 1) * s}" width="{2 * s}" height="{2 * s}" fill="#24363a" '
                     'stroke="#000"/>')
    for px_, py_ in [(48.5, 57), (53.5, 57), (48.5, 60), (53.5, 60)]:
        parts.append(f'<circle cx="{px_ * s}" cy="{py_ * s}" r="3.5" fill="#5fe0f0" stroke="#0b4a55"/>')
    parts.append(f'<line x1="{48.5 * s}" y1="{57 * s}" x2="{53.5 * s}" y2="{57 * s}" stroke="#5fe0f0" '
                 'stroke-width="2.5" stroke-opacity="0.8"/>')
    parts.append(f'<line x1="{48.5 * s}" y1="{60 * s}" x2="{53.5 * s}" y2="{60 * s}" stroke="#5fe0f0" '
                 'stroke-width="2.5" stroke-opacity="0.8"/>')
    # the pods: Corak's nose-up (a capsule seen from above, the hatch toward the shore), Sheltem's upright
    parts.append(f'<ellipse cx="{72.5 * s}" cy="{67.5 * s}" rx="{1.6 * s}" ry="{0.9 * s}" fill="#5a3a2c" '
                 f'stroke="#ffcf6a" stroke-width="1.4" transform="rotate(40 {72.5 * s} {67.5 * s})"/>')
    parts.append(f'<circle cx="{78.5 * s}" cy="{38.5 * s}" r="{1.1 * s}" fill="#4a585c" stroke="#ccd" '
                 'stroke-width="1.2"/>')
    parts.append(f'<circle cx="{78.5 * s}" cy="{38.5 * s}" r="{2.6 * s}" fill="none" stroke="#333" '
                 'stroke-width="1" stroke-dasharray="3 3"/>')
    # Necropolis's walls and gatehouse
    parts.append(f'<rect x="{82 * s}" y="{74 * s}" width="{18 * s}" height="{16 * s}" fill="none" stroke="#2a2420" '
                 'stroke-width="4"/>')
    parts.append(f'<rect x="{82 * s}" y="{74 * s}" width="{18 * s}" height="{16 * s}" fill="none" stroke="#d8d0c0" '
                 'stroke-width="1.4"/>')
    for tx, ty in [(82, 74), (100, 74), (82, 90), (100, 90), (90, 74), (93, 74)]:
        parts.append(f'<rect x="{(tx - 0.7) * s}" y="{(ty - 0.7) * s}" width="{1.4 * s}" height="{1.4 * s}" '
                     'fill="#3a3430" stroke="#d8d0c0" stroke-width="1"/>')
    # Ambrose's griffin flight (to DD-14 on D4, off the map east)
    parts.append(f'<path d="M{61.5 * s},{95.5 * s} Q{90 * s},{60 * s} {127 * s},{40 * s}" fill="none" '
                 'stroke="#f4e3b0" stroke-width="2" stroke-dasharray="3 5"/>')
    parts.append(f'<text x="{118 * s}" y="{37 * s}" font-size="12" font-style="italic" text-anchor="end" '
                 'fill="#f4e3b0" stroke="#000" stroke-width="2.5" paint-order="stroke">griffin to DD-14 (M25)</text>')
    return '\n'.join(parts)


CAPTIONS = [
    ('E1 Ancient field, gamma gazers: 34 (40-65)', (86, 27.6), 13, '#7a1010'),
    ('E2 Alamar robots: 18 (50-75)', (51, 39.8), 12.5, '#bff'),
    ('E3 lava dwellers: 14 placed', (64, 52.0), 12, '#7a3a00'),
    ('E4a griffins: 16 (38-48)', (38, 105.6), 12.5, '#5a2400'),
    ('E4b griffins: 16 (38-48)', (90, 105.6), 12.5, '#5a2400'),
    ("E6 archers' camp: 12 placed", (34, 81.6), 11.5, '#5a1a80'),
    ("CORAK'S LAVA LAKE (1,450)", (71, 61.2), 12, '#3a0a00'),
    ('lava moat (1,550)', (64, 33.5), 12, '#ffe0a0'),
    ('THE VOLCANIC WASTE', (32, 44.5), 14, '#eee'),
    ('THE ANCIENT FIELD', (90, 48.5), 14, '#eef'),
    ('THE CINDER PLAINS', (42, 72), 14, '#eee'),
    ('NECROPOLIS', (91, 92.6), 15, '#222'),
    ('GRIFFIN PASS (2,450)', (64, 90.4), 13, '#222'),
    ("the Forbidden Zone's southern border", (42, 108.4), 12, '#eee'),
    ('the world rim: a cliff above the stars', (64, 14), 15, '#ccd'),
    ('rim', (12, 70), 15, '#ccd'),
    ('to D1 (south edge, x 64)', (64, 125), 12, '#fff'),
    ('to D5 (east edge, y 64)', (118, 61.4), 12, '#fff'),
    ('ash falls (40 % of days)', (34, 19.6), 12, '#e9c46a'),
]


def main():
    plan, sketch, project = pr.load('d6')
    OUT.mkdir(exist_ok=True)
    height, lava, rim = build_land(sketch)
    img = colour_land(sketch, height, lava, rim)
    img.save(OUT / 'colour.png')
    labels = {'kinds': KINDS, 'names': NAMES, 'offsets': OFFSETS,
              'arrows': {'entrance:south_road': True, 'entrance:east_pass': True}, 'encounters': ENCOUNTERS,
              'captions': CAPTIONS}
    pr.HERE = HERE            # svg_plan reads <HERE>/<key>/colour.png: point it at phase5
    svg = pr.svg_plan('d6', plan, sketch, project, labels, extra_svg(8, sketch))
    (OUT / 'plan_d6.svg').write_text(svg)
    if '--no-blockout' not in sys.argv:
        models = MODELS + house_models(plan, sketch) + metal_models(sketch, height, np.random.default_rng(21))
        pitch = {'view:arrival': -6.0, 'view:signature': 1.5}
        fovs = {'view:arrival': 76.0, 'view:signature': 60.0}
        for view in sketch['views']:
            name = view['id'].split(':')[1]
            d2r.blockout(height, img, view, models, OUT / f'blockout_{name}.png', fov=fovs[view['id']],
                         annotations=ANNOTATIONS.get(view['id']), pitch=pitch.get(view['id'], -3.0))
    result = measure(plan, sketch, project, height, lava, rim)
    (OUT / 'measure.json').write_text(json.dumps(result, indent=1))
    e1 = edge_d1(sketch, height)
    (OUT / 'edge_d1.json').write_text(json.dumps(e1, indent=1))
    e5 = edge_d5(sketch, height)
    (OUT / 'edge_d5.json').write_text(json.dumps(e5, indent=1))
    show = {k: v for k, v in result.items() if k != 'poi_groups'}
    print(json.dumps(show, indent=1))
    for g in result['poi_groups']:
        print('  ', ', '.join(g))
    for s in e1['spans']:
        print('edge D1', s['span'], s['form'], s['d1_border_mean'], s['d6_border_mean'], s['mean_abs_diff'])
    print('road', e1['road'])
    for s in e5['spans']:
        print('edge D5', s['span'], s['form'], s['file_mean'], s['d6_border_mean'], s['mean_abs_diff'])
    print('pass', e5['pass'])


if __name__ == '__main__':
    main()
