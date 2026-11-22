"""X3 MU-3 helpers: the land the sketch implies (for the drawings only) and the figures against MAPS (lane A5).

The studio build makes its own land from sketch.yml; this raster only draws the plan, the blockouts and measures the
plan's figures (areas, quiet land, first fights, roads, heights, POIs, the town's footprint).
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_l1 as G  # noqa: E402

RES = 6          # raster pixels per cell
N = 128
UNIT = 512
PLAY = (19, 19, 109, 109)
BAND_BASE = {'band:rim_sea': 0, 'band:water': 860, 'band:low': 960, 'band:mid': 1220, 'band:high': 1550,
             'band:peaks': 2300}
FLAT = {'town:nightshadow': 1000, 'town:ebenezer_camp': 1020, 'town:newcastle': 1750, 'zone:tower_islet': 1050,
        'zone:tomb': 1180}
DUMMY = {'hostiles': 0, 'areas': 0, 'markers': 0, 'chests': 0, 'pois': 0, 'kill_xp_member': 0, 'water_share': 0,
         'summary': '', 'ns_cells': 0}


def poly_mask(points, scale=RES, size=N):
    img = Image.new('L', (size * scale, size * scale), 0)
    ImageDraw.Draw(img).polygon([(x * scale, y * scale) for x, y in points], fill=255)
    return np.asarray(img) > 127


def line_mask(points, width_cells, scale=RES, size=N):
    img = Image.new('L', (size * scale, size * scale), 0)
    d = ImageDraw.Draw(img)
    pts = [(x * scale, y * scale) for x, y in points]
    w = max(1, int(round(width_cells * scale)))
    d.line(pts, fill=255, width=w, joint='curve')
    for p in pts:
        d.ellipse((p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2), fill=255)
    return np.asarray(img) > 127


def data():
    return G.plan(DUMMY), G.sketch(DUMMY)


def grids():
    size = N * RES
    yy, xx = np.mgrid[0:size, 0:size].astype(float) / RES
    return xx, yy


def build_land(sketch):
    """Height per raster pixel and the water, rim and causeway masks."""
    size = N * RES
    xx, yy = grids()
    height = np.full((size, size), 1000.0)
    for band in sketch['heights']['bands']:
        if band['band'] in ('band:rim_sea', 'band:water'):
            continue
        height[poly_mask(band['polygon'])] = BAND_BASE[band['band']]
    height[poly_mask(G.LAGOON)] = 900
    height = ndimage.gaussian_filter(height, 3 * RES)
    # the frame: ridges and levels beyond the playable square
    rng = np.random.default_rng(7)
    for rim in sketch['frame']['rim']:
        side = rim['side']
        if side == 'south':
            continue
        lo, hi = (rim['height'], rim['height']) if rim['form'] == 'level' else rim['height']
        span = rim.get('span', [0, 128])
        along = xx if side in ('north', 'south') else yy
        depth = {'north': 19 - yy, 'west': 19 - xx, 'east': xx - 109, 'south': yy - 104}[side]
        inside = (along >= span[0]) & (along < span[1])
        w = np.clip(depth / 10.0, 0, 1) if rim['form'] == 'ridge' else np.clip(depth / 6.0 + 0.15, 0, 1)
        if rim['form'] == 'ridge':
            wave = ndimage.gaussian_filter1d(rng.normal(size=N * RES), 2.5 * RES)
            wave = (wave - wave.min()) / (np.ptp(wave) + 1e-6)
            wave2d = wave[np.clip((along * RES).astype(int), 0, N * RES - 1)]
            target = lo + (hi - lo) * wave2d
        else:
            target = np.full_like(height, lo)
        m = inside & (depth > -4)
        height[m] = height[m] * (1 - w[m]) + target[m] * w[m]
    # key heights: soft cones
    for point in sketch['heights'].get('points', []):
        px, py = point['at']
        r = 6.5 if point['h'] > 2400 else 4.0
        d = np.hypot(xx - px, yy - py)
        t = np.clip(1 - d / r, 0, 1)
        w = t * t * (3 - 2 * t)
        height = height * (1 - w) + point['h'] * w
    for ridge in sketch['heights'].get('ridges', []):
        m = line_mask(ridge['line'], ridge.get('width', 2))
        dist = ndimage.distance_transform_edt(~m) / RES
        slope = ridge.get('slope', 3) + 2.5
        w = np.clip(1 - dist / slope, 0, 1)
        height = np.maximum(height, height * (1 - w) + ridge['height'] * w)
    # swells and roughness, calm in towns and on water
    noise = ndimage.gaussian_filter(rng.normal(size=(size, size)), 2.5 * RES)
    noise /= np.abs(noise).max() + 1e-6
    rough = ndimage.gaussian_filter(rng.normal(size=(size, size)), 0.6 * RES)
    rough /= np.abs(rough).max() + 1e-6
    calm = np.zeros((size, size), bool)
    for d in sketch['districts']:
        if d['space'] in FLAT or d['space'] == 'zone:nightshadow_square':
            calm |= poly_mask(d['polygon'])
    calm |= poly_mask(G.LAGOON)
    calm = ndimage.binary_dilation(calm, iterations=2 * RES)
    steep = np.clip((height - 1400) / 1200, 0, 1)
    height += np.where(calm, 0, noise * 180 + rough * (40 + 220 * steep))
    for d in sketch['districts']:
        if d['space'] in FLAT:
            m = poly_mask(d['polygon'])
            soft = ndimage.gaussian_filter(m.astype(float), 1.2 * RES)
            height = height * (1 - soft) + FLAT[d['space']] * soft
    # water
    water = np.zeros((size, size), bool)
    lagoon = poly_mask(G.LAGOON)
    shore = ndimage.binary_dilation(lagoon, iterations=2 * RES) & ~lagoon
    height[shore] = np.minimum(height[shore], np.maximum(height[shore] - 80, 885))
    height[lagoon] = 860
    water |= lagoon
    for poly, level, _ in G.PONDS.values():
        m = poly_mask(poly)
        height[m] = level - 10
        water |= m
    river = line_mask(G.RIVER, 2.5)
    bank = ndimage.binary_dilation(river, iterations=2 * RES) & ~river
    height[bank] = np.minimum(height[bank], np.maximum(height[bank] - 120, 880))
    height[river] = 850
    water |= river
    causeway = line_mask([[64, 57], [64, 62], [64, 66.5]], 2.0) & ~lagoon
    height[causeway] = np.clip(height[causeway], 900, 940)
    rim = yy >= 104
    height[rim] = 0
    water &= ~rim
    return height, water, rim


def playable_mask():
    xx, yy = grids()
    return (xx >= PLAY[0]) & (xx < PLAY[2]) & (yy >= PLAY[1]) & (yy < PLAY[3])


def area_masks():
    out = {}
    for pid, slot, count, key, poly, _ in G.AREAS:
        out.setdefault(key, np.zeros((N * RES, N * RES), bool))
        out[key] |= poly_mask(poly)
    return out


def road_mask(inside_only=True):
    m = np.zeros((N * RES, N * RES), bool)
    for link, line, width, _ in G.ROADS:
        m |= line_mask(line, 1.0 if width == 'road' else 0.5)
    return m


def markers(land):
    """Indicative marker spots, per area key (E1-E5): the fixed first spots (G.FIRST_SPOTS), then an even spread
    (farthest-point start, five Lloyd steps) over the area's land, off roads, water and the doors' steps. The studio
    places the real markers; these only draw the plan and measure first fights and empty land."""
    roads = ndimage.binary_dilation(road_mask(), iterations=RES)
    avoid = [(34, 82.5, 3.0), (64.5, 67.5, 3.0), (27.5, 34, 3.0)]
    step = RES // 2
    keys = []
    for pid, slot, count, key, poly, _ in G.AREAS:
        if key not in keys:
            keys.append(key)
    placed = []
    for key in keys:
        entries = [a for a in G.AREAS if a[3] == key]
        poly = entries[0][4]
        m = ndimage.binary_erosion(poly_mask(poly), iterations=int(1.0 * RES)) & land & ~roads
        for ax, ay, r in avoid:
            m &= ~poly_mask([[ax - r, ay - r], [ax + r, ay - r], [ax + r, ay + r], [ax - r, ay + r]])
        ys, xs = np.nonzero(m[::step, ::step])
        cand = np.stack([xs * step / RES, ys * step / RES], axis=1)
        fixed = [(tuple(spot), a[1]) for a in entries for spot in G.FIRST_SPOTS.get(a[0], [])]
        slots = [s for _, s in fixed]
        for a in entries:
            slots += [a[1]] * (a[2] - sum(1 for _, s in fixed if s == a[1] and _ in
                                          [tuple(x) for x in G.FIRST_SPOTS.get(a[0], [])]))
        total = sum(a[2] for a in entries)
        pts = [np.array(f[0], float) for f in fixed]
        while len(pts) < total:
            pp = np.array(pts) if pts else np.zeros((0, 2))
            d = (np.min(np.hypot(cand[:, None, 0] - pp[None, :, 0], cand[:, None, 1] - pp[None, :, 1]), axis=1)
                 if len(pp) else np.ones(len(cand)))
            pts.append(cand[int(np.argmax(d))].copy())
        pts = np.array(pts)
        nfix = len(fixed)
        for _ in range(5):
            owner = np.argmin(np.hypot(cand[:, None, 0] - pts[None, :, 0], cand[:, None, 1] - pts[None, :, 1]), axis=1)
            for i in range(nfix, total):
                mine = cand[owner == i]
                if len(mine):
                    c = mine.mean(axis=0)
                    pts[i] = cand[int(np.argmin(np.hypot(cand[:, 0] - c[0], cand[:, 1] - c[1])))]
        for (x, y), slot in zip(pts, slots):
            placed.append((float(x), float(y), slot, key))
    return placed


def dist_to_mask(mask):
    return ndimage.distance_transform_edt(~mask) / RES * UNIT


def measure(plan, sketch, height, water, rim):
    xx, yy = grids()
    play = playable_mask()
    land = play & ~water & ~rim
    land_cells = land.sum() / RES ** 2
    areas = area_masks()
    any_enc = np.zeros_like(land)
    for m in areas.values():
        any_enc |= m
    quiet_cells = (land & ~any_enc).sum() / RES ** 2 / land_cells
    # blocks of 4,096 (8 x 8 cells)
    B = 8 * RES
    land_blocks, quiet_blocks, area_blocks = 0, 0, {k: 0 for k in areas}
    for by in range(16):
        for bx in range(16):
            sl = (slice(by * B, (by + 1) * B), slice(bx * B, (bx + 1) * B))
            lb = land[sl]
            if lb.sum() < 0.5 * B * B:
                continue
            land_blocks += 1
            hit = False
            for k, m in areas.items():
                if (m[sl] & lb).sum() >= 0.25 * lb.sum():
                    area_blocks[k] += 1
                    hit = True
            if not hit:
                quiet_blocks += 1
    marks = markers(land)
    hostiles = sum(G.SLOT_MEAN[s] for _, _, s, _ in marks) + sum(a[2] for a in G.ACTORS)
    # kill XP: slots at the A/B/C mix, placed rows at their own XP
    kill = 0.0
    for _, _, s, _ in marks:
        kill += G.SLOT_MEAN[s] * sum(w * x for w, x in zip(G.TIER_MIX, G.XP[s]))
    for m, at, c, *_ in G.ACTORS:
        kill += c * G.XP[m]
    hostile_spots = [(x, y) for x, y, _, _ in marks] + [tuple(a[1]) for a in G.ACTORS]

    def nearest_fight(p):
        return min(math.hypot(p[0] - x, p[1] - y) for x, y in hostile_spots) * UNIT

    def nearest_area(p):
        d = dist_to_mask(any_enc)
        return float(d[int(p[1] * RES), int(p[0] * RES)])

    pts = {p[0]: p[1] for p in G.POINTS}
    first = {}
    for name, pid in [('east (X2)', 'entrance:east_road'), ('west (X5)', 'entrance:west_road'),
                      ('north (X4)', 'entrance:north_road'), ('X8 landing', 'entrance:x8_landing')]:
        first[name] = (round(nearest_fight(pts[pid])), round(nearest_area(pts[pid])))
    doors = {'Nightshadow doors': [], "Ebenezer's camp doors": [], 'Newcastle gate': [pts['entrance:newcastle_gate']]}
    for space, label in [('town:nightshadow', 'Nightshadow doors'), ('town:ebenezer_camp', "Ebenezer's camp doors")]:
        for b, idx, at, facing, *_ in G.PLOTS[space]:
            doors[label].append(door_point(b, idx, at, facing))
    town_fight = {k: round(min(nearest_fight(p) for p in v)) for k, v in doors.items()}
    roads = road_mask() & land
    road_share = roads.sum() / land.sum()
    hl = height[land & ~ndimage.binary_dilation(water, iterations=RES)]
    water_share = (water & play).sum() / (play & ~rim).sum()
    # points of interest. Budget (MAPS: named items + generic devices): every poi point but the mirrors, the
    # sundials as one set, plus the dungeon doors. Census (MAP_CRAFT_CALIBRATION: bound interactions collapsed within
    # 400 units): service doors, dungeon doors, chests, wells, springs, shrines, the obelisk, sundials, camps and
    # devices; not signposts, signs, mirrors or residences.
    budget = []
    for pid, at, facing, kind, label in G.POINTS:
        if pid in ('poi:nightshadow_mirror', 'poi:newcastle_mirror', 'poi:draco_coffin'):
            continue
        if pid == 'poi:sundials' and any(b[0] == pid for b in budget):
            continue
        if pid.startswith('poi:') or pid.startswith('entrance:xd'):
            budget.append((pid, at))
    census = []
    for pid, at, facing, kind, label in G.POINTS:
        if pid in ('poi:count_sign', 'poi:rhyme_board', 'poi:draco_coffin', 'poi:nightshadow_mirror',
                   'poi:newcastle_mirror', 'poi:signposts'):
            continue
        if pid.startswith('poi:') or pid.startswith('entrance:xd'):
            census.append((pid, at))
    for space in ('town:nightshadow', 'town:ebenezer_camp'):
        for b, idx, at, facing, *_ in G.PLOTS[space]:
            if b != 'building:nightshadow_houses':
                census.append((b, door_point(b, idx, at, facing)))
    merged = []
    for pid, at in census:
        if any(math.hypot(at[0] - m[1][0], at[1] - m[1][1]) * UNIT < 400 for m in merged):
            continue
        merged.append((pid, at))
    ns_poly = poly_mask(G.TOWN_NIGHTSHADOW)
    in_town = [m for m in budget if ns_poly[int(m[1][1] * RES), int(m[1][0] * RES)]]
    nn = []
    for i, (pid, a) in enumerate(merged):
        nn.append(min(math.hypot(a[0] - b[0], a[1] - b[1]) for j, (_, b) in enumerate(merged) if j != i) * UNIT)
    # land far from any place or fight
    place = np.zeros_like(land)
    for _, at in merged:
        place[int(at[1] * RES), int(at[0] * RES)] = True
    for x, y in hostile_spots:
        place[int(y * RES), int(x * RES)] = True
    for pid, at, *_ in G.POINTS:      # the edge arrivals count as places (signposted road ends)
        if pid in ('entrance:east_road', 'entrance:west_road', 'entrance:north_road'):
            place[int(at[1] * RES), int(at[0] * RES)] = True
    far = dist_to_mask(place)
    far_land = far[land]
    fy, fx = np.unravel_index(np.argmax(np.where(land, far, 0)), far.shape)
    chests = sum(1 for p in G.POINTS if p[3] == 'chest')
    # Nightshadow's footprint
    rects = []
    for b, idx, at, facing, *_ in G.PLOTS['town:nightshadow']:
        fp = footprint(b, idx)
        wx, wy = (fp[0], fp[1]) if facing in 'ns' else (fp[1], fp[0])
        rects.append((at[0], at[1], wx, wy))
    built = np.zeros_like(land)
    for x, y, wx, wy in rects:
        built[int(y * RES):int((y + wy) * RES), int(x * RES):int((x + wx) * RES)] = True
    foot = ndimage.binary_dilation(built, iterations=int(1.5 * RES))
    foot_cells = foot.sum() / RES ** 2
    xs = [r[0] for r in rects] + [r[0] + r[2] for r in rects]
    ys = [r[1] for r in rects] + [r[1] + r[3] for r in rects]
    mids = [(x + wx / 2, y + wy / 2) for x, y, wx, wy in rects]
    mid_nn = sorted(min(math.hypot(a[0] - b[0], a[1] - b[1]) for j, b in enumerate(mids) if j != i) * UNIT
                    for i, a in enumerate(mids))
    services = [door_point(b, idx, at, f) for b, idx, at, f, *_ in G.PLOTS['town:nightshadow']
                if b != 'building:nightshadow_houses']
    pairs = sorted(math.hypot(a[0] - b[0], a[1] - b[1]) * UNIT for i, a in enumerate(services)
                   for b in services[i + 1:])
    fig = {
        'land_cells': int(land_cells),
        'hostiles': int(round(hostiles)),
        'markers': len(marks),
        'placed': sum(a[2] for a in G.ACTORS),
        'areas': len(areas),
        'area_blocks': area_blocks,
        'land_blocks': land_blocks,
        'quiet_blocks': quiet_blocks,
        'quiet_block_share': round(quiet_blocks / land_blocks, 2),
        'quiet_cell_share': round(float(quiet_cells), 2),
        'first_fight': first,
        'town_fight': town_fight,
        'road_share': round(float(road_share) * 100, 1),
        'height_min': int(hl.min()),
        'height_max': int(hl.max()),
        'water_share': round(float(water_share), 3),
        'pois': len(budget),
        'pois_in_town': len(in_town),
        'census_pois': len(merged),
        'poi_nn_median': int(np.median(nn)),
        'poi_nn_p90': int(np.percentile(nn, 90)),
        'far_max': int(far_land.max()),
        'far_at': (round(fx / RES, 1), round(fy / RES, 1)),
        'far_share_3000': round(float((far_land > 3000).mean()), 2),
        'chests': chests,
        'kill_xp_member': round(kill / 4 / 1000, 1),
        'ns_buildings': len(rects),
        'ns_cells': int(foot_cells),
        'ns_per100': round(len(rects) / foot_cells * 100, 1),
        'ns_built_share': round(float(built.sum() / foot.sum()), 2),
        'ns_extent': (int((max(xs) - min(xs)) * UNIT), int((max(ys) - min(ys)) * UNIT)),
        'ns_mid_nn_median': int(np.median(mid_nn)),
        'ns_service_pairs_median': int(np.median(pairs)),
    }
    fig['summary'] = (
        f"hostiles at load {fig['hostiles']} ({fig['markers']} markers at 2-3 or 2-4, {fig['placed']} placed); "
        f"{fig['areas']} encounter areas over {sum(area_blocks.values())} blocks of 4,096 "
        f"({', '.join(f'{k} {v}' for k, v in area_blocks.items())}); quiet land {fig['quiet_cell_share']:.0%} of "
        f"cells, {fig['quiet_block_share']:.0%} of blocks; first fight east {first['east (X2)'][0]:,}, west "
        f"{first['west (X5)'][0]:,}, north {first['north (X4)'][0]:,}; roads {fig['road_share']} % of land; land "
        f"{fig['height_min']:,}-{fig['height_max']:,} (range {fig['height_max'] - fig['height_min']:,}); "
        f"{fig['pois']} POIs by the MAPS budget ({fig['pois_in_town']} in Nightshadow); census {fig['census_pois']} "
        f"with the service doors, nearest-neighbour median {fig['poi_nn_median']:,}; land farthest from a place or fight {fig['far_max']:,}; {fig['chests']} chests; "
        f"Nightshadow {fig['ns_buildings']} buildings on {fig['ns_cells']} cells of footprint; kill XP about "
        f"{fig['kill_xp_member']}k per member (A/B/C 50/35/15).")
    return fig, marks


def footprint(b, idx):
    if b == 'building:nightshadow_houses':
        return G.NS_HOUSES[idx - 1][2]
    for space, items in G.BUILDINGS.items():
        for bid, _, fp in items:
            if bid == b:
                return fp
    raise KeyError(b)


def door_point(b, idx, at, facing):
    fp = footprint(b, idx)
    wx, wy = (fp[0], fp[1]) if facing in 'ns' else (fp[1], fp[0])
    x, y = at
    return {'n': (x + wx / 2, y), 's': (x + wx / 2, y + wy), 'e': (x + wx, y + wy / 2),
            'w': (x, y + wy / 2)}[facing]


def figures_for_brief():
    plan, sketch = data()
    height, water, rim = build_land(sketch)
    fig, _ = measure(plan, sketch, height, water, rim)
    return fig
