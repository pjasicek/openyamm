"""Build the Crown (hes_out4.odm, map 9130) from its design: terrain, ground materials, buildings, decorations, chests,
the hostile groups and spawn points, the people, the events, then the ODM through the editor's writer, into
runtime/worlds/hesper for the shared Hesper stage.

    python3 level_generation/projects/hesper_out4/build_out4.py
    flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py

The design is the authority (design/kreegan_world/zone4/THE_CROWN.md, BUILD-READY): the terrain functions of
crown_terrain.py and every place, road, footprint, cover piece, decoration group, chest, monster group, pylon, relay,
hatch and the plaza lift of crown_detail.json (make_crown_detail.py). Nothing is typed here that the design places.
Starport Reach's kit is reused (level_generation/projects/hesper_out1: bmodels.py, houses.py, spawns.Ground). The
editor needs the stage as its asset root (the Hesper textures and decorations live only there): stage once before
the first build. Nothing is written to assets_dev.
"""
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import yaml
from PIL import Image
from scipy import ndimage

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
DESIGN = ROOT / 'design/kreegan_world/zone4'
OUT1 = ROOT / 'level_generation/projects/hesper_out1'
STAGE_DATA = ROOT / 'level_generation/projects/hesper_stage'
STAGE = ROOT / 'output/hesper_stage/assets_editor_dev'
SOURCE = PROJECT / 'source'
TREE = PROJECT / 'runtime/worlds/hesper'
MAP = 'hes_out4.odm'
sys.path.insert(0, str(DESIGN))
sys.path.insert(0, str(OUT1))
sys.path.insert(0, str(PROJECT))
import crown_terrain as ct  # noqa: E402
from bmodels import Model, normal, write_obj  # noqa: E402
import bmodels_out4 as kit  # noqa: E402
from spawns import Ground  # noqa: E402

DETAIL = json.loads((DESIGN / 'crown_detail.json').read_text())
GRID = 128
STEP = 512
TEXELS = 16
BOUND = ct.HALF                                  # the playable square: +-23 040
EDGE_Z = 1200.0                                  # the crossings' contract height (WORK_PACKAGES/README.md, Map edges)
FLOOR_Z = 800.0 + 1500.0 * ct.FLOOR_H            # 1 100
rng = np.random.default_rng(20261023)


def game_height(h):
    """The design's relative height in world units: 800 + 1 500 h (the rim's crest peaks near 5 000)."""
    return np.clip(800.0 + 1500.0 * h, 0.0, 8000.0)


# What the outer ring's ridges and terraces keep clear of (crown_terrain.clear_distance): every road and track of the
# design (and the Blooding Ring's track), every footprint, the hatches, the pit, the blast wall.
CLEAR_LINES = [line for kind in ('paving', 'track') for line in DETAIL['roads'][kind]]
CLEAR_LINES.append([(ct.RING_HALF + 320.0, ct.RING_PIT[1]), (ct.RING_PIT[0] - 2400.0, ct.RING_PIT[1])])
CLEAR_DISCS = ct.footprint_discs(DETAIL['footprints'], DETAIL['service_exits'],
                                 [(p['x'], p['y']) for p in DETAIL['places'] if p['kind'] not in ('m_raid',)]
                                 + list(DETAIL['pylons'].values()) + list(DETAIL['relays'].values()))
CLEAR_DISCS.append((tuple(np.mean(DETAIL['test_wall'], axis=0)), 900.0))
CUT_LINES = ct.cut_lines(DETAIL['roads']) + [CLEAR_LINES[-1]]
CUT_DISCS = ct.cut_discs(DETAIL['service_exits'])


def terrain(x, y):
    x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    return ct.build_terrain(*ct.world_px(x, y), clear=ct.clear_distance(x, y, CLEAR_LINES, CLEAR_DISCS),
                            cut=ct.clear_distance(x, y, CUT_LINES, CUT_DISCS))


# --- Terrain heights ------------------------------------------------------------------------------------------------
gx = np.arange(GRID)
sample_x, sample_y = np.meshgrid((gx - 64) * STEP, (64 - gx) * STEP)        # [gy, gx]
heights = np.zeros((GRID, GRID))
fixed = np.zeros((GRID, GRID), dtype=bool)       # vertices a road, a pad or a crossing set (the pit pass keeps off)
for dx in (-170, 0, 170):
    for dy in (-170, 0, 170):
        h, _ = terrain(sample_x + dx, sample_y + dy)
        heights += game_height(h) / 9.0


def height_at(x, y):
    """The native triangle height at a world point (the cell splits along fracX + fracY <= 1)."""
    fx = (x + 32768.0) / STEP
    fy = (32768.0 - y) / STEP
    ix, iy = int(np.clip(math.floor(fx), 0, GRID - 2)), int(np.clip(math.floor(fy), 0, GRID - 2))
    tx, ty = fx - ix, fy - iy
    h00, h10 = heights[iy, ix], heights[iy, ix + 1]
    h01, h11 = heights[iy + 1, ix], heights[iy + 1, ix + 1]
    if tx + ty <= 1:
        return float(h00 + (h10 - h00) * tx + (h01 - h00) * ty)
    return float(h11 + (h01 - h11) * (1 - tx) + (h10 - h11) * (1 - ty))


def resample(points, spacing=256.0):
    out = [tuple(points[0])]
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        steps = max(1, int(math.hypot(bx - ax, by - ay) / spacing))
        out += [(ax + (bx - ax) * k / steps, ay + (by - ay) * k / steps) for k in range(1, steps + 1)]
    return out


def grade(points, width, falloff, max_slope, smooth=9):
    """Cut a road into the heights: along-path heights smoothed and slope-limited, blended into a corridor."""
    path = resample(points)
    profile = np.array([height_at(x, y) for x, y in path])
    kernel = np.ones(smooth) / smooth
    profile = np.convolve(np.pad(profile, smooth // 2, mode='edge'), kernel, mode='valid')
    step = 256.0 * max_slope
    for _ in range(2):
        for i in range(1, len(profile)):
            profile[i] = np.clip(profile[i], profile[i - 1] - step, profile[i - 1] + step)
        for i in range(len(profile) - 2, -1, -1):
            profile[i] = np.clip(profile[i], profile[i + 1] - step, profile[i + 1] + step)
    px = np.array(path)
    for iy in range(GRID):
        for ix in range(GRID):
            x, y = sample_x[iy, ix], sample_y[iy, ix]
            if x < px[:, 0].min() - width - falloff or x > px[:, 0].max() + width + falloff or \
                    y < px[:, 1].min() - width - falloff or y > px[:, 1].max() + width + falloff:
                continue
            d = np.hypot(px[:, 0] - x, px[:, 1] - y)
            k = int(np.argmin(d))
            if d[k] > width / 2 + falloff:
                continue
            weight = 1.0 if d[k] <= width / 2 else 1.0 - (d[k] - width / 2) / falloff
            heights[iy, ix] = heights[iy, ix] * (1 - weight) + profile[k] * weight
            fixed[iy, ix] = True


def flatten(centre, half_x, half_y, yaw=0.0, falloff=600.0, level=None):
    """Level a rectangular pad (the median height under it unless given), blended over falloff."""
    cx, cy = centre
    c, s = math.cos(-yaw), math.sin(-yaw)
    lx = (sample_x - cx) * c - (sample_y - cy) * s
    ly = (sample_x - cx) * s + (sample_y - cy) * c
    inside = (np.abs(lx) <= half_x) & (np.abs(ly) <= half_y)
    if level is None:
        level = float(np.median(heights[inside])) if inside.any() else height_at(cx, cy)
    distance = np.hypot(np.maximum(np.abs(lx) - half_x, 0), np.maximum(np.abs(ly) - half_y, 0))
    weight = np.clip(1.0 - distance / falloff, 0.0, 1.0)
    heights[:] = heights * (1 - weight) + level * weight
    fixed[weight > 0] = True
    return level


def flatten_disc(centre, radius, falloff=600.0, level=None):
    d = np.hypot(sample_x - centre[0], sample_y - centre[1])
    if level is None:
        inside = d <= radius
        level = float(np.median(heights[inside])) if inside.any() else height_at(*centre)
    weight = np.clip(1.0 - np.maximum(d - radius, 0) / falloff, 0.0, 1.0)
    heights[:] = heights * (1 - weight) + level * weight
    fixed[weight > 0] = True
    return level


# Roads (crown_detail.json): resin paving 640 wide, the scree tracks with two tread lines. The two edge roads already
# run on 900 past the edge in the design.
paving = [[tuple(p) for p in line] for line in DETAIL['roads']['paving']]
tracks = [[tuple(p) for p in line] for line in DETAIL['roads']['track']]
# The Blooding Ring (a follow-up, THE_CROWN.md section 7 and HARROWERS.md): the design's centre (17 400, 9 400) moved
# 300 east so the pad (radius 1 500) cuts into the rim's foot (built: the rise starts near x = 18 900 here) and the
# cliff closes its east side. The floor 2 400 across inside the wall, the gate west, a scree track to the ring road.
RING = ct.RING_PIT                   # (17 700, 9 400): the design's relief keeps its pad and passage level
RING_R = 1200.0                      # the floor's radius to the wall's inner face
RING_WALL = 150.0
RING_PAD = 1500.0
RING_GATE = 180.0                    # degrees: the gate faces the ring road
RING_CHEEK, RING_BLIND, RING_BLIND_HALF = 250.0, 800.0, 900.0     # the gate's cheek walls and its blind wall
RING_BLIND_FACE = RING_R + RING_WALL + RING_BLIND + RING_WALL     # the blind wall's outer face from the centre
tracks.append([(ct.RING_HALF + 320.0, RING[1]), (RING[0] - RING_BLIND_FACE - 60.0, RING[1])])
for line in paving:
    grade(line, 700, 500, 0.15)
for line in tracks:
    grade(line, 480, 400, 0.3)

# Pads: the fortress with its bastions, the plaza, the node blockhouses, every footprint of the districts.
flatten((0.0, 0.0), ct.FORTRESS_HALF + 900, ct.FORTRESS_HALF + 900, level=FLOOR_Z, falloff=700)
PLAZA, PLAZA_R = tuple(ct.PLAZA), ct.PLAZA_R
flatten_disc(PLAZA, PLAZA_R + 250, falloff=700, level=FLOOR_Z)
NODES = {name: (tuple(v['door']), tuple(v['outward'])) for name, v in DETAIL['nodes'].items()}
for door, (ox, oy) in NODES.values():
    flatten_disc((door[0] - ox * ct.NODE_BUNKER_BACK, door[1] - oy * ct.NODE_BUNKER_BACK), ct.NODE_BUNKER_R + 400,
                 falloff=600, level=FLOOR_Z)
FOOTPRINTS = [(kind, tuple(centre), size, angle) for kind, centre, size, angle in DETAIL['footprints']]
for kind, centre, size, angle in FOOTPRINTS:
    if kind in ('fortress', 'plaza', 'lift'):
        continue
    if isinstance(size, list):
        flatten(centre, size[0] / 2 + 200, size[1] / 2 + 200, math.radians(angle), falloff=500)
    else:
        flatten_disc(centre, size + 200, falloff=500)
COVER = [(kind, tuple(centre), length, angle) for kind, centre, length, angle in DETAIL['cover']]
for kind, centre, length, angle in COVER:
    if kind == 'wreck':
        flatten(centre, 600, 400, math.radians(angle), falloff=400)
for kind, centre, length, angle in COVER:          # the slabs stand level (the terraces' risers pass them by)
    if kind == 'slab':
        flatten(centre, length / 2 + 150, 250, math.radians(angle), falloff=400)
TEST_CANNON = tuple(DETAIL['test_cannon'])
TEST_WALL = [tuple(p) for p in DETAIL['test_wall']]
flatten(((TEST_WALL[0][0] + TEST_WALL[1][0]) / 2, (TEST_WALL[0][1] + TEST_WALL[1][1]) / 2),
        math.hypot(TEST_WALL[1][0] - TEST_WALL[0][0], TEST_WALL[1][1] - TEST_WALL[0][1]) / 2 + 200, 300,
        math.atan2(TEST_WALL[1][1] - TEST_WALL[0][1], TEST_WALL[1][0] - TEST_WALL[0][0]), falloff=400)
flatten_disc(RING, RING_PAD, falloff=500, level=FLOOR_Z)
# The pit's passage: the blind wall, the gate's cheeks and the track's end stand on the floor's level (kit.blooding_ring
# builds them at FLOOR_Z; the relief climbs round them).
flatten((RING[0] - (RING_BLIND_FACE + 300) / 2, RING[1]), (RING_BLIND_FACE + 300) / 2, RING_BLIND_HALF + 350,
        falloff=500, level=FLOOR_Z)
# The node causeways from each blockhouse out past its door's arrival (10 300) stay at the floor's level: D6, D7 and D16
# read their exits from out4_build.json.
for door, (ox, oy) in NODES.values():
    mid = (math.hypot(*door) - ct.NODE_BUNKER_BACK + 10800.0) / 2
    flatten((ox * mid, oy * mid), (10800.0 - math.hypot(*door) + ct.NODE_BUNKER_BACK) / 2, 1450,
            math.atan2(oy, ox), falloff=500, level=FLOOR_Z)

# The service hatches: each in a black-glass outcrop at the rim's foot, facing the ring (THE_CROWN.md section 13):
# the ground before it level, an outcrop rising 1 000 behind it.
SERVICE_EXITS = {name: tuple(p) for name, p in DETAIL['service_exits'].items()}
HATCH_FRONT = {'D6 West': 0.0, 'D16 North': 270.0, 'D7 East': 180.0}       # degrees, toward the ring
# Each hatch's ground at the level of its first build (the median then): D6, D7 and D16 read the hatch arrivals.
HATCH_LEVEL = {'D6 West': 1120.0, 'D16 North': 1056.0, 'D7 East': 1056.0}
hatch_levels = {}
for name, (hx, hy) in SERVICE_EXITS.items():
    fx, fy = math.cos(math.radians(HATCH_FRONT[name])), math.sin(math.radians(HATCH_FRONT[name]))
    level = flatten((hx + fx * 450, hy + fy * 450), 650, 700, math.radians(HATCH_FRONT[name]), falloff=500,
                    level=HATCH_LEVEL[name])
    along = (sample_x - hx) * -fx + (sample_y - hy) * -fy           # positive behind the hatch
    across = -(sample_x - hx) * -fy + (sample_y - hy) * -fx
    # The rock starts a terrain cell (512) behind the face: the ground's triangles would otherwise climb in front of it.
    outside = np.maximum.reduce([1050 - along, np.abs(across) - 800, along - 2200, np.zeros_like(along)])
    rock = np.clip(1.0 - outside / 500.0, 0.0, 1.0)
    heights[:] = np.maximum(heights, heights * (1 - rock) + (level + 1050) * rock)
    hatch_levels[name] = level

# The crossings: the contract's 1 200 flat for 1 500 inside the edge across the notch's 2 000 floor.
CROSSINGS = {'south': ((2880.0, -BOUND), (0.0, 1.0)), 'west': ((-BOUND, 8640.0), (1.0, 0.0))}
for (ex, ey), (ux, uy) in CROSSINGS.values():
    along = (sample_x - ex) * ux + (sample_y - ey) * uy
    across = np.abs((sample_x - ex) * -uy + (sample_y - ey) * ux)
    heights[(along <= 1600) & (across <= 1000)] = EDGE_Z
    fixed[(along <= 1600) & (across <= 1000)] = True


def floor_pits(quantised):
    """Tiles of the cut-off pits of the floor (check_relief.py's rule): walkable tiles (four corners within 512, the
    monsters' rule) inside the playable square below 2 500, cut off from the Kreegan Road's arrival, with the open
    floor beside them higher (the party walks onto the slope between and slides in)."""
    corners = np.stack([quantised[:-1, :-1], quantised[:-1, 1:], quantised[1:, :-1], quantised[1:, 1:]])
    walk = (corners.max(0) - corners.min(0)) <= 512
    labels, count = ndimage.label(walk)
    main = labels[int((32768 + 21800) // STEP), int((2880 + 32768) // STEP)]
    centres = -32768.0 + (np.arange(GRID - 1) + 0.5) * STEP
    inside = (np.abs(centres)[None, :] < BOUND - 512) & (np.abs(centres)[:, None] < BOUND - 512)
    mean = corners.mean(0)
    pits = np.zeros(walk.shape, dtype=bool)
    for label in range(1, count + 1):
        cells = (labels == label) & inside
        if label == main or cells.sum() < 4 or mean[cells].mean() >= 2500:
            continue
        beside = ndimage.binary_dilation(cells, iterations=2) & (labels == main)
        if beside.any() and mean[beside].max() > mean[cells].mean() + 64:
            pits |= cells
    return pits


# Pockets the ridges, the spurs and the rim close round (a pit a party slides into and cannot leave) are smoothed open,
# off the roads, the pads and the crossings.
PIT_PASSES = 0
for _ in range(16):
    pits = floor_pits(np.round(heights / 32.0) * 32.0)
    if not pits.any():
        break
    PIT_PASSES += 1
    region = ndimage.binary_dilation(pits, iterations=2)
    vertices = np.zeros((GRID, GRID), dtype=bool)
    for oy in (0, 1):
        for ox in (0, 1):
            vertices[oy:GRID - 1 + oy, ox:GRID - 1 + ox] |= region
    vertices &= ~fixed
    heights[vertices] = ndimage.gaussian_filter(heights, 1.0, mode='nearest')[vertices]
assert not floor_pits(np.round(heights / 32.0) * 32.0).any(), 'pits left after the pit pass'

height_bytes = np.clip(np.round(heights / 32.0), 0, 255).astype(np.uint8)
heights = height_bytes.astype(np.float64) * 32.0          # the quantised heights everything else stands on
EDGE_BUILT = {}
for name, ((ex, ey), (ux, uy)) in CROSSINGS.items():
    rows = [height_at(ex + ux * d - uy * a, ey + uy * d + ux * a) for d in range(0, 1501, 100) for a in (-300, 0, 300)]
    assert max(abs(z - EDGE_Z) for z in rows) <= 32, (name, rows)
    EDGE_BUILT[name] = sorted(set(round(z) for z in rows))

# --- Materials: tiles (one per cell) and weights (16 texels per cell) ----------------------------------------------
# No plants grow on the Crown (K13); the tiles still name the ground for the engine's footstep and tile lookups, from
# Starport Reach's tile sets (volcanic 198, sand 594, rock 342, water 126).
LOOKUPS = [198, 594, 342, 126]
TILES = {'ash': 90, 'scree': 91, 'scorched': 103, 'plating': 1, 'paving': 1, 'creep': 102, 'glass': 175, 'rock': 162}
LAYERS = ['ash', 'scree', 'scorched', 'plating', 'paving', 'creep', 'glass']       # weighted; 'rock' is the slope


def segment_distance(xs, ys, lines):
    best = np.full(np.shape(xs), 1e9)
    for line in lines:
        for (ax, ay), (bx, by) in zip(line, line[1:]):
            dx, dy = bx - ax, by - ay
            t = np.clip(((xs - ax) * dx + (ys - ay) * dy) / (dx * dx + dy * dy), 0, 1)
            best = np.minimum(best, np.hypot(xs - (ax + t * dx), ys - (ay + t * dy)))
    return best


def road_masks(xs, ys):
    """Paved road and the tracks' two tread lines at world points (the third value: no creep path here)."""
    road = segment_distance(xs, ys, paving) < 320
    ruts = np.abs(segment_distance(xs, ys, tracks) - 150) < 55
    return road, ruts, np.zeros(np.shape(xs), bool)


cell_x, cell_y = np.meshgrid((gx - 64) * STEP + STEP / 2, (64 - gx) * STEP - STEP / 2)
_, cell_material = terrain(cell_x, cell_y)
road_cells, _, _ = road_masks(cell_x, cell_y)
cell_material[road_cells] = 'paving'
cell_material[np.hypot(cell_x - RING[0], cell_y - RING[1]) < RING_R + RING_WALL] = 'paving'
tile_bytes = np.vectorize(TILES.get)(cell_material).astype(np.uint8)

TEXEL_GRID = GRID * TEXELS
units = 65536.0 / TEXEL_GRID
tx, ty = np.meshgrid(-32768.0 + (np.arange(TEXEL_GRID) + 0.5) * units,
                     32768.0 - (np.arange(TEXEL_GRID) + 0.5) * units)
_, texel_material = terrain(tx, ty)
# The colony's old pavement round the core (the design's plating where its fine noise is above 0.3) reads from the
# air as white pavement full of black holes; closed and filled it reads as one cracked surface, its outer edge still
# ragged (the integrator's sheet review).
old_core = (texel_material == 'plating') & (np.hypot(tx, ty) < 9000)
core = ndimage.binary_fill_holes(ndimage.binary_closing(old_core, structure=np.ones((3, 3)), iterations=6))
texel_material[core & (texel_material == 'scorched')] = 'plating'
field = np.zeros((TEXEL_GRID, TEXEL_GRID, len(LAYERS)), dtype=np.float32)
for layer in LAYERS:
    field[..., LAYERS.index(layer)] = texel_material == layer
# The hatches' outcrops are the rim's black glass.
for name, (hx, hy) in SERVICE_EXITS.items():
    fx, fy = math.cos(math.radians(HATCH_FRONT[name])), math.sin(math.radians(HATCH_FRONT[name]))
    along = (tx - hx) * -fx + (ty - hy) * -fy
    across = -(tx - hx) * -fy + (ty - hy) * -fx
    outcrop = (along > 0) & (along < 1900) & (np.abs(across) < 1100)
    field[outcrop] = 0
    field[outcrop, LAYERS.index('glass')] = 1
softness = 90.0 / units
field = np.stack([ndimage.gaussian_filter(field[..., c], softness, mode='nearest') for c in range(len(LAYERS))], -1)
road_t, ruts_t, _ = road_masks(tx, ty)
for mask, layer, crisp in [(ruts_t, 'scree', 0.8), (road_t, 'paving', 0.75)]:
    weight = np.clip(ndimage.gaussian_filter(mask.astype(np.float32), crisp, mode='nearest'), 0, 1)
    field *= (1 - weight)[..., None]
    field[..., LAYERS.index(layer)] += weight
# The Blooding Ring's floor: the resin paving to the wall, scored with blade cuts (strokes a texel wide of the
# grey ash layer at most 0.6 over the paving, most of them in pairs: the Harrowers' twin cut; the old pavement's pale
# layer read as ragged white patches), drawn in a window round the ring.
ring_rows = np.nonzero(np.abs(ty[:, 0] - RING[1]) < RING_PAD)[0]
ring_cols = np.nonzero(np.abs(tx[0] - RING[0]) < RING_PAD)[0]
window = np.s_[ring_rows[0]:ring_rows[-1] + 1, ring_cols[0]:ring_cols[-1] + 1]
wx, wy = tx[window], ty[window]
floor = (np.hypot(wx - RING[0], wy - RING[1]) < RING_R + RING_WALL + 40).astype(np.float32)
cuts = np.zeros(wx.shape, np.float32)
cut_rng = np.random.default_rng(10147)              # its own stream: the map's other placements stay as they were
for _ in range(70):
    a, r = cut_rng.uniform(0, 2 * math.pi), math.sqrt(cut_rng.uniform(0, (RING_R - 150) ** 2))
    sx, sy = RING[0] + r * math.cos(a), RING[1] + r * math.sin(a)
    heading, length = cut_rng.uniform(0, math.pi), cut_rng.uniform(220.0, 620.0)
    ux, uy = math.cos(heading), math.sin(heading)
    for offset in ((0.0, 70.0) if cut_rng.uniform() < 0.6 else (0.0,)):
        ox, oy = sx - uy * offset, sy + ux * offset
        along = (wx - ox) * ux + (wy - oy) * uy
        across = np.abs(-(wx - ox) * uy + (wy - oy) * ux)
        taper = 1.0 - np.abs(along) / (length / 2)            # widest in the middle, to a point at both ends
        cuts = np.maximum(cuts, ((np.abs(along) < length / 2) & (across < 18.0 * taper)).astype(np.float32))
cuts *= floor
floor = np.clip(ndimage.gaussian_filter(floor, 0.8, mode='nearest'), 0, 1)
part = field[window]
part *= (1 - floor)[..., None]
part[..., LAYERS.index('paving')] += floor
cut_weight = np.clip(ndimage.gaussian_filter(cuts, 0.45, mode='nearest') * 1.2, 0, 0.6)
part *= (1 - cut_weight)[..., None]
part[..., LAYERS.index('ash')] += cut_weight
field[window] = part
field /= np.maximum(field.sum(-1, keepdims=True), 1e-6)
field = np.concatenate([field, np.zeros((TEXEL_GRID, TEXEL_GRID, 8 - len(LAYERS)), dtype=np.float32)], -1)
quantized = np.clip(field * 255 + 0.5, 0, 255).astype(np.uint8)
del texel_material

# --- Buildings (bmodels_out4.py, THE_CROWN.md section 12) -----------------------------------------------------------
ART = ROOT / 'design/kreegan_world/art'
SIZES = {}                          # texture -> native size (master / 4)
for folder in ['textures_d0/blv', 'textures_out1/masters', 'textures_interiors/masters', 'textures_k9_lattice/masters',
               'textures_k10_palace/masters', 'textures_k5_grafted/masters']:
    for png in (ART / folder).glob('*.png'):
        with Image.open(png) as image:
            SIZES.setdefault(png.stem, (image.width / 4, image.height / 4))
# A larger repeat for the textures whose detail reads too small at one native texel per world unit on buildings this
# large (the citadel's 5 760-wide walls, the 1 600-high towers).
TEXTURE_SCALE = {'hnfloor': 3.0, 'hocrown': 3.0, 'hodomrib': 4.0, 'homast': 1.5, 'hocannon': 2.0, 'honode': 2.0, 'hocondt': 1.5,
                 'horoost': 2.0, 'hokspine': 1.5, 'hokwall': 1.5, 'hoplate': 1.5, 'hoterm': 1.25, 'hhscrapw': 1.5,
                 'homarket': 1.25}
for texture, scale in TEXTURE_SCALE.items():
    SIZES[texture] = (SIZES[texture][0] * scale, SIZES[texture][1] * scale)
models = []
EVENTS = {}                         # event id -> (title, handler body)
COGS = {}                           # model name -> cog on every face (evt.SetFacetBit shows and hides it)
HIDDEN_MODELS = set()               # models that start Invisible and Untouchable
face_cogs = {}                      # (model name, face index) -> cog (a single face swapped by evt.SetTexture)


def ground(x, y):
    return height_at(x, y)


# Event ids (WORK_PACKAGES/README.md bands; THE_CROWN.md section 17).
EV_LOAD, EV_FIRST, EV_CANNONS, EV_RAID, EV_LANDER_TIMER, EV_MARKET_NOISE = 1, 2, 3, 4, 5, 6
EV_RELAY = {'West': 10, 'North': 11, 'East': 12, 'Plaza': 13}
EV_TABLETS, EV_PLATES = 14, 17
EV_CHESTS = 30
EV_DOORS = {'D6 West': 50, 'D7 East': 51, 'D16 North': 52}
EV_GATE, EV_LIFT, EV_LANDER = 53, 57, 58
EV_HATCH = {'D6 West': 54, 'D16 North': 55, 'D7 East': 56}
EV_PYLON = {'West': 70, 'North': 71, 'East': 72}
EV_COLLAR = 73
EV_STALL_VESK, EV_STALL_SORREL = 301, 302
EV_RING_PLATE, EV_RING, EV_VRETH = 21, 150, 151      # the Blooding Ring (HARROWERS.md)

crownspire, gate_face = kit.crownspire(ct.FORTRESS_HALF, FLOOR_Z, EV_GATE)
face_cogs[('crownspire', gate_face)] = kit.GATE_COG
# One great ion cannon on the dome's crown, where the mast stood (the user, 2026-10-23; COMBAT "Ion cannons"); the
# four corner bastions carry Crown Sentinels (placed actors, below).
DOME_CROWN = 8000.0                 # the dome's crown above the ground (THE_CROWN.md section 4, enlarged)
models += [crownspire, kit.dome(FLOOR_Z, ct.FORTRESS_HALF, DOME_CROWN)]
CANNONS = {name: tuple(p) for name, p in DETAIL['cannons'].items()}
BASTIONS = {name: tuple(p) for name, p in ct.BASTIONS.items()}
BASTION_H = 3600.0
DOME_RINGS = 5                      # kit.dome's rings: its flat crown is the top ring, at 4/5 of the quarter arc
DOME_TOP = FLOOR_Z + kit.WALL_H + (DOME_CROWN - kit.WALL_H) * math.sin(math.pi / 2 * (DOME_RINGS - 1) / DOME_RINGS)
# The model's pivot and muzzle over its origin, the mount's base (level_generation/creatures/hes_ion_cannon_codex,
# README "Geometry, scale and integration": the measured front-axis marker, map-local before the facing).
# The enlarged dome's curve hides its crown from the ground inside the cannon's reach, so the cannon stands on a
# 1 500 tower over the crown (pivot about 10 400 above the ground; the design's 8 400 would be out of sight).
CANNON_TOWER = 1500.0
CANNON_BASE = DOME_TOP + CANNON_TOWER
models.append(kit.cannon_tower(DOME_TOP, CANNON_TOWER))
CANNON_PIVOT = CANNON_BASE + 1200.0
MUZZLE_SIDE, MUZZLE_FORWARD, MUZZLE_UP = 4.9, 3188.9, 1150.5      # the bore's mouth, on the barrel's axis
for name, (cx, cy) in BASTIONS.items():
    models.append(kit.bastion(f'bastion_{name.lower()}', cx, cy, FLOOR_Z, ct.BASTION_R, BASTION_H))
mast_tops = {}
for name, (door, outward) in NODES.items():
    model, top = kit.blockhouse(f'node_{name.split()[0].lower()}', door, outward, ct.NODE_BUNKER_BACK,
                                ct.NODE_BUNKER_R, FLOOR_Z, EV_DOORS[name])
    models.append(model)
    mast_tops[name] = top
    # The conduit run from the fortress wall to the blockhouse's back.
    ox, oy = outward
    bx, by = door[0] - ox * ct.NODE_BUNKER_BACK, door[1] - oy * ct.NODE_BUNKER_BACK
    start = (ox * (ct.FORTRESS_HALF + 40), oy * (ct.FORTRESS_HALF + 40))
    end = (bx - ox * (ct.NODE_BUNKER_R - 60), by - oy * (ct.NODE_BUNKER_R - 60))
    models.append(kit.conduit(f'conduit_{name.split()[0].lower()}', start, end, height_at))
cover = Model('cover_slabs')
for kind, centre, length, angle in COVER:
    if kind == 'slab':
        kit.cover_slab(cover, centre, length, angle, height_at(*centre))
models.append(cover)
plaza_model, PLAZA_TOP = kit.plaza(PLAZA[0], PLAZA[1], FLOOR_Z, PLAZA_R)
models.append(plaza_model)
LIFT = tuple(DETAIL['plaza_lift'])
LIFT_RADIUS = 260.0
lift_front = math.radians(270.0)                               # the cage faces south, across the pad
lift_origin = (LIFT[0], LIFT[1] - LIFT_RADIUS)                 # the tower's axis is the design's point
models.append(kit.lift_kiosk(*lift_origin, PLAZA_TOP, lift_front, EV_LIFT))

districts = {'west_ward': Model('west_ward'), 'roosts': Model('roosts'), 'grafting_nw': Model('grafting_nw'),
             'grafting_se': Model('grafting_se'), 'cable_yards': Model('cable_yards'), 'market': Model('market'),
             'colony_ruins': Model('colony_ruins')}
DISTRICT_CENTRES = {name: tuple(centre) for name, (centre, _) in ct.DISTRICTS.items()}


def district_of(x, y):
    if x < -12000 and 4000 < y < 12000:
        return 'west_ward'
    if x > 12000 and -8000 < y < 0:
        return 'cable_yards'
    if y > 15000 and -10000 < x < 0:
        return 'colony_ruins'
    return min(DISTRICT_CENTRES, key=lambda n: math.hypot(x - DISTRICT_CENTRES[n][0], y - DISTRICT_CENTRES[n][1]))


def snapped_direction(x, y, target):
    """Degrees from (x, y) toward target, snapped to the nearest quarter."""
    return round(math.degrees(math.atan2(target[1] - y, target[0] - x)) / 90.0) % 4 * 90.0


ROOST_SIZES = []
roost_tops = []
PLINTH = next(tuple(c) for k, c, _, _ in FOOTPRINTS if k == 'plinth')
collar_face = None
stall_points = {}
ruin_count = 0
for kind, centre, size, angle in FOOTPRINTS:
    x, y = centre
    z = height_at(x, y)
    if kind == 'roost':
        heights_by_radius = {520: 3200.0, 420: 2400.0, 360: 1800.0, 380: 2000.0}
        top = kit.roost(districts['roosts'], x, y, z, size, heights_by_radius[size])
        roost_tops.append((x, y, z, size, heights_by_radius[size]))
    elif kind == 'shed':
        district = district_of(x, y)
        target = (17600.0, -4400.0) if district == 'cable_yards' else DISTRICT_CENTRES[district]
        kit.shed(districts[district], x, y, z, size[0], size[1], snapped_direction(x, y, target))
    elif kind == 'pen':
        directions = {'south': -90, 'east': 0, 'north': 90, 'west': 180}
        to_plinth = math.degrees(math.atan2(PLINTH[1] - y, PLINTH[0] - x))
        side = max(directions, key=lambda n: math.cos(math.radians(directions[n] + angle - to_plinth)))
        kit.pen(districts['market'], x, y, z, size[0], size[1], angle, open_side=side)
    elif kind == 'plinth':
        front = math.degrees(math.atan2(-1.0, 1.0))         # the collar faces the market's way in (south-east)
        collar_face = kit.auction_plinth(districts['market'], x, y, z, size, EV_COLLAR, front)
    elif kind == 'pavilion':
        kit.pavilion(districts['market'], x, y, z, size[0], size[1])
    elif kind == 'stall':
        stall_points['sorrel' if x > 0 else 'vesk'] = (x, y)
    elif kind == 'spine':
        kit.spine(districts['west_ward'], x, y, z, size)
    elif kind == 'dome':
        kit.ruin_dome(districts['colony_ruins'], x, y, z, size, open_from=270.0, seed=31 + ruin_count)
        ruin_count += 1
    elif kind == 'testplinth':
        pass                                                # with the blast wall below
for model in districts.values():
    if model.faces:
        models.append(model)
COLLAR_COG, VESK_COG, SORREL_COG, LANDER_COG = 9302, 9303, 9304, 9305
VESK_HOUSE, SORREL_HOUSE = 9400, 9401        # the stalls' shops (vendors, hesper_stage/npcs_crown.yml)
face_cogs[('market', collar_face)] = COLLAR_COG
# The stalls: Vesk's at the market's edge (house 9400, from 100601) and Sorrel's on the plaza's west side (house
# 9401, from M7: 100007), each its own model, hidden
# until its QBit (evt.SetFacetBit on the model's cog).
for who, event, cog in (('vesk', EV_STALL_VESK, VESK_COG), ('sorrel', EV_STALL_SORREL, SORREL_COG)):
    x, y = stall_points[who]
    front = math.radians(snapped_direction(x, y, (-15000.0, -15000.0) if who == 'vesk' else PLAZA))
    model = kit.stall(f'stall_{who}', x, y, height_at(x, y), front, event)
    models.append(model)
    COGS[model.name] = cog
    HIDDEN_MODELS.add(model.name)
test = Model('test_emplacement')
TEST_TOP = kit.test_plinth(test, *TEST_CANNON, height_at(*TEST_CANNON))
kit.blast_wall(test, TEST_WALL[0], TEST_WALL[1], height_at)
models.append(test)
for name, (hx, hy) in SERVICE_EXITS.items():
    models.append(kit.hatch(f'hatch_{name.split()[0].lower()}', hx, hy, hatch_levels[name], HATCH_FRONT[name],
                            EV_HATCH[name]))
ring_model, RING_DAIS_TOP = kit.blooding_ring(*RING, FLOOR_Z, RING_R, RING_GATE, thick=RING_WALL, cheek=RING_CHEEK,
                                              blind=RING_BLIND, blind_half=RING_BLIND_HALF)
models.append(ring_model)
GATE_OUT = (math.cos(math.radians(RING_GATE)), math.sin(math.radians(RING_GATE)))
RING_GATE_POINT = (RING[0] + GATE_OUT[0] * (RING_R + RING_WALL / 2), RING[1] + GATE_OUT[1] * (RING_R + RING_WALL / 2))


def ring_sight_from_road():
    """The share of the ring's floor each point of the ring road (every 100 within 8 000) sees, eye and target both
    under the walls' 400: a line reaches the floor only through the gate, past its cheek walls and the blind wall.
    Returns the worst share."""
    road = []
    line = ct.ring_line(24)
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay) / 100))
        road += [(ax + (bx - ax) * k / n, ay + (by - ay) * k / n) for k in range(n)]
    g = np.linspace(-RING_R + 50, RING_R - 50, 47)
    fx, fy = np.meshgrid(g, g)
    keep = np.hypot(fx, fy) < RING_R - 50
    fx, fy = fx[keep] + RING[0], fy[keep] + RING[1]
    gate, step = math.radians(RING_GATE), 2 * math.pi / kit.RING_SIDES
    ox, oy = GATE_OUT
    qx, qy = -oy, ox
    opening, inner_face = RING_R * math.sin(step), RING_R * math.cos(step)

    def crosses(px, py, a, b):
        dx, dy, ex, ey = fx - px, fy - py, b[0] - a[0], b[1] - a[1]
        den = dx * ey - dy * ex
        with np.errstate(divide='ignore', invalid='ignore'):
            t = ((a[0] - px) * ey - (a[1] - py) * ex) / den
            u = ((a[0] - px) * dy - (a[1] - py) * dx) / den
        return (t > 0) & (t < 1) & (u >= 0) & (u <= 1)

    def at(along, across):
        return RING[0] + ox * along + qx * across, RING[1] + oy * along + qy * across
    screens = [(at(inner_face, side * opening), at(RING_R + RING_WALL + RING_CHEEK, side * opening)) for side in (-1, 1)]
    screens.append((at(RING_BLIND_FACE - RING_WALL / 2, -RING_BLIND_HALF - RING_WALL / 2),
                    at(RING_BLIND_FACE - RING_WALL / 2, RING_BLIND_HALF + RING_WALL / 2)))
    worst = 0.0
    for px, py in road:
        if math.hypot(px - RING[0], py - RING[1]) > 8000:
            continue
        dx, dy = fx - px, fy - py
        cx, cy = px - RING[0], py - RING[1]
        a, b = dx * dx + dy * dy, 2 * (cx * dx + cy * dy)
        c = cx * cx + cy * cy - (RING_R + RING_WALL / 2) ** 2
        t = (-b - np.sqrt(np.maximum(b * b - 4 * a * c, 0))) / (2 * a)
        through = np.abs(np.angle(np.exp(1j * (np.arctan2(cy + t * dy, cx + t * dx) - gate)))) < step - 0.03
        for screen in screens:
            through &= ~crosses(px, py, *screen)
        worst = max(worst, float(through.mean()))
    return worst


RING_SIGHT = ring_sight_from_road()
assert RING_SIGHT == 0.0, f'the ring road sees {RING_SIGHT:.3f} of the Blooding Ring\'s floor'

# --- Decorations, chests and the party start ------------------------------------------------------------------------
ids = json.loads((ROOT / 'output/hesper_stage/decoration_ids.json').read_text())
DECORATION_RADII = {d['name']: d.get('radius', 0) for d in yaml.safe_load(
    (STAGE_DATA / 'decorations.yml').read_text())['decorations']}
entities = []
model_placements = []                   # the big models the minimap draws (build_minimap_blender.py)
MINIMAP_MODELS = {'hes_great_cannon', 'hes_node_mast', 'hes_crawler_wreck', 'hes_grafting_frame', 'hes_cable_spool'}


def decoration(name, x, y, facing=None, event=0, cog=0, z=None, sink=0.0):
    """A decoration entity. A click runs `event` (the engine reads the secondary slot); `cog` (the primary) keys
    evt.SetSprite's swaps."""
    assert name in ids, f'{name}: not staged (hesper_stage/decorations.yml, then stage.py)'
    facing = int(rng.integers(0, 360)) if facing is None else int(round(facing)) % 360
    position = {'x': int(round(x)), 'y': int(round(y)), 'z': int(round((height_at(x, y) if z is None else z) - sink))}
    if name in MINIMAP_MODELS:
        model_placements.append({'name': name, **position, 'facing': facing})
    entities.append({'entity_index': 0, 'name': name, 'decoration_list_id': ids[name] - 1, 'ai_attributes': 0,
                     'position': position, 'facing': facing, 'event_id_primary': cog,
                     'event_id_secondary': event, 'variable_primary': 0, 'variable_secondary': 0, 'special_trigger': 0,
                     'initial_decoration_flag': 0})


def facing_to(x, y, target):
    return math.degrees(math.atan2(target[1] - y, target[0] - x))


FRONT_YAW = 270          # a model whose front is its glTF +z faces `front` at facing = front + 270 (hesper_out1)


# The ion cannons on the bastions (lit; `_dark` once the Lattice falls: cogs 9311-9314), facing out along the
# diagonal; the node masts on the blockhouses' crowns (lit; `_off`: cogs 9321-9323).
CANNON_COGS = {name: 9311 + k for k, name in enumerate(CANNONS)}
for name, (cx, cy) in CANNONS.items():               # facing south, over the gate road and the plaza
    decoration('hes_great_cannon', cx, cy, facing=270 + FRONT_YAW, cog=CANNON_COGS[name], z=CANNON_BASE)
MAST_COGS = {name: 9321 + k for k, name in enumerate(NODES)}
for name, (mx, my, mz) in mast_tops.items():
    decoration('hes_node_mast', mx, my, facing=0, cog=MAST_COGS[name], z=mz - 40)

# Door ways (700 out and 900 wide before every door and entrance): no decoration, no actor, no spawn point.
door_ways = []                                  # (x, y, out_x, out_y)
for name, (door, (ox, oy)) in NODES.items():
    door_ways.append((door[0], door[1], ox, oy))
door_ways.append((0.0, -ct.FORTRESS_HALF - kit.GATEHOUSE_DEPTH, 0.0, -1.0))
for name, (hx, hy) in SERVICE_EXITS.items():
    door_ways.append((hx, hy, math.cos(math.radians(HATCH_FRONT[name])), math.sin(math.radians(HATCH_FRONT[name]))))
door_ways.append((LIFT[0], LIFT[1] - LIFT_RADIUS - 120, 0.0, -1.0))
for who, (x, y) in stall_points.items():
    target = (-15000.0, -15000.0) if who == 'vesk' else PLAZA
    a = math.radians(snapped_direction(x, y, target))
    door_ways.append((x + math.cos(a) * 250, y + math.sin(a) * 250, math.cos(a), math.sin(a)))
door_ways.append((*RING_GATE_POINT, *GATE_OUT))


def in_door_way(x, y, margin=0.0):
    return any(-50 < (x - dx) * ox + (y - dy) * oy < 700 + margin and
               abs(-(x - dx) * oy + (y - dy) * ox) < 450 + margin for dx, dy, ox, oy in door_ways)


footprint_discs = [((0.0, 0.0), ct.FORTRESS_HALF * 1.45), (PLAZA, PLAZA_R + 150)]
for door, (ox, oy) in NODES.values():
    footprint_discs.append(((door[0] - ox * ct.NODE_BUNKER_BACK, door[1] - oy * ct.NODE_BUNKER_BACK),
                            ct.NODE_BUNKER_R + 150))
for kind, centre, size, angle in FOOTPRINTS:
    if kind in ('fortress', 'plaza'):
        continue
    footprint_discs.append((centre, (math.hypot(*size) / 2 if isinstance(size, list) else size) + 150))
for kind, centre, length, angle in COVER:
    footprint_discs.append((centre, length / 2 + 150))
footprint_discs += [(TEST_CANNON, 450), (((TEST_WALL[0][0] + TEST_WALL[1][0]) / 2,
                                          (TEST_WALL[0][1] + TEST_WALL[1][1]) / 2), 850)]
for name, (hx, hy) in SERVICE_EXITS.items():
    footprint_discs.append(((hx, hy), 700))
footprint_discs.append((RING, RING_BLIND_FACE + 250))


def in_range(x, y):
    return min(math.hypot(x - cx, y - cy) for cx, cy in CANNONS.values()) <= ct.RANGE_GROUND


def level_ground(x, y, rise=80.0):
    z = height_at(x, y)
    return all(abs(height_at(x + dx, y + dy) - z) < rise for dx, dy in ((150, 0), (-150, 0), (0, 150), (0, -150)))


def clear(x, y, margin=0.0, road_gap=160.0):
    """Free ground for a decoration: inside the square, off every footprint and door way, at least road_gap off the
    roads' edges and the tracks."""
    if abs(x) > BOUND - 500 or abs(y) > BOUND - 500:
        return False
    if any(math.hypot(x - c[0], y - c[1]) < r + margin for c, r in footprint_discs):
        return False
    if in_door_way(x, y, 100):
        return False
    road_d = segment_distance(np.array([x]), np.array([y]), paving)[0]
    track_d = segment_distance(np.array([x]), np.array([y]), tracks)[0]
    return road_d > 320 + road_gap and track_d > 260


def spaced(x, y, gap, kind=None):
    return all(math.hypot(x - e['position']['x'], y - e['position']['y'])
               >= (gap if kind and e['name'].startswith(kind) else min(gap, 180.0)) for e in entities)


# DECOR (make_crown_detail.py): each group scattered round its anchor, off the roads, the footprints and the doors,
# on level ground; the killing ground's debris only inside the range (it is not cover: all under 300 high), the
# rest outside it. The gilded fire bowls burn at the roosts and the plaza (K10), the plain ones elsewhere (K5).
SYMBOLS = {'frame': 'hes_grafting_frame', 'banner': 'hes_membrane_banner', 'pod': 'hes_creep_pod',
           'crate': 'hes_crate_clean', 'spool': 'hes_cable_spool', 'pylon_dead': 'hes_light_pylon_off',
           'trophy': 'hes_trophy_pile', 'shard': 'hes_glass_shards', 'boulder': 'hes_glass_boulder',
           'debris': 'hes_fallen_plates'}
dressing = {}
for symbol, ax, ay, count, spread in DETAIL['decor']:
    if symbol == 'bowl':
        name = 'hes_fire_bowl_gilded_out' if (ax > 12000 and ay > 12000) or (ax, ay) == tuple(PLAZA) else \
            'hes_fire_bowl_out'
    else:
        name = SYMBOLS[symbol]
    placed = 0
    rise = 160.0 if symbol in ('shard', 'boulder') else 80.0
    # Round the plaza the group stands on a ring outside the pad (the pad stays clear for the lander); a group that
    # finds no room within its spread (an anchor on a road) tries a wider ring once.
    rings = [(PLAZA_R + 250, PLAZA_R + 250 + spread * 0.5)] if (ax, ay) == PLAZA else \
        [(spread * 0.2, spread), (max(spread, 450.0), spread * 2.5 + 600)]
    for attempt in range(count * 60 * len(rings)):
        if placed == count:
            break
        inner, outer = rings[attempt // (count * 60)]
        a, r = rng.uniform(0, 2 * math.pi), math.sqrt(rng.uniform(inner ** 2, outer ** 2))
        x, y = ax + r * math.cos(a), ay + r * math.sin(a)
        if not clear(x, y, 60 if symbol != 'debris' else 0) or not level_ground(x, y, rise):
            continue
        if (symbol == 'debris') != in_range(x, y):
            continue
        if not spaced(x, y, 420 if symbol in ('frame', 'spool', 'boulder') else 300, name):
            continue
        facing = facing_to(x, y, (ax, ay)) + FRONT_YAW if symbol in ('frame', 'banner') else None
        decoration(name, x, y, facing=facing, sink=20 if symbol in ('shard', 'boulder', 'debris') else 0)
        placed += 1
    dressing[f'{symbol} {ax},{ay}'] = f'{placed}/{count}'

# The Blooding Ring's dressing (HARROWERS.md): six fire bowls on the wall's inner foot, trophy piles between them (none
# before the gate), two banners beside the gate's cheek walls and the glyph plate (event 21) on its post before the
# blind wall, where the track ends.
for k in range(6):
    a = math.radians(RING_GATE + 30 + 60 * k)
    decoration('hes_fire_bowl_out', RING[0] + (RING_R - 110) * math.cos(a), RING[1] + (RING_R - 110) * math.sin(a),
               facing=0)
for k in range(1, 6):
    a = math.radians(RING_GATE + 60 * k)
    x, y = RING[0] + (RING_R - 150) * math.cos(a), RING[1] + (RING_R - 150) * math.sin(a)
    decoration('hes_trophy_pile', x, y, facing=facing_to(x, y, RING) + FRONT_YAW + 37 * k)
for side in (-1, 1):
    along, across = RING_R + RING_WALL + 170, side * 500
    x, y = RING[0] + GATE_OUT[0] * along - GATE_OUT[1] * across, RING[1] + GATE_OUT[1] * along + GATE_OUT[0] * across
    decoration('hes_membrane_banner', x, y, facing=facing_to(x, y, (x + GATE_OUT[0], y + GATE_OUT[1])) + FRONT_YAW)
# The passage between the gate and the blind wall lies in both walls' shadow (the integrator's review of ring01): a
# fire bowl against the blind wall's inner face at each end of it.
for side in (-1, 1):
    along, across = RING_BLIND_FACE - RING_WALL - 70, side * 450
    decoration('hes_fire_bowl_out', RING[0] + GATE_OUT[0] * along - GATE_OUT[1] * across,
               RING[1] + GATE_OUT[1] * along + GATE_OUT[0] * across, facing=0)
RING_PLATE = (RING[0] + GATE_OUT[0] * (RING_BLIND_FACE + 140) + GATE_OUT[1] * 420,
              RING[1] + GATE_OUT[1] * (RING_BLIND_FACE + 140) - GATE_OUT[0] * 420)
decoration('hes_glyph_plate', *RING_PLATE, event=EV_RING_PLATE,
           facing=facing_to(*RING_PLATE, (RING_PLATE[0] + GATE_OUT[0], RING_PLATE[1] + GATE_OUT[1])) + FRONT_YAW)

# The alarm pylons (events 70-72, cogs the same: evt.SetSprite swaps the dead one in), Aster's relay posts (10-13),
# the colony log tablets' plinths (14-16, the tablets on them as ground items) and the four glyph plates (17-20).
PYLONS = {name: tuple(p) for name, p in DETAIL['pylons'].items()}
for name, (x, y) in PYLONS.items():
    decoration('hes_alarm_pylon', x, y, facing=facing_to(x, y, (0.0, 0.0)), event=EV_PYLON[name], cog=EV_PYLON[name])
RELAYS = {name: tuple(p) for name, p in DETAIL['relays'].items()}
for name, (x, y) in RELAYS.items():
    decoration('hes_relay_post', x, y, facing=facing_to(x, y, (0.0, 0.0)), event=EV_RELAY[name])
PLACES = DETAIL['places']
TABLETS = [(p['x'], p['y']) for p in PLACES if p['kind'] == 'tablet']
for k, (x, y) in enumerate(TABLETS):
    decoration('hes_tablet_plinth', x, y, facing=0, event=EV_TABLETS + k)
PLATES = [(p['x'], p['y'], p['label']) for p in PLACES if p['kind'] == 'plate']
PLATE_FACING = []
for k, (x, y, label) in enumerate(PLATES):
    nearest = min((p for line in paving for p in resample(line, 200)), key=lambda p: math.hypot(p[0] - x, p[1] - y))
    PLATE_FACING.append(facing_to(x, y, nearest))
    decoration('hes_glyph_plate', x, y, facing=PLATE_FACING[-1] + FRONT_YAW, event=EV_PLATES + k)
# The Kept market's collar posts: two in each pen, by its back wall (the Labourers chained to them).
pen_posts = []
for kind, (x, y), size, angle in FOOTPRINTS:
    if kind != 'pen':
        continue
    a = math.radians(angle)
    to_plinth = math.atan2(PLINTH[1] - y, PLINTH[0] - x)
    for side in (-1, 1):
        along = size[0] * 0.25 * side if size[0] >= size[1] else 0.0
        across = size[1] * 0.25 * side if size[1] > size[0] else 0.0
        px, py = x + along * math.cos(a) - across * math.sin(a), y + along * math.sin(a) + across * math.cos(a)
        px, py = px - math.cos(to_plinth) * 120, py - math.sin(to_plinth) * 120
        pen_posts.append((px, py))
        decoration('hes_pen_post', px, py, facing=math.degrees(to_plinth) + FRONT_YAW)

# The chests (events 30-38, crown_detail's chest places in order): Kreegan pods and colonial lockers. The Noble's hoard
# stands on the tallest roost's crown; the dare is in the crawler wreck; the slavers' strongbox is locked (Hacking
# Master, +50 % gold: LOOT_RULES).
CHESTS = {'chest_c': 'hes_colonial_locker', 'chest_k': 'hes_kreegan_pod_chest'}
WRECK = next((centre, angle) for kind, centre, _, angle in COVER if kind == 'wreck')
loot = []
chest_events = {}
tallest = max(roost_tops, key=lambda r: r[4])
for kind, x, y, label in [(p['kind'], p['x'], p['y'], p['label']) for p in PLACES if p['kind'] in CHESTS]:
    index = len(loot)
    event = EV_CHESTS + index
    z = None
    if 'hoard' in label:
        x, y, z = tallest[0], tallest[1], tallest[2] + tallest[4]
    if 'wreck' in label:                        # in the wreck's opening (its front: facing + 90), on its floor
        (wx, wy), degrees = WRECK
        x, y = wx + math.cos(math.radians(degrees + 90)) * 40, wy + math.sin(math.radians(degrees + 90)) * 40
        z = height_at(wx, wy) + 25
    decoration(CHESTS[kind], x, y, event=event, z=z, facing=facing_to(x, y, (0.0, 0.0)))
    strongbox = 'strongbox' in label
    loot.append({'source_id': f'hesper:out4:chest_{index}', 'source_object_index': index,
                 'source_name': label.split(':')[0].split(' (')[0],
                 'position': {'x': int(x), 'y': int(y), 'z': int(height_at(x, y) if z is None else z)},
                 'container_id': index, 'kind': 'chest', 'presentation': CHESTS[kind].replace('hes_', ''),
                 'random_treasure_level': 3, 'treasure_type': 0, 'gold': 18000 if strongbox else 12000,
                 'gold_only': False, 'random': True, 'ai_drop': False, 'trap_level': 0,
                 'should_repopulate': False, 'fixed_items': [], 'remove_when_empty': False})
    chest_events[event] = (index, label, strongbox)
assert len(loot) == 9, loot

# The crawler wreck (a model with an invisible collision box: its locker inside) and, from 100607, the lander on the
# pad (stand-in: Starport Reach's wrecked lander until the whole lander is modelled), hidden until then.
colliders = Model('colliders')
lander_box = Model('lander_box')
decoration('hes_crawler_wreck', *WRECK[0], facing=WRECK[1])
LANDER = (PLAZA[0] - 300.0, PLAZA[1] - 200.0)
decoration('hes_lander_wreck', *LANDER, facing=200, event=EV_LANDER, cog=LANDER_COG, z=PLAZA_TOP)
lander_box.collider((LANDER[0], LANDER[1], PLAZA_TOP - 20), (1200, 700, 520), yaw=math.radians(200))
COGS['lander_box'] = LANDER_COG
HIDDEN_MODELS.add('lander_box')


def wreck_collider():
    """The wreck's box, 900 x 450 x 400, leaving its open +z side's middle free for the locker (a box each side)."""
    (cx, cy), degrees = WRECK
    yaw = math.radians(degrees)
    c, s = math.cos(yaw), math.sin(yaw)
    for along, length in ((-300.0, 300.0), (300.0, 300.0)):
        colliders.collider((cx + c * along, cy + s * along, height_at(cx, cy) - 40), (length, 450, 440), yaw=yaw)
    colliders.collider((cx + s * 160, cy - c * 160, height_at(cx, cy) - 40), (300, 130, 440), yaw=yaw)


wreck_collider()

# --- Ground items: the tablets, the gold piles and the scouts' caches ------------------------------------------------
staged_item_rows = {int(row[0]): row for row in (line.split('\t') for line in
                    (STAGE / 'worlds/hesper/data_tables/items.txt').read_text().splitlines()) if row and row[0].isdigit()}
engine_item_rows = {int(row[0]): row for row in (line.split('\t') for line in
                    (ROOT / 'assets_dev/engine/data_tables/items.txt').read_text(encoding='latin-1').splitlines()[1:])
                    if row and row[0].isdigit()}
object_ids = [int(line.split('\t')[2]) for line in (ROOT / 'assets_dev/engine/data_tables/object_list.txt')
              .read_text(encoding='latin-1').splitlines()[1:] if line.strip()]
ground_items = []


def ground_item(item_id, x, y, z, gold=0):
    row = staged_item_rows.get(item_id) or engine_item_rows[item_id]
    sprite = int(row[11])
    item_bytes = item_id.to_bytes(4, 'little') + bytes(8) + int(gold).to_bytes(4, 'little') + bytes(20)
    ground_items.append({
        'sprite_object_index': len(ground_items), 'sprite_id': sprite,
        'object_description_id': object_ids.index(sprite),
        'position': {'x': int(round(x)), 'y': int(round(y)), 'z': int(round(z))},
        'velocity': {'x': 0, 'y': 0, 'z': 0}, 'yaw_angle': int(rng.integers(0, 2048)), 'sound_id': 0,
        'attributes': 0, 'sector_id': 0, 'time_since_created': 0, 'temporary_lifetime': 0,
        'glow_radius_multiplier': 0, 'spell_id': 0, 'spell_level': 0, 'spell_skill': 0, 'field54': 0,
        'spell_caster_pid': 0, 'spell_target_pid': 0, 'lod_distance': 0, 'spell_caster_ability': 0,
        'initial_position': {'x': 0, 'y': 0, 'z': 0}, 'raw_containing_item_hex': item_bytes.hex().upper()})


plinth_top = 135                                     # hes_tablet_plinth: 1.35 m
for k, (x, y) in enumerate(TABLETS):                 # the S9 tablets X-XII (P4's READABLES, 11369-11371)
    ground_item(11369 + k, x, y, height_at(x, y) + plinth_top + 2)
GOLD = [(p['x'], p['y']) for p in PLACES if p['kind'] == 'gold']
for k, (x, y) in enumerate(GOLD):                    # 1 500-3 500 each (LOOT_RULES: the Crown's four piles)
    amount = (1500, 2500, 3500, 2000)[k % 4]
    ground_item(189 if amount >= 3000 else 188, x, y, height_at(x, y), gold=amount)
CACHES = [(p['x'], p['y']) for p in PLACES if p['kind'] == 'cache']
for x, y in CACHES:                                  # two Shield Cells and a Stim each, before the node runs
    for k, item in enumerate((11300, 11300, 11302)):
        ground_item(item, x + 60 * (k - 1), y + 40 * (k % 2), height_at(x, y))

# --- Actors: the placed groups, the market, the people; then the spawn points ---------------------------------------
MONSTER_ROWS = {int(row[0]): row for row in (line.split('\t') for line in
                (ROOT / 'design/kreegan_world/data/monster_data.txt').read_text().splitlines()) if row[0].isdigit()}
STAGE_MONSTERS = {m['id']: m for m in yaml.safe_load((STAGE_DATA / 'monsters.yml').read_text())['monsters']}
NOBLE, DUELLIST, COURT_NOBLE, COURT_OVERSEER = 10040, 10041, 10042, 10032
LABOURER, ENFORCER, TEST_EMPLACEMENT, FREED_M, FREED_F = 10060, 10062, 10140, 10260, 10261
VRETH = 10147
GROUPS = {'door_west': 78, 'door_east': 79, 'door_north': 80, 'roosts': 81, 'master_nw': 82, 'master_se': 83,
          'slaver': 84, 'labourers': 85, 'enforcers': 86, 'freed': 87, 'test': 89, 'sentinels': 90,
          'raid_ne': 68, 'raid_n': 69, 'raid_w': 70, 'vreth': 91}
INVISIBLE, AGGRESSOR = 0x00010000, 0x00080000
actors = []
ground_check = None                                   # spawns.Ground, made once the models are final


def actor(monster, x, y, facing, z=None, posted=False, name='', group=0, attributes=0, npc=0, search=True):
    radius, height = STAGE_MONSTERS[monster]['radius'], STAGE_MONSTERS[monster]['height']
    flier = MONSTER_ROWS[monster][9] == 'Y'
    if z is None and search and not actor_free(x, y, radius, flier):
        for ring in range(1, 30):
            spots = [(x + 80 * ring * math.cos(a), y + 80 * ring * math.sin(a))
                     for a in np.linspace(0, 2 * math.pi, 8 + 4 * ring, endpoint=False)]
            free = [p for p in spots if actor_free(*p, radius, flier)]
            if free:
                x, y = free[0]
                break
        else:
            raise SystemExit(f'no room for {monster} {name} near {x:.0f}, {y:.0f}')
    row = MONSTER_ROWS[monster]
    actors.append({'actor_index': len(actors), 'name': name, 'npc_id': npc, 'attributes': attributes,
                   'hp': int(row[4]), 'hostility_type': int(row[12]), 'monster_info_id': monster,
                   'monster_id': monster, 'radius': radius, 'height': height,
                   'move_speed': 0 if posted else int(row[13]),
                   'position': {'x': int(round(x)), 'y': int(round(y)),
                                'z': int(round(height_at(x, y) if z is None else z))},
                   'initial_yaw_units': int(round((facing % 360) / 360 * 2048)) % 2048, 'immobile': posted,
                   'sprite_ids': [0, 0, 0, 0], 'sector_id': 0, 'current_action_animation': 0, 'carried_item_id': 0,
                   'group': group, 'ally': 0, 'unique_name_index': 0})


def tiles_walkable(x, y, radius):
    """Every terrain tile within radius spans at most 448 (the engine slides monsters off 512)."""
    for dx in (-radius, 0, radius):
        for dy in (-radius, 0, radius):
            iy = int(np.clip((32768.0 - (y + dy)) // STEP, 0, GRID - 2))
            ix = int(np.clip((x + dx + 32768.0) // STEP, 0, GRID - 2))
            quad = heights[iy:iy + 2, ix:ix + 2]
            if quad.max() - quad.min() > 448:
                return False
    return True


def actor_free(x, y, radius, flier):
    if in_door_way(x, y):
        return False
    if not flier and not tiles_walkable(x, y, radius):
        return False
    if not ground_check.free(x, y, radius, walker=not flier):
        return False
    return all(math.hypot(x - a['position']['x'], y - a['position']['y']) >= radius + a['radius'] + 60
               for a in actors)


# The colliders and the hidden lander's box block like walls; the occupancy grid sees every model's upright faces.
if colliders.faces:
    models.append(colliders)
models.append(lander_box)
ground_check = Ground(models, entities, height_at, road_masks, lambda placement: False, BOUND)

# The door posts: two Noble Duellists 300 outside each node door (THE_CROWN.md section 7, 78-80), placed immobile:
# they hold the door and shoot (the only hostiles inside range).
DOOR_POSTS = {'D6 West': 'door_west', 'D7 East': 'door_east', 'D16 North': 'door_north'}
for name, (door, (ox, oy)) in NODES.items():
    for side in (-1, 1):
        x = door[0] + ox * 300 - oy * 420 * side
        y = door[1] + oy * 300 + ox * 420 * side
        actor(DUELLIST, x, y, math.degrees(math.atan2(oy, ox)), posted=True, name='door post',
              group=GROUPS[DOOR_POSTS[name]], search=False)
# The roosts (81): two Court Nobles and three Duellists perched on the towers' platforms (immobile: the Court Nobles'
# post tactic flies them down within its leash), four Nobles on the plaza between the towers (free).
roost_order = sorted(roost_tops, key=lambda r: -r[4])
for k, (x, y, z, radius, height) in enumerate(roost_order):
    perch = z + height * 0.8
    out = math.atan2(y - 15800.0, x - 15800.0) + math.pi
    px, py = x + math.cos(out) * radius * 1.2, y + math.sin(out) * radius * 1.2
    actor(COURT_NOBLE if k < 2 else DUELLIST, px, py, math.degrees(out), z=perch, posted=True, name='roost perch',
          group=GROUPS['roosts'])
roost_plaza = (15600.0, 15600.0)
for k in range(4):
    a = 2 * math.pi * k / 4 + 0.4
    actor(NOBLE, roost_plaza[0] + 700 * math.cos(a), roost_plaza[1] + 700 * math.sin(a), 225, name='roost noble',
          group=GROUPS['roosts'])
# The district masters (82-84): a Court Noble each, immobile on its post (10042's post tactic: leash 1 536).
masters = [p for p in PLACES if p['kind'] == 'm_court' and ('master' in p['label'] or 'slaver' in p['label'])]
for p in masters:
    group = 'slaver' if 'slaver' in p['label'] else ('master_nw' if p['x'] < 0 else 'master_se')
    actor(COURT_NOBLE, p['x'], p['y'], facing_to(p['x'], p['y'], (0.0, 0.0)), posted=True, name=group,
          group=GROUPS[group])
# The Kept market (85, 86): ten collared Labourers, two in each pen by its collar posts (immobile), and six Enforcers
# round the plinth (free, wandering). Hostile while collared (relations.yml: the kreegans faction); event 73 frees them.
for k, (px, py) in enumerate(pen_posts):
    actor(LABOURER, px + 80 * math.cos(k), py + 80 * math.sin(k), facing_to(px, py, PLINTH), posted=True,
          name='Kept labourer', group=GROUPS['labourers'])
for k in range(6):
    a = 2 * math.pi * k / 6
    actor(ENFORCER, PLINTH[0] + 750 * math.cos(a), PLINTH[1] + 750 * math.sin(a), math.degrees(a),
          name='Kept enforcer', group=GROUPS['enforcers'])
# Anni and Tor (P4's 9611, 9612; actor rows 10261, 10260) beside Vesk's stall, shown once the market is freed.
vx, vy = stall_points['vesk']
for (monster, npc, nm), (dx, dy) in zip([(FREED_F, 9611, 'Anni'), (FREED_M, 9612, 'Tor')], [(-500, 300), (500, 300)]):
    actor(monster, vx + dx, vy + dy, facing_to(vx + dx, vy + dy, PLINTH), posted=True, name=nm, npc=npc,
          group=GROUPS['freed'], attributes=INVISIBLE)
# The Crown Sentinels (10057, ordinary killable turrets; the staged Ward Turret binding) on the four bastions' tops,
# facing out along the diagonals.
CROWN_SENTINEL = 10057
for name, (bx, by) in BASTIONS.items():
    actor(CROWN_SENTINEL, bx, by, math.degrees(math.atan2(by, bx)), z=FLOOR_Z + BASTION_H, posted=True,
          name='Crown Sentinel', group=GROUPS['sentinels'], search=False)
# The test emplacement (10140) on its plinth: a Stationary turret, Kreegan-friendly and party-hostile.
actor(TEST_EMPLACEMENT, *TEST_CANNON, facing_to(*TEST_CANNON, (12000.0, -13600.0)), z=TEST_TOP, posted=True,
      name='test emplacement', group=GROUPS['test'], search=False)
# The air raid (68-70): two Court Overseers behind the rim's crest at each place, hidden until event 4.
for p, group in zip([p for p in PLACES if p['kind'] == 'm_raid'], ('raid_ne', 'raid_n', 'raid_w')):
    for side in (-1, 1):
        x, y = p['x'] + 300 * side, p['y'] - 200 * side
        actor(COURT_OVERSEER, x, y, facing_to(x, y, (0.0, 0.0)), z=height_at(x, y) + 500, name='raid',
              group=GROUPS[group], attributes=INVISIBLE | AGGRESSOR, search=False)

# Huntmaster Vreth (10147) on his dais facing the gate (HARROWERS.md): placed immobile, so his `post` tactic (leash
# 1 300, hesper_stage/monsters.yml) keeps him in the ring; hidden on load once 100609 is set; he carries the Striking
# Lattice (event 1: evt.SetMonsterItem), which drops with his body.
VRETH_INDEX = len(actors)
actor(VRETH, *RING, RING_GATE, z=RING_DAIS_TOP, posted=True, name='Huntmaster Vreth', group=GROUPS['vreth'],
      search=False)

# R5 Ashkite wildlife: Storm Kite roosts outside the cannon table, over the B2/G7 grafting yards.
for flock, (cx, cy) in enumerate(((-16000, 15500), (16500, -16000))):
    assert math.hypot(cx - TEST_CANNON[0], cy - TEST_CANNON[1]) > 2200
    for k in range(4):
        t = k * math.pi / 2
        actor(10312, cx + 420 * math.cos(t), cy + 420 * math.sin(t), math.degrees(t),
              name=f'Storm Kite grafting-yard flock {flock + 1}', group=150 + flock)

# Spawn points: the yards' and the streets' Drudge Hulk gangs (slot 1, fixed tier C), the Overseer flights (slot 2,
# fixed C) and the ring's Noble patrols (slot 3, by difficulty), one point per design group, 500 off the roads.
SPAWN_RADIUS = 128


def encounter_index(slot, tier):
    """The ODM spawn index: 1-3 a slot at a random tier, 4-12 a slot at a fixed tier (4 + 3 x tier + slot - 1)."""
    return slot if not tier else 4 + 3 * 'ABC'.index(tier) + slot - 1


SPAWN_GROUPS = {'m_hulk': (1, 'C', 51), 'm_overseer': (2, 'C', 61), 'm_noble': (3, None, 71)}
spawns, spawn_plan, moved = [], [], []
counters = {kind: 0 for kind in SPAWN_GROUPS}
for p in PLACES:
    if p['kind'] not in SPAWN_GROUPS:
        continue
    slot, tier, first_group = SPAWN_GROUPS[p['kind']]
    flier = p['kind'] == 'm_overseer'
    x, y = p['x'], p['y']

    def ok(px, py):
        return not in_door_way(px, py) and math.hypot(px - RING[0], py - RING[1]) > RING_BLIND_FACE + 400 and \
            ground_check.free(px, py, 2 * 60 + SPAWN_RADIUS, walker=not flier, off_road=500) and \
            (flier or tiles_walkable(px, py, 2 * 60 + SPAWN_RADIUS)) and \
            all(math.hypot(px - s['position']['x'], py - s['position']['y']) > 900 for s in spawns)
    if not ok(x, y):
        for ring in range(1, 40):
            spots = [(x + 80 * ring * math.cos(a), y + 80 * ring * math.sin(a))
                     for a in np.linspace(0, 2 * math.pi, 8 + 4 * ring, endpoint=False)]
            free = [q for q in spots if ok(*q)]
            if free:
                moved.append((p['label'], ring * 80))
                x, y = free[0]
                break
        else:
            raise SystemExit(f'no room for the spawn point {p["label"]}')
    group = first_group + counters[p['kind']]
    counters[p['kind']] += 1
    spawns.append({'spawn_index': len(spawns), 'position': {'x': round(x), 'y': round(y), 'z': round(height_at(x, y))},
                   'radius': SPAWN_RADIUS, 'type_id': 3, 'index': encounter_index(slot, tier), 'attributes': 0,
                   'group': group})
    spawn_plan.append({'label': p['label'], 'slot': slot, 'tier': tier, 'group': group, 'position': [round(x), round(y)]})

# --- The party start and the arrivals (out4_build.json: the dungeons and the neighbours read them) -------------------
ARRIVALS = {
    'kreegan_road': (2880.0, -21800.0, 90.0), 'west_road': (-21800.0, 8640.0, 0.0),
    'd6_door': (-10300.0, 0.0, 180.0), 'd7_door': (10300.0, 0.0, 0.0), 'd16_door': (0.0, 10300.0, 90.0),
    'd6_hatch': (-17200.0, -2880.0, 0.0), 'd16_hatch': (-2880.0, 17200.0, 270.0), 'd7_hatch': (17200.0, 2880.0, 180.0),
    'spire_gate': (0.0, -ct.FORTRESS_HALF - kit.GATEHOUSE_DEPTH - 520.0, 270.0),   # before the enlarged gatehouse's steps
    'pad_lift': (2880.0, -13400.0, 270.0)}
arrivals = {}
for key, (x, y, degrees) in ARRIVALS.items():
    z = PLAZA_TOP if key == 'pad_lift' else height_at(x, y)
    arrivals[key] = {'position': [round(x), round(y), round(z)], 'direction_degrees': round(degrees)}
for key in ('kreegan_road', 'west_road'):
    assert abs(arrivals[key]['position'][2] - EDGE_Z) <= 32, arrivals[key]
# The arrivals other maps read (the dungeons' exits, the neighbours' edges) keep the heights they were built with
# (the relief of 2026-10-24 moved none of them): a change here means rebuilding D6, D7, D12, D13 and D16.
PINNED_ARRIVAL_Z = {'kreegan_road': 1216, 'west_road': 1216, 'd6_door': 1088, 'd7_door': 1088, 'd16_door': 1088,
                    'd6_hatch': 1120, 'd16_hatch': 1056, 'd7_hatch': 1056, 'spire_gate': 1088, 'pad_lift': 1160}
for key, z in PINNED_ARRIVAL_Z.items():
    assert arrivals[key]['position'][2] == z, (key, arrivals[key], z)
for index, entity in enumerate(entities):
    entity['entity_index'] = index + 1
start = arrivals['kreegan_road']
entities.insert(0, {'entity_index': 0, 'name': 'Party Start', 'decoration_list_id': 14, 'ai_attributes': 2,
                    'position': dict(zip('xyz', start['position'])),
                    'facing': round(start['direction_degrees'] / 360 * 2048) % 2048,     # the start reads yaw units
                    'event_id_primary': 0, 'event_id_secondary': 0, 'variable_primary': 0, 'variable_secondary': 0,
                    'special_trigger': 0, 'initial_decoration_flag': 2})

# The neighbours' arrivals (THE_CROWN.md BUILD-READY 6; the stage writes the edge travel rows from maps.yml).
EDGES = {'south': {'map': 'hes_out2.odm', 'arrival': [2880, 22406, 1200], 'facing': 270},
         'west': {'map': 'hes_out3.odm', 'arrival': [21800, 8640, 1200], 'facing': 180}}

# --- Events (THE_CROWN.md sections 13, 17 and 18; P4's texts: quests/dialogue/ASTER.md, CROWN.md, READABLES.md) ---
STAGED_MAPS = {m['file'] for m in yaml.safe_load((STAGE_DATA / 'maps.yml').read_text())['maps']}
NOT_OPEN = 'The way is not yet open.'


def dungeon_entry(project, map_file, arrival, refusal):
    """The Lua that moves the party to a Hesper dungeon's arrival (its semantic record), or `refusal` while the
    dungeon is not built and registered."""
    path = ROOT / 'level_generation/projects' / project / 'source' / (Path(map_file).stem + '.semantic.json')
    built = (ROOT / 'level_generation/projects' / project / 'runtime/worlds/hesper/maps' / map_file).exists()
    if not path.exists() or not built or map_file not in STAGED_MAPS:
        return f'evt.StatusText({json.dumps(refusal)})'
    a = json.loads(path.read_text())['arrivals'][arrival]
    x, y, z = a['position']
    direction = round(a['direction_degrees'] / 360 * 2048) % 2048
    return f'evt.MoveToMap({x}, {y}, {z}, {direction}, 0, 0, 0, 0, "{map_file}")'


def lua_string(text):
    return json.dumps(text)


NODE_MAPS = {'D6 West': ('hesper_d06', 'hes_d06.blv', 100010), 'D7 East': ('hesper_d07', 'hes_d07.blv', 100009),
             'D16 North': ('hesper_d16', 'hes_d16.blv', 100014)}
for name, (project, map_file, qbit) in NODE_MAPS.items():
    EVENTS[EV_DOORS[name]] = (f'Node {name.split()[1]} blast door', dungeon_entry(
        project, map_file, 'blast_door', 'The blast door\'s violet seal hums and does not open. ' + NOT_OPEN))
    EVENTS[EV_HATCH[name]] = (f'Node {name.split()[1]} service hatch', f'if IsQBitSet(QBit({qbit})) then '
                              + dungeon_entry(project, map_file, 'service_tunnel', NOT_OPEN)
                              + ' else evt.StatusText("Sealed from inside.") end')
EVENTS[EV_GATE] = ('The Spire Gate', 'if IsQBitSet(QBit(100603)) then '
                   + dungeon_entry('hesper_d12', 'hes_d12.blv', 'spire_gate', 'The Spire Gate stands open on darkness. '
                                   + NOT_OPEN)
                   + ' else evt.StatusText("The Spire Gate\'s seal burns violet. Nothing opens it while the Lattice '
                     'stands.") end')
EVENTS[EV_LIFT] = ('The pad lift', 'if not IsAtLeast(MapVar(3), 1) then SetValue(MapVar(3), 1) SetAutonote(10303) end '
                   'if IsQBitSet(QBit(100603)) then '
                   + dungeon_entry('hesper_d12', 'hes_d12.blv', 'pad_lift', 'The lift hums, but does not move. '
                                   + NOT_OPEN)
                   + ' else evt.StatusText("The lift is dead. Its call plate is dark.") end')

# Aster's relay posts (P4's relay_crown_*; ASTER.md block 4): dead until she is met (M3 done, 100003) and after Tear
# it out (100034). A node relay briefs its run until its node falls, then gives the count of hearts down; the plaza's
# changes once the cannons are dark. Each relay's first use adds the cannon rule (autonote 10301's words).
CANNON_RULE = ('Remember the great cannon: step into its reach and sight and a red beam locks on, three '
               'heartbeats, then it strikes. Break its sight behind a slab or a wall, or be inside before it ends.')
BRIEFINGS = {
    'West': (100010, "Node West is the cold node. Vapor vents in its coolant loop on a timer; count them. Its keeper "
                     "fights in a ring of rotating shields that stop shots both ways. Run straight for the door."),
    'North': (100014, "Node North is half-grown, still being grafted. It feeds the guns' eyes in orbit. Its master draws "
                      "the node's power into his shield from three columns. Short them and his shield fails, but he "
                      "grows faster in the dark."),
    'East': (100009, "Node East was my makers' defense works. The devils run it now. They build drones in its hall; stop "
                     "the line if you can. The guardian at its heart is a machine, coupled to the heart three times. "
                     "Cut the couplings before you fight it.")}
COUNT_LINES = ['One heart dark. The Hum is thinner already.', 'Two hearts dark. Your casters will feel the difference.',
               'All three. The cannons are dying. Listen: silence.']
DEAD_RELAY = 'evt.StatusText("A dead relay post; something hums inside.")'
NODES_DOWN = ('local down = 0 for _, q in ipairs({100009, 100010, 100014}) do if IsQBitSet(QBit(q)) then down = down + '
              '1 end end')
for k, (name, event) in enumerate(EV_RELAY.items()):
    first = 21 + k
    rule = (f'local rule = "" if not IsAtLeast(MapVar({first}), 1) then SetValue(MapVar({first}), 1) rule = " "'
            f' .. {lua_string(CANNON_RULE)} end')
    if name == 'Plaza':
        body = (f'{rule} if IsQBitSet(QBit(100603)) then evt.SimpleMessage("Aster, through the relay: \\"The cannons '
                'are dark. The gate is open, and the lift on this plaza goes down to the core. I will meet you '
                'inside.\\"") else evt.SimpleMessage("Aster, through the relay: \\"The Crown. See the great cannon on '
                'the dome? Stay out of its reach unless you are running to a node\'s door. A red beam '
                'means it has found you. Three breaths, then it fires. Break the beam behind a wall, or be inside '
                'before it ends.\\"") end')
    else:
        qbit, briefing = BRIEFINGS[name]
        counts = ' '.join(f'if down == {n + 1} then line = {lua_string(text)} end' for n, text in enumerate(COUNT_LINES))
        body = (f'{rule} {NODES_DOWN} if IsQBitSet(QBit({qbit})) then local line = "" {counts} '
                f'evt.SimpleMessage("Aster, through the relay: \\"" .. line .. "\\"" .. rule) else '
                f'evt.SimpleMessage("Aster, through the relay: \\"" .. {lua_string(briefing)} .. "\\"" .. rule) end')
    EVENTS[event] = (f'Aster relay post ({name})', 'if IsQBitSet(QBit(100034)) or not IsQBitSet(QBit(100003)) then '
                     + DEAD_RELAY + ' return end ' + body)

for k in range(len(TABLETS)):
    EVENTS[EV_TABLETS + k] = ('Colony log tablet', 'evt.StatusText("A crystal slab with faint blue lines.")')
PLATE_TEXTS = {'spine': 'A watch sigil: see, and call.', 'plinth': 'A trade sigil marks the sale of the Kept.',
               'roost': "A house sigil: the court's roosts.", 'yards': "A forge sigil: of their arms, our armor."}
for k, (_, _, label) in enumerate(PLATES):
    key = next(key for key in PLATE_TEXTS if key in label)
    text = f'evt.SimpleMessage({lua_string("A Kreegan glyph plate. " + PLATE_TEXTS[key])})'
    if key == 'plinth':                         # Aster's line at the market's plate (THE_CROWN.md section 18)
        text = ('if IsQBitSet(QBit(100003)) and not IsQBitSet(QBit(100034)) then evt.SimpleMessage('
                + lua_string('A Kreegan glyph plate. ' + PLATE_TEXTS[key] + ' Aster, quietly: "I am sorry."')
                + ') else ' + text + ' end')
    EVENTS[EV_PLATES + k] = ('Kreegan glyph plate', text)

for event, (index, label, strongbox) in chest_events.items():
    body = f'evt.OpenChest({index})'
    if strongbox:                               # locked: Hacking Master (LOOT_RULES, the Crown)
        body = ('if evt.CheckSkill(const.Skills.Hacking, const.SkillCheck.Master, 1) then ' + body
                + ' else evt.StatusText("The strongbox\'s lock is beyond you. (Hacking Master.)") end')
    EVENTS[event] = (label.split(':')[0].split(' (')[0], body)

PYLON_QBITS = {'West': 100604, 'North': 100605, 'East': 100606}
for name, event in EV_PYLON.items():
    qbit = PYLON_QBITS[name]
    EVENTS[event] = (f'Alarm pylon ({name})', f'if IsQBitSet(QBit({qbit})) then evt.StatusText("The pylon is dead.") '
                     'elseif evt.CheckSkill(const.Skills.Hacking, const.SkillCheck.Novice, 1) then '
                     f'SetQBit(QBit({qbit})) evt.SetSprite({event}, 1, "hes_alarm_pylon_off") '
                     'evt.StatusText("The pylon\'s eye gutters out.") else evt.StatusText("It is beyond you.") end')

# The Kept market freed (event 73; THE_CROWN.md section 7): QBit 100601, reputation -2 once (flag 100726, the
# engine's sign: negative is good), autonote 10302, the collars dark, the Kept and the Enforcers friendly and the
# Enforcers against the slaver and the Overseers, the stall shown with Anni and Tor. The relations are this map's own
# (evt.SetMonsterRelation): the Scour's camps keep their Kept hostile until their own collar nodes.
MARKET_FREED = (f'evt.SetMonsterRelation({LABOURER}, 0, 0) evt.SetMonsterRelation({ENFORCER}, 0, 0) '
                f'evt.SetMonsterRelation({ENFORCER}, {COURT_NOBLE}, 2) evt.SetMonsterRelation({ENFORCER}, '
                f'{COURT_OVERSEER}, 2) evt.SetMonsterRelation({COURT_NOBLE}, {ENFORCER}, 2) '
                f'evt.SetMonsterRelation({COURT_OVERSEER}, {ENFORCER}, 2) evt.SetTexture({COLLAR_COG}, "hkcollof") '
                f'evt.SetFacetBit({VESK_COG}, FacetBits.Invisible, false) '
                f'evt.SetFacetBit({VESK_COG}, FacetBits.Untouchable, false) '
                f'evt.SetMonGroupBit({GROUPS["freed"]}, MonsterBits.Invisible, false)')
EVENTS[EV_COLLAR] = ('The collar node', 'if IsQBitSet(QBit(100601)) then evt.StatusText("The collar node is dark.") '
                     'return end if evt.CheckSkill(const.Skills.Hacking, const.SkillCheck.Novice, 1) or '
                     f'evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUPS["slaver"]}, 0, false) then '
                     'SetQBit(QBit(100601)) if not IsQBitSet(QBit(100726)) then SetQBit(QBit(100726)) '
                     'AddValue(ReputationInCurrentLocation, -2) end SetAutonote(10302) ' + MARKET_FREED +
                     ' evt.SimpleMessage("The collars go dark, one after another, down the pens.") else '
                     'evt.StatusText("The node answers to its keeper. (Hacking, or the slaver dead.)") end')
EVENTS[EV_STALL_VESK] = ("Vesk's stall", f'if IsQBitSet(QBit(100601)) then evt.EnterHouse({VESK_HOUSE}) end')
EVENTS[EV_STALL_SORREL] = ("Sorrel's stall", f'if IsQBitSet(QBit(100007)) then evt.EnterHouse({SORREL_HOUSE}) end')

# The lander (M16, event 58, and event 5's 15 s): ENDING's boarding lines at its first second, the boarding at 15.
ENDING = ('The ramp seals behind you. The Pilot does not wait for anyone to sit down. Below, the Crown\'s dome splits '
          'like an egg. Light comes up out of the ground, first red, then white. The Pilot: \\"Hold on to something.\\" '
          'From the ring the whole world is visible, and then Hesper\'s crust lifts, cracks and goes out '
          'like a lamp. The Seedship goes with it, and the spires, and the pits, and the Crown.')
BOARD = ('if IsQBitSet(QBit(100016)) or not IsQBitSet(QBit(100607)) then return end SetQBit(QBit(100016)) '
         'ClearQBit(QBit(100216)) local last = "The Pilot: \\"That\'s it. That\'s all of it. ... The star map came up '
         'with the splinter\'s codes. Three more brood worlds. Bare coordinates.\\"" if not IsQBitSet(QBit(100034)) '
         'then last = "Aster, from the lander\'s console: \\"Hesper is gone. So is everything that was born to eat '
         "your world. I have the star map, travelers. There are three more.\\\"\" end "
         f'evt.SimpleMessage("{ENDING} " .. last .. " The Pilot: \\"Setting course for home.\\"")')
EVENTS[EV_LANDER] = ('The lander', BOARD)

# The ion cannons (THE_CROWN.md section 7, until ENGINE item 7): a map timer every half second (15 game seconds)
# locks each cannon on a party in its reach (9 000; 13 500 flying) and in its sight (a ray from the cannon's pivot to
# the party, against the cover's boxes and the towers' cylinders), for 3 s, then strikes 1 500 Energy at every
# character; a new lock 6 s after a strike. Half a second out of sight or reach breaks it. The test emplacement does
# the same at 2 500 with a 15D10 strike while its actor stands.
boxes, cylinders = [], []
for kind, (cx, cy), length, angle in COVER:
    a = math.radians(angle)
    z = height_at(cx, cy)
    if kind == 'slab':
        lean = 700 * math.tan(math.radians(10.0)) / 2
        boxes.append((cx - math.sin(a) * lean, cy + math.cos(a) * lean, math.cos(a), math.sin(a), length / 2, 130,
                      z - 40, z + 700))
    else:
        boxes.append((cx, cy, math.cos(a), math.sin(a), 450, 225, z - 40, z + 400))
for name, (door, (ox, oy)) in NODES.items():
    bx, by = door[0] - ox * ct.NODE_BUNKER_BACK, door[1] - oy * ct.NODE_BUNKER_BACK
    cylinders.append((bx, by, ct.NODE_BUNKER_R, FLOOR_Z - 40, FLOOR_Z + 420))
    boxes.append((door[0] - ox * 210, door[1] - oy * 210, ox, oy, 210, 300, FLOOR_Z - 40, FLOOR_Z + 420))
    length = math.hypot(bx, by) - ct.NODE_BUNKER_R - ct.FORTRESS_HALF
    mid = (math.hypot(bx, by) - ct.NODE_BUNKER_R + ct.FORTRESS_HALF) / 2
    boxes.append((ox * mid, oy * mid, ox, oy, length / 2, 150, FLOOR_Z - 40, FLOOR_Z + 180))
boxes.append((0.0, 0.0, 1.0, 0.0, ct.FORTRESS_HALF, ct.FORTRESS_HALF, FLOOR_Z - 40, FLOOR_Z + kit.WALL_H))   # walls
(wx0, wy0), (wx1, wy1) = TEST_WALL
wall_len = math.hypot(wx1 - wx0, wy1 - wy0)
boxes.append(((wx0 + wx1) / 2, (wy0 + wy1) / 2, (wx1 - wx0) / wall_len, (wy1 - wy0) / wall_len, wall_len / 2, 75,
              height_at(wx0, wy0) - 40, height_at(wx0, wy0) + 600))
for cx, cy in BASTIONS.values():
    cylinders.append((cx, cy, ct.BASTION_R, FLOOR_Z - 40, FLOOR_Z + BASTION_H))
# The great cannon fires down from its pivot over the dome (the dome itself never stands in its way).
cannon_rows = [f'{{x = {cx:.0f}, y = {cy:.0f}, z = {CANNON_PIVOT:.0f}, range = {ct.RANGE_GROUND}, '
               f'fly = {ct.RANGE_FLYING}, name = "the great cannon", own = 0, damage = 1500, cog = {CANNON_COGS[name]}, '
               f'mx = {cx + MUZZLE_SIDE:.0f}, my = {cy - MUZZLE_FORWARD:.0f}, mz = {CANNON_BASE + MUZZLE_UP:.0f}}}'
               for name, (cx, cy) in CANNONS.items()]                 # it faces south: the muzzle is south of it
cannon_rows.append(f'{{x = {TEST_CANNON[0]:.0f}, y = {TEST_CANNON[1]:.0f}, z = {TEST_TOP + 120:.0f}, range = 2500, '
                   f'fly = 2500, name = "the test emplacement", own = 0, damage = 0, cog = 0, test = true}}')
GREAT_CANNON_STATES = ['hes_great_cannon', 'hes_great_cannon_dark'] + [f'hes_great_cannon_c{k}' for k in range(1, 6)]
GREAT_CANNON_SHOW = '\n'.join(
    f'    {"if" if k == 0 else "elseif"} model == "{state}" then evt.SetSprite({cog}, 1, "{state}")'
    for k, state in enumerate(GREAT_CANNON_STATES) for cog in CANNON_COGS.values()) + '\n    end'
# The alarm's watchers (COMBAT "Alarm pylons"): the hostile actors placed within 6 000 of a pylon, the cannons apart.
WATCHERS = [a['actor_index'] for a in actors if a['hostility_type'] > 0 and a['monster_id'] != 10059
            and any(math.hypot(a['position']['x'] - wx, a['position']['y'] - wy) < 6000 for wx, wy in PYLONS.values())]
CANNON_LUA = f'''
-- The ion cannons' lock-on (build_out4.py, THE_CROWN.md section 7): every half second.
local CANNONS = {{{', '.join(cannon_rows)}}}
local BOXES = {{{', '.join('{' + ', '.join(f'{v:.3f}' if isinstance(v, float) and abs(v) < 2 else f'{v:.0f}'
                                                for v in b) + '}' for b in boxes)}}}
local CYLINDERS = {{{', '.join('{' + ', '.join(f'{v:.0f}' for v in c) + '}' for c in cylinders)}}}
local lock = {{0, 0, 0, 0, 0}}
-- The ground (the relief of 2026-10-24: terraces, basins and knolls break the line of sight too): the map's 128 x 128
-- height bytes, north row first, x 32; a ray point below the native triangle under it is blocked.
local GROUND_HEX = "{height_bytes.tobytes().hex()}"
local GROUND = {{}}
for i = 1, #GROUND_HEX, 2 do GROUND[#GROUND + 1] = tonumber(GROUND_HEX:sub(i, i + 1), 16) * 32 end
local function ground_at(x, y)
    local fx, fy = (x + 32768) / 512, (32768 - y) / 512
    local ix, iy = math.max(0, math.min(126, math.floor(fx))), math.max(0, math.min(126, math.floor(fy)))
    local tx, ty = fx - ix, fy - iy
    local function h(gx, gy) return GROUND[gy * 128 + gx + 1] end
    if tx + ty <= 1 then
        return h(ix, iy) + (h(ix + 1, iy) - h(ix, iy)) * tx + (h(ix, iy + 1) - h(ix, iy)) * ty
    end
    return h(ix + 1, iy + 1) + (h(ix, iy + 1) - h(ix + 1, iy + 1)) * (1 - tx) + (h(ix + 1, iy) - h(ix + 1, iy + 1)) * (1 - ty)
end
-- The lock's length (3 s; 5 s while a character wears the Jammer, unless the alarm is up) and the last charge stage each
-- cannon played.
local LOCK_SECONDS = 3
local JAMMER = 11470
-- The alarm (COMBAT "Alarm pylons"): while a pylon stands, a hostile watcher that sees the party for 3 s raises it, and
-- the cannons ignore the Jammer for 20 s (counted in half seconds; runtime state, not saved).
local WATCHERS = {{{', '.join(str(i) for i in WATCHERS)}}}
local PYLON_QBITS = {{{', '.join(str(q) for q in PYLON_QBITS.values())}}}
local seen_half_seconds, alarm_half_seconds = 0, 0
local function jammed()
    for player = 0, evt.GetPartyMemberCount() - 1 do
        if evt.PartyMemberHasEquippedItem(player, JAMMER) then return true end
    end
    return false
end
local function watch_alarm()
    alarm_half_seconds = math.max(0, alarm_half_seconds - 1)
    local standing = false
    for _, qbit in ipairs(PYLON_QBITS) do
        if not IsQBitSet(QBit(qbit)) then standing = true end
    end
    local seen = false
    if standing and not IsQBitSet(QBit(100603)) then
        for _, index in ipairs(WATCHERS) do
            if evt.ActorSeesParty(index, 4000) then seen = true break end
        end
    end
    seen_half_seconds = seen and seen_half_seconds + 1 or 0
    if seen_half_seconds >= 6 and alarm_half_seconds == 0 then
        alarm_half_seconds = 40
        evt.StatusText("An alarm pylon shrieks! The cannons' lock quickens.")
        evt.PlaySoundName("turret_windup")
    end
end
local charge = {{0, 0, 0, 0, 0}}

local function blocked(cannon, px, py, pz)
    local dx, dy, dz = px - cannon.x, py - cannon.y, pz - cannon.z
    local steps = math.floor(math.sqrt(dx * dx + dy * dy + dz * dz) / 48)
    for i = 2, steps - 1 do
        local t = i / steps
        local x, y, z = cannon.x + dx * t, cannon.y + dy * t, cannon.z + dz * t
        if z < ground_at(x, y) - 16 then
            return true
        end
        for _, b in ipairs(BOXES) do
            local rx, ry = x - b[1], y - b[2]
            if z >= b[7] and z <= b[8] and math.abs(rx * b[3] + ry * b[4]) <= b[5]
                and math.abs(-rx * b[4] + ry * b[3]) <= b[6] then
                return true
            end
        end
        for k, c in ipairs(CYLINDERS) do
            local rx, ry = x - c[1], y - c[2]
            if k ~= cannon.own and z >= c[4] and z <= c[5] and rx * rx + ry * ry <= c[3] * c[3] then
                return true
            end
        end
    end
    return false
end

-- The great cannon's wind-up (COMBAT, "The look and the shot"): its decoration's state models, swapped by the lock's
-- half seconds: the breech core, the pods, the first rings, all five rings, the muzzle crown flaring; dark on release
-- until the recharge ends.
local WIND_UP = {{[0.5] = "hes_great_cannon_c1", [1.0] = "hes_great_cannon_c2", [1.5] = "hes_great_cannon_c3",
                 [2.0] = "hes_great_cannon_c4", [2.5] = "hes_great_cannon_c5"}}

-- The charge sound (the user, 2026-10-23): five 0.6 s stages, cannon_charge_1..5 (audio/make_cannon_charge.py),
-- rising through the wind-up into the shot. A tick plays the stage of the lock's progress before its step (3 s:
-- stages 1-5 at 0, 0.5 .. 2 s; the tick at 2.5 s fires), at most one a tick and never one twice; a broken lock plays
-- nothing more and its stage dies out.
local function charge_sound(k)
    local stage = math.min(5, math.floor(lock[k] * 5 / (LOCK_SECONDS - 0.5)) + 1)
    if stage > charge[k] then
        charge[k] = stage
        evt.PlaySoundName("cannon_charge_" .. stage)
    end
end

-- Literal swaps (the lighting bake reads every evt.SetSprite with a literal index and name).
local function show(cannon, model)
    if cannon.cog == 0 then return end
{GREAT_CANNON_SHOW}
end

-- The great cannon's head turns about its pivot from its rest facing (south, 270): evt.AimDecoration turns it toward
-- the locked party at 120 degrees a second; the muzzle (and the lock beam's start) is where the turned head puts it.
local function muzzle(cannon)
    local a = math.rad(evt.DecorationAim(cannon.cog))
    local dx, dy = cannon.mx - cannon.x, cannon.my - cannon.y
    return cannon.x + dx * math.cos(a) - dy * math.sin(a), cannon.y + dx * math.sin(a) + dy * math.cos(a), cannon.mz
end

local function track(k, cannon, px, py, pz)
    if cannon.cog == 0 then return end
    evt.AimDecoration(cannon.cog, math.deg(math.atan(py - cannon.y, px - cannon.x)) - 270, 120)
    local mx, my, mz = muzzle(cannon)
    evt.BeamToParty("crown_lock" .. k, "hesper:fx/beam/crown_lock", mx, my, mz)
end

local function strike(cannon, px, py, pz)
    local damage = cannon.damage
    if cannon.test then
        damage = 0
        for _ = 1, 15 do damage = damage + evt.RandomBetween(1, 10) end
        evt.SpawnWorldEffect("hesper:fx/impact/hes_heavy_bolt", px, py, pz + 100, 1.5)
        evt.PlaySoundName("hes_heavy_fire")
        evt.StatusText("The cannon fires!")
    else
        -- The release: the muzzle flash, the ion pulse (the CrownIon missile, 0.15 s to the party; its ion-plasma
        -- blast there gives every actor within 600 the strike's Energy), the head's recoil, every zone dark at once.
        local mx, my, mz = muzzle(cannon)
        evt.SpawnWorldEffect("hesper:fx/impact/crown_muzzle", mx, my, mz, 1.0)
        evt.FireMissile("CrownIon", mx, my, mz, px, py, pz + 60, damage, "Energy", 600, 0.15)
        evt.RecoilDecoration(cannon.cog, 350, 1.2)
        evt.PlaySoundName("cannon_pulse")
        evt.PlaySoundName("cannon_blast", px, py, pz)
        evt.StatusText("The great cannon fires!")
        show(cannon, "hes_great_cannon_dark")
    end
    evt.DamagePlayer(5, 12, damage)
end

RegisterMapTimerEvent({EV_CANNONS}, 15, function()
    local px, py, pz = evt.GetPartyPosition()
    watch_alarm()
    LOCK_SECONDS = (alarm_half_seconds == 0 and jammed()) and 5 or 3
    -- isFlying, not IsFlying: event_support exports VarTag.IsFlying (a number) over the IsFlying function.
    local flying = isFlying()
    for k, cannon in ipairs(CANNONS) do
        local active
        if cannon.test then
            active = not evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUPS["test"]}, 0, false)
        else
            active = not IsQBitSet(QBit(100603))
        end
        local reach = flying and cannon.fly or cannon.range
        local dx, dy = px - cannon.x, py - cannon.y
        local seen = active and dx * dx + dy * dy <= reach * reach and not blocked(cannon, px, py, pz + 150)
        if seen and lock[k] >= 0 then
            if lock[k] == 0 then
                charge[k] = 0
                evt.StatusText("A red beam from " .. cannon.name .. " locks onto you!")
            end
            if cannon.test then evt.SpawnWorldEffect("hesper:fx/impact/kr_dart", px, py, pz, 1.0) end
            -- Not on the firing tick: the beam asked for again there would outlive its StopBeam.
            if lock[k] + 0.5 < LOCK_SECONDS then track(k, cannon, px, py, pz) end
            if lock[k] + 0.5 < LOCK_SECONDS then charge_sound(k) end
            lock[k] = lock[k] + 0.5
            if WIND_UP[lock[k]] then show(cannon, WIND_UP[lock[k]]) end
            if lock[k] >= LOCK_SECONDS then
                evt.StopBeam("crown_lock" .. k)
                strike(cannon, px, py, pz)
                lock[k] = -6
            end
        elseif lock[k] > 0 then
            lock[k] = 0
            evt.StopBeam("crown_lock" .. k)
            show(cannon, "hes_great_cannon")
            evt.StatusText("The beam slides off you.")
        elseif lock[k] < 0 then
            lock[k] = math.min(0, lock[k] + 0.5)
            if lock[k] == 0 and active then show(cannon, "hes_great_cannon") end
        end
        -- A dead cannon sinks back to its rest facing.
        if not active and cannon.cog ~= 0 then evt.AimDecoration(cannon.cog, 0, 20) end
    end
end, "The ion cannons", "", 15)
'''

# The Blooding Ring (HARROWERS.md): the gate's glyph plate (event 21); when the party is inside the ring (event 150,
# every half second, once per visit by the named var `ring_seen`, cleared on load), the first time his roar and voiced
# line as one clip, `vo_vreth_sight` (non-positional, design/kreegan_world/audio/BOSS_LINES.md), and autonote 10304
# (MapVar 5: once per save), on later visits the bare roar at the dais; his death (event 151): QBit 100609 (the load
# event then hides him).
EVENTS[EV_RING_PLATE] = ('Kreegan glyph plate', 'evt.SimpleMessage("A Kreegan glyph plate. A hunt sigil: here the '
                         'hunters are blooded.")')
RING_LUA = (f'RegisterMapTimerEvent({EV_RING}, 15, function() if IsQBitSet(QBit(100609)) or '
            'evt.GetMapVar("ring_seen", 0) == 1 then return end local px, py = evt.GetPartyPosition() '
            f'if (px - {RING[0]:.0f}) ^ 2 + (py - {RING[1]:.0f}) ^ 2 > {RING_R - 100:.0f} ^ 2 then return end '
            'evt.SetMapVar("ring_seen", 1) if not IsAtLeast(MapVar(5), 1) then SetValue(MapVar(5), 1) SetAutonote(10304) '
            'evt.StatusText("Huntmaster Vreth: Prey, in my ring. Stand still; it is quicker.") '
            'evt.PlaySoundName("vo_vreth_sight") '
            f'else evt.PlaySoundName("vreth_roar", {RING[0]:.0f}, {RING[1]:.0f}, {RING_DAIS_TOP + 150:.0f}) '
            'end end, "The Blooding Ring", "", 15)\n'
            f'RegisterMonsterKilledHook({EV_VRETH}, "Huntmaster Vreth", function() if IsQBitSet(QBit(100609)) or not '
            f'evt.CheckMonstersKilled(ActorKillCheck.Group, {GROUPS["vreth"]}, 0, false) then return end '
            'SetQBit(QBit(100609)) end)\n')

# The Kept market's noise (event 6, every 5 s while the market is collared and the party within 6 000 of the plinth):
# the crowd, the chains and the auctioneer at the plinth (until the engine's ambience loop; AUDIO.md, Zone 4).
MARKET_LUA = (f'RegisterMapTimerEvent({EV_MARKET_NOISE}, 150, function() if IsQBitSet(QBit(100601)) then return end '
              'local px, py = evt.GetPartyPosition() '
              f'if (px - {PLINTH[0]:.0f}) ^ 2 + (py - {PLINTH[1]:.0f}) ^ 2 > 6000 ^ 2 then return end '
              f'evt.PlaySoundName("market_crowd", {PLINTH[0]:.0f}, {PLINTH[1]:.0f}, {height_at(*PLINTH) + 200:.0f}) end, '
              '"The market\'s noise", "", 150)\n')

# The air raid (event 4, every 2 s; THE_CROWN.md section 7): a flying party scrambles the three hidden flights once.
RAID_LUA = (f'RegisterMapTimerEvent({EV_RAID}, 60, function() if IsAtLeast(MapVar(1), 1) or not isFlying() then '
            'return end SetValue(MapVar(1), 1) '
            + ' '.join(f'evt.SetMonGroupBit({GROUPS[g]}, MonsterBits.Invisible, false)'
                       for g in ('raid_ne', 'raid_n', 'raid_w'))
            + ' evt.StatusText("Overseer flights scramble from the roosts!") end, "The air raid", "", 60)\n')
# The lander's 15 s (event 5, every second while 100607 is set and 100016 clear).
LANDER_LUA = (f'RegisterMapTimerEvent({EV_LANDER_TIMER}, 30, function() if IsQBitSet(QBit(100016)) or not '
              'IsQBitSet(QBit(100607)) then return end local t = evt.GetMapVar("lander_seconds", 0) + 1 '
              'evt.SetMapVar("lander_seconds", t) if t == 1 then evt.StatusText("The lander\'s ramp is down, its engines '
              'already screaming.") if not IsQBitSet(QBit(100034)) then evt.SimpleMessage("Aster, from the lander\'s '
              'console: \\"I am here. Go.\\"\\n\\nThe Pilot, over the speakers: \\"Up the ramp! Now!\\"") else '
              'evt.SimpleMessage("The Pilot, over the speakers: \\"Up the ramp! Now!\\"") end elseif t >= 15 then '
              f'{BOARD} end end, "The lander waits", "", 30)\n')

# Load (event 1) and the first visit (event 2).
LOAD = [f'if (IsQBitSet(QBit(100009)) and IsQBitSet(QBit(100010)) and IsQBitSet(QBit(100014))) or '
        'IsQBitSet(QBit(100602)) then SetQBit(QBit(100603)) end',
        'if IsQBitSet(QBit(100603)) then '
        + ' '.join(f'evt.SetSprite({cog}, 1, "hes_great_cannon_dark")' for cog in CANNON_COGS.values()) + ' '
        + ' '.join(f'evt.SetSprite({cog}, 1, "hes_node_mast_off")' for cog in MAST_COGS.values())
        + f' evt.SetTexture({kit.GATE_COG}, "hogateof") end']
LOAD += [f'if IsQBitSet(QBit({PYLON_QBITS[name]})) then evt.SetSprite({event}, 1, "hes_alarm_pylon_off") end'
         for name, event in EV_PYLON.items()]
LOAD.append('if IsQBitSet(QBit(100601)) then ' + MARKET_FREED + ' '
            + ' '.join(f'evt.SetMonGroupBit({GROUPS[g]}, MonsterBits.Invisible, true)'
                       for g in ('labourers', 'enforcers')) + ' end')
LOAD.append(f'if IsQBitSet(QBit(100007)) then evt.SetFacetBit({SORREL_COG}, FacetBits.Invisible, false) '
            f'evt.SetFacetBit({SORREL_COG}, FacetBits.Untouchable, false) end')
LOAD.append(f'evt.SetMapVar("ring_seen", 0) if IsQBitSet(QBit(100609)) then evt.SetMonGroupBit({GROUPS["vreth"]}, '
            f'MonsterBits.Invisible, true) else evt.SetMonsterItem({VRETH_INDEX}, 11227) end')
LOAD.append(f'if IsQBitSet(QBit(100607)) and not IsQBitSet(QBit(100016)) then evt.SetSprite({LANDER_COG}, 1) '
            f'evt.SetFacetBit({LANDER_COG}, FacetBits.Untouchable, false) else evt.SetSprite({LANDER_COG}, 0) end')
EVENTS[EV_LOAD] = ('The Crown on load', ' '.join(LOAD))
EVENTS[EV_FIRST] = ('The first visit', 'if IsAtLeast(MapVar(2), 1) then return end SetValue(MapVar(2), 1) '
                    'SetAutonote(10301) evt.StatusText("The Crown. A great cannon stands on the citadel\'s dome.")')

LUA = '-- Generated by level_generation/projects/hesper_out4/build_out4.py.\n'
LUA += f'SetMapMetadata({{onLoad = {{{EV_LOAD}, {EV_FIRST}}}, onLeave = {{}}, openedChestIds = {{'
LUA += ', '.join(f'[{event}] = {{{index}}}' for event, (index, _, _) in sorted(chest_events.items())) + '}})\n'
for event in sorted(EVENTS):
    title, body = EVENTS[event]
    LUA += f'RegisterEvent({event}, {json.dumps(title)}, function() {body} end, {json.dumps(title)})\n'
LUA += CANNON_LUA + RAID_LUA + LANDER_LUA + RING_LUA + MARKET_LUA

# --- Write the sources, build with the editor, verify -----------------------------------------------------------------
if SOURCE.exists():
    shutil.rmtree(SOURCE)
(SOURCE / 'models').mkdir(parents=True)
bmodel_records = []
interactive = []
for index, model in enumerate(models):
    write_obj(model, SOURCE / 'models' / f'{model.name}.obj', SIZES)
    textures = sorted({texture for _, texture, _ in model.faces})
    bmodel_records.append({'geometry_id': f'hes_out4:{model.name}', 'runtime_bmodel_index': index,
                           'source': {'asset_path': str(SOURCE / 'models' / f'{model.name}.obj'), 'scale': 128,
                                      'merge_coplanar_faces': False, 'preserve_source_winding': True},
                           'materials': {'default_texture': textures[0], 'remaps': {t: t for t in textures}}})
    # A model in COGS carries its cog on every face (evt.SetFacetBit shows and hides it), a HIDDEN_MODELS one starts
    # Invisible and Untouchable; a face in face_cogs carries its own cog (evt.SetTexture swaps it).
    cog = COGS.get(model.name, 0)
    hidden = 0x20002000 if model.name in HIDDEN_MODELS else 0
    face_events = {face: event for event, faces in model.events.items() for face in faces if event}
    own_cogs = {face: c for (name, face), c in face_cogs.items() if name == model.name}
    for face in sorted(set(face_events) | set(own_cogs) | (set(range(len(model.faces))) if cog else set())):
        event = face_events.get(face, 0)
        interactive.append({'bmodel_index': index, 'face_index': face,
                            'legacy_attributes': (0x2000000 if event else 0) | hidden
                            | (0x2000 if face in model.invisible else 0),
                            'cog_number': own_cogs.get(face, cog), 'cog_triggered_number': event, 'cog_trigger': 0})
    for face in model.invisible:                        # FaceAttribute::Invisible: blocks, not drawn
        if cog or face in face_events:
            continue
        interactive.append({'bmodel_index': index, 'face_index': face, 'legacy_attributes': 0x2000,
                            'cog_number': 0, 'cog_triggered_number': 0, 'cog_trigger': 0})
(SOURCE / 'hes_out4.geometry.yml').write_text(json.dumps({'version': 1, 'map_file': MAP, 'bmodels': bmodel_records},
                                                         indent=1) + '\n')
(SOURCE / 'hes_out4.terrain.yml').write_text(json.dumps({
    'version': 1, 'map_file': MAP, 'height_map_hex': height_bytes.tobytes().hex().upper(),
    'tile_map_hex': tile_bytes.tobytes().hex().upper(),
    'attribute_map_hex': bytes(GRID * GRID).hex().upper()}) + '\n')
reference = yaml.safe_load((ROOT / 'assets_dev/worlds/mm8/maps/out02.scene.yml').read_text())
environment = reference['environment']
environment['tile_set_lookup_indices'] = LOOKUPS
scene = {'format_version': 1, 'kind': 'outdoor_scene', 'source': {'geometry_file': MAP},
         'environment': environment, 'terrain': {'attribute_overrides': [], 'footstep_sound_overrides': []},
         'bmodel_faces': {'interactive_faces': interactive}, 'entities': entities, 'spawns': spawns,
         'initial_state': {'location': {'respawn_count': 0, 'last_respawn_day': 0, 'reputation': 0,
                                        'alert_status': 0},
                           'face_attribute_overrides': [], 'actors': actors, 'sprite_objects': ground_items,
                           'chests': [], 'variables': {'map': [0] * 75, 'decor': [0] * 125}},
         'loot_containers': loot, 'world_items': []}
(SOURCE / 'hes_out4.scene.yml').write_text(json.dumps(scene, indent=1) + '\n')
package = {'format_version': 1, 'kind': 'outdoor_map_package', 'package_id': 'hesper:the_crown',
           'display_name': 'The Crown', 'map_file': MAP, 'scene_file': 'hes_out4.scene.yml',
           'geometry_metadata_file': 'hes_out4.geometry.yml', 'terrain_metadata_file': 'hes_out4.terrain.yml',
           'script_module': 'maps/hes_out4.lua', 'map_stats_id': 9130, 'redbook_track': 0,
           'environment_name': 'grassland', 'is_top_level_area': True,
           'outdoor_bounds': {'enabled': True, 'min_x': -BOUND, 'max_x': BOUND, 'min_y': -BOUND, 'max_y': BOUND}}
(SOURCE / 'hes_out4.map.yml').write_text(json.dumps(package, indent=1) + '\n')

if TREE.exists():
    shutil.rmtree(TREE)
for folder in ['maps', 'events/maps', 'terrain_materials', 'terrain_decorations', 'effects', 'behaviors/bosses']:
    (TREE / folder).mkdir(parents=True, exist_ok=True)
shutil.copy2(PROJECT / 'huntmaster.lua', TREE / 'behaviors/bosses/huntmaster.lua')     # behaviors.yml names it
import crown_effects  # noqa: E402
crown_effects.write(TREE / 'effects/hes_out4.yml')                # the great cannon's effects (event 3)
with tempfile.TemporaryDirectory(prefix='hes-out4-') as directory:
    temp = Path(directory)
    for name in ['hes_out4.map.yml', 'hes_out4.scene.yml', 'hes_out4.geometry.yml', 'hes_out4.terrain.yml']:
        shutil.copy2(SOURCE / name, temp / name)
    log = PROJECT / 'build.log'
    with log.open('w') as stream:
        subprocess.run([str(ROOT / 'build/editor/openyamm-editor'), '--asset-root', str(STAGE), '--headless-build-map',
                        str(temp / 'hes_out4.map.yml')], check=True, stdout=stream, stderr=subprocess.STDOUT)
    shutil.copy2(temp / MAP, TREE / 'maps' / MAP)
shutil.copy2(SOURCE / 'hes_out4.scene.yml', TREE / 'maps/hes_out4.scene.yml')

sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file  # noqa: E402
native = parse_odm_file(TREE / 'maps' / MAP)['payload']
assert bytes(native['height_map']) == height_bytes.tobytes()
assert bytes(native['tile_map']) == tile_bytes.tobytes()
assert len(native['bmodels']) == len(models)
assert len(native['entities']) == len(entities)
for face in interactive:
    model = native['bmodels'][face['bmodel_index']]
    assert model['faces'][face['face_index']]['cog_triggered_number'] == face['cog_triggered_number'], face
    assert model['faces'][face['face_index']]['cog_number'] == face['cog_number'], face

# Where a scenario stands to click a face: 240 out from the face's centre along its normal, facing it.
door_poses = {}
for model in models:
    for event, faces in model.events.items():
        points = np.array(model.faces[faces[0]][0])
        centre = points.mean(0)
        n = normal([tuple(p) for p in points])
        px, py = centre[0] + n[0] * 240, centre[1] + n[1] * 240
        on_plaza = math.hypot(px - PLAZA[0], py - PLAZA[1]) < PLAZA_R
        door_poses[event] = [round(px), round(py), round(PLAZA_TOP if on_plaza else height_at(px, py)),
                             round(math.atan2(-n[1], -n[0]), 4)]
(TREE / 'events/maps/hes_out4.lua').write_text(LUA)

# Ground materials: the slot file (tints from the design's targets over the library materials' mean colours) and the
# weights.
library = yaml.safe_load((ROOT / 'assets_dev/engine/terrain_materials/library.yml').read_text())['materials']
library.update(yaml.safe_load((STAGE_DATA / 'terrain_library.yml').read_text())['materials'])
slot = yaml.safe_load((DESIGN / 'terrain_materials.yml').read_text())
# The slope layer: the design's rock_cliff is a red-brown scan that reads salmon under the Crown's violet light; the
# neutral grey rock_ground scan (CC0, Poly Haven rock_ground_02) takes the same black target.
slot['layers'][-1]['library'] = 'rock_ground'
# The old pavement a weathered grey-white (the integrator's sheet review: the swatch's bright cream against the
# near-black killing ground read blotchy from the air).
next(layer for layer in slot['layers'] if layer['name'] == 'plating')['target'] = [150, 144, 134]
slot['layers'] = [{'name': layer['name'], 'library': layer['library'],
                   'tint': [round(t / 255.0 / m, 4) for t, m in zip(layer['target'],
                                                                   library[layer['library']]['mean_color'])],
                   **{k: v for k, v in layer.items() if k not in ('name', 'library', 'target')}}
                  for layer in slot['layers']]
# The rim's black glass: obsidian's mean colour is so dark that target / mean gives (2.3, 1.2, 1.6), which turns the
# scan's bright facets pink; its tint is the target's brightness ratio with a mild violet instead.
next(layer for layer in slot['layers'] if layer['name'] == 'glass')['tint'] = [1.3, 1.15, 1.45]
slot['weights'] = ['hes_out4_weights0.png', 'hes_out4_weights1.png']
slot['weighted_layers'] = len(LAYERS)
slot['slope'] = {'layer': len(LAYERS), 'start': slot['slope']['start'], 'end': slot['slope']['end']}
assert [layer['name'] for layer in slot['layers']] == LAYERS + ['rock']
(TREE / 'terrain_materials/hes_out4.yml').write_text(
    '# Generated by level_generation/projects/hesper_out4/build_out4.py from design/kreegan_world/zone4/'
    "terrain_materials.yml (tint = target / the library material's mean color).\n# weights: RGBA images covering "
    'the 128x128 cell map, channels in layer order (north row first).\n' + yaml.safe_dump(slot, sort_keys=False))
for index in range(2):
    Image.fromarray(quantized[..., index * 4:index * 4 + 4], 'RGBA').save(
        TREE / f'terrain_materials/hes_out4_weights{index}.png', optimize=True)
# No ground plants on the Crown (K13): the map's plant file is off.
(TREE / 'terrain_decorations/hes_out4.yml').write_text(
    '# The Crown grows nothing (THE_CROWN.md section 8, K13). Generated by build_out4.py.\nversion: 2\nenabled: false\n'
    'rules: []\n')

# The ground's colour as it reads in the game, for the minimap (each layer's tinted library colour by the weights,
# the rock on steep slopes) and the models the minimap draws.
colour = np.zeros((TEXEL_GRID, TEXEL_GRID, 3), dtype=np.float32)
for index, layer in enumerate(slot['layers'][:len(LAYERS)]):
    rgb = np.array(library[layer['library']]['mean_color']) * np.array(layer['tint'])
    colour += field[..., index:index + 1] * (rgb ** 2.2)[None, None, :]
texel_heights = ndimage.gaussian_filter(ndimage.zoom(heights, TEXEL_GRID / GRID, order=3), 6)
gy_, gx_ = np.gradient(texel_heights, units)
slope = np.hypot(gx_, gy_)
cliff = np.clip((slope - slot['slope']['start']) / (slot['slope']['end'] - slot['slope']['start']), 0, 1)[..., None]
rock = np.array(library[slot['layers'][-1]['library']]['mean_color']) * np.array(slot['layers'][-1]['tint'])
colour = colour * (1 - cliff) + (rock ** 2.2)[None, None, :] * cliff
(PROJECT / 'work').mkdir(exist_ok=True)
Image.fromarray(np.clip(colour ** (1 / 2.2) * 255 + 0.5, 0, 255).astype(np.uint8), 'RGB').save(
    PROJECT / 'work/ground_colour.png')
DECORATIONS = ROOT / 'level_generation/props/hesper_decorations'
for placement in model_placements:
    placement['model'] = str(DECORATIONS / 'work/hard_surface' / f'{placement["name"]}.glb')
    placement['scale'] = 100.0
(PROJECT / 'work/minimap_models.json').write_text(json.dumps(model_placements, indent=1) + '\n')

# Previews for review.
review = PROJECT / 'review'
review.mkdir(exist_ok=True)
low, high = heights.min(), heights.max()
Image.fromarray(((heights - low) / (high - low) * 255).astype(np.uint8), 'L').resize((512, 512)).save(
    review / 'heights.png')
colours = np.array([[84, 78, 92], [62, 58, 66], [44, 40, 44], [198, 190, 172], [70, 50, 110], [60, 30, 64],
                    [36, 32, 46], [0, 0, 0]], dtype=np.float32)
Image.fromarray(np.clip(field[::4, ::4] @ colours, 0, 255).astype(np.uint8), 'RGB').save(review / 'weights.png')
report = {'map': MAP, 'map_id': 9130, 'bmodels': len(models), 'faces': sum(len(m.faces) for m in models),
          'entities': len(entities), 'actors': len(actors), 'spawns': len(spawns), 'chests': len(loot),
          'ground_items': len(ground_items), 'events': sorted(EVENTS),
          'height_range': [int(heights.min()), int(heights.max())], 'edge_rows': EDGE_BUILT, 'pit_passes': PIT_PASSES,
          'arrivals': arrivals, 'edges': EDGES, 'door_poses': door_poses,
          'cannons': {name: [x, y, round(CANNON_PIVOT)] for name, (x, y) in CANNONS.items()},
          'groups': GROUPS, 'spawn_plan': spawn_plan, 'moved_spawns': moved,
          'actor_groups': {str(g): [a['actor_index'] for a in actors if a['group'] == g] for g in GROUPS.values()},
          'stalls': {k: [round(v) for v in p] for k, p in stall_points.items()}, 'plaza_top': round(PLAZA_TOP),
          'chests_at': [list(c['position'].values()) for c in loot],
          'ring': {'centre': [round(RING[0]), round(RING[1])], 'floor_z': round(height_at(*RING)),
                   'radius': RING_R, 'gate': [round(v) for v in RING_GATE_POINT], 'gate_out': list(GATE_OUT),
                   'dais_top': round(RING_DAIS_TOP), 'vreth': VRETH_INDEX, 'sight_from_road': RING_SIGHT, 'plate': [round(v) for v in RING_PLATE]}}
(PROJECT / 'out4_build.json').write_text(json.dumps(report, indent=1) + '\n')
print('dressing', json.dumps(dressing))
print(json.dumps({k: report[k] for k in ('map', 'bmodels', 'faces', 'entities', 'actors', 'spawns', 'chests',
                                        'ground_items', 'height_range', 'edge_rows')}))
