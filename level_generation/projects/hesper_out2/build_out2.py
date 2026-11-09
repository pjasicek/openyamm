"""Build the Scour (hes_out2.odm, map 9110) from its design: terrain, ground materials, plants, buildings, decorations,
chests, items, people, monsters, events, then the ODM through the editor's writer, into runtime/worlds/hesper for the
shared Hesper stage.

    python3 level_generation/projects/hesper_out2/build_out2.py
    flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py

The design is the authority (design/kreegan_world/zone2/THE_SCOUR.md, BUILD-READY): the terrain functions of
scour_terrain.py, the roads, conveyor, places, spawn points and decoration groups of make_scour_detail.py and the
five camps of work_camps_plan.json. The build never invents a position: everything stands where those put it, moved
only to free ground. Modelled on hesper_out1/build_out1.py (Starport Reach), whose BModel kit it shares
(bmodels.py, houses.py); the Scour's own buildings are scour_kit.py. Nothing is written to assets_dev.
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
DESIGN = ROOT / 'design/kreegan_world/zone2'
OUT1 = ROOT / 'level_generation/projects/hesper_out1'
STAGE_INPUT = ROOT / 'level_generation/projects/hesper_stage'
STAGE = ROOT / 'output/hesper_stage/assets_editor_dev'
SOURCE = PROJECT / 'source'
TREE = PROJECT / 'runtime/worlds/hesper'
MAP = 'hes_out2.odm'
MAP_ID = 9110
sys.path.insert(0, str(DESIGN))
sys.path.insert(0, str(OUT1))
sys.path.insert(0, str(PROJECT))
import make_scour_detail as detail  # noqa: E402
import scour_terrain as terrain  # noqa: E402
from bmodels import Model, normal, write_obj  # noqa: E402
import scour_kit as kit  # noqa: E402

GRID = 128
STEP = 512
TEXELS = 16                                   # weight texels per terrain cell
CU = terrain.CELL_UNITS
BOUND = 4 * CU                                # the playable square: +-23 040
rng = np.random.default_rng(20261023)


# --- Coordinates: the detail script's cells (x east from the west edge, y south from the north edge) ----------------
def cw(cx, cy):
    """World (x, y) of a point in cells."""
    return float((cx - 4) * CU), float((4 - cy) * CU)


def to_px(x, y):
    return terrain.world_px(np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64))


def game_height(z):
    """World height as the map stores it: the outer spoil cliffs flattened above 6 000 (they climb 5 200 a cell)."""
    return np.minimum(np.where(z > 6000.0, 6000.0 + (z - 6000.0) * 0.3, z), 8000.0)


def segment_distance(points, xs, ys):
    best = np.full(np.shape(xs), 1e9)
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        dx, dy = bx - ax, by - ay
        t = np.clip(((xs - ax) * dx + (ys - ay) * dy) / (dx * dx + dy * dy), 0, 1)
        best = np.minimum(best, np.hypot(xs - (ax + t * dx), ys - (ay + t * dy)))
    return best


# --- Terrain heights ------------------------------------------------------------------------------------------------
# The design's world heights (scour_terrain.build_terrain, return_world: the pit floor is world 320, never clamped),
# averaged over 3 x 3 samples round each vertex so the pit's ramps (430 wide) read on the 512 grid.
gx = np.arange(GRID)
sample_x, sample_y = np.meshgrid((gx - 64) * STEP, (64 - gx) * STEP)        # [gy, gx]
heights = np.zeros((GRID, GRID))
for dx in (-170, 0, 170):
    for dy in (-170, 0, 170):
        world, _ = terrain.build_terrain(*to_px(sample_x + dx, sample_y + dy), return_world=True)
        heights += game_height(world) / 9.0

PIT_CENTRE = cw(*terrain.PIT)
PIT_RIM_R = terrain.PIT_RIM * CU
pit_inside = np.hypot(sample_x - PIT_CENTRE[0], sample_y - PIT_CENTRE[1]) < PIT_RIM_R + 150


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
    out = [points[0]]
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        steps = max(1, int(math.hypot(bx - ax, by - ay) / spacing))
        out += [(ax + (bx - ax) * k / steps, ay + (by - ay) * k / steps) for k in range(1, steps + 1)]
    return out


def grade(points, width, falloff, max_slope, smooth=9):
    """Cut a road into the heights: along-path heights smoothed and slope-limited, blended into a corridor. The Great
    Pit is never graded (its benches, ramps and risers stay as the design gives them)."""
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
    reach = width / 2 + falloff
    lo, hi = px.min(0) - reach, px.max(0) + reach
    near = (sample_x >= lo[0]) & (sample_x <= hi[0]) & (sample_y >= lo[1]) & (sample_y <= hi[1]) & ~pit_inside
    for iy, ix in zip(*np.nonzero(near)):
        x, y = sample_x[iy, ix], sample_y[iy, ix]
        d = np.hypot(px[:, 0] - x, px[:, 1] - y)
        k = int(np.argmin(d))
        if d[k] > reach:
            continue
        weight = 1.0 if d[k] <= width / 2 else 1.0 - (d[k] - width / 2) / falloff
        heights[iy, ix] = heights[iy, ix] * (1 - weight) + profile[k] * weight


def flatten(centre, half_x, half_y, yaw=0.0, falloff=700.0, level=None, raise_only=False):
    """Level a pad (the median height under it unless given), blended over falloff."""
    cx, cy = centre
    c, s = math.cos(-yaw), math.sin(-yaw)
    lx = (sample_x - cx) * c - (sample_y - cy) * s
    ly = (sample_x - cx) * s + (sample_y - cy) * c
    inside = (np.abs(lx) <= half_x) & (np.abs(ly) <= half_y)
    if level is None:
        level = float(np.median(heights[inside])) if inside.any() else height_at(cx, cy)
    distance = np.hypot(np.maximum(np.abs(lx) - half_x, 0), np.maximum(np.abs(ly) - half_y, 0))
    weight = np.clip(1.0 - distance / falloff, 0.0, 1.0)
    target = heights * (1 - weight) + level * weight
    heights[:] = np.maximum(heights, target) if raise_only else target
    return level


def run_on(line, distance=11000.0):
    """A road that leaves the playable square at an end runs on past the map's edge (as Starport Reach's)."""
    for end, inner in ((0, 1), (-1, -2)):
        (x, y), (ix, iy) = line[end], line[inner]
        if max(abs(x), abs(y)) > BOUND - 600:
            dx, dy = x - ix, y - iy
            length = math.hypot(dx, dy)
            point = (x + dx / length * distance, y + dy / length * distance)
            line = [point] + line if end == 0 else line + [point]
    return line


# Roads (the detail script's ROADS, in world units). The mine road and the Kreegan Road run on past their edges.
paved = [run_on([cw(*p) for p in line]) for line in detail.ROADS['paved']]
haul = [[cw(*p) for p in line] for line in detail.ROADS['haul']]
haul[0] = run_on(haul[0])                                   # the Kreegan Road
MESA_RAMP_ROAD = 2                                          # graded in the terrain (scour_terrain.MESA_RAMP)
rim = [[cw(*p) for p in line] for line in detail.ROADS['rim']]
tracks = [[cw(*p) for p in line] for line in detail.ROADS['track']]
CAMPS = {camp['n']: camp for camp in json.loads((DESIGN / 'work_camps_plan.json').read_text())['camps']}

# --- Places (world units, from the design's tables) ------------------------------------------------------------------
GATE_D3 = (-12211.0, -403.0)                 # D3's Outer Gate, facing east down the ramp
D3_RETURN = (-11650.0, -403.0)
PYLON_P1 = (-11923.0, 173.0)
DOOR_D4 = (3456.0, -10714.0)                 # D4's Pit Stairs door, facing north across the sunken yard
D4_RETURN = (3456.0, -10138.0)
GATE_D8 = (14112.0, 16819.0)                 # D8's Slag Gate, facing south
D8_RETURN = (14112.0, 16013.0)
TUNNEL = (-21600.0, 8064.0)                  # the tunnel portal, facing east
TUNNEL_ARRIVAL = (-20621.0, 8064.0)
THRIX = (-19872.0, 19123.0)                  # Thrix's stall at his cave mouth
TARRO = (-18778.0, 1498.0)                   # Tarro's lean-to
DEPOT = (19296.0, -11808.0)
DEPOT_PYLON = (19123.0, -11059.0)
DEPOT_PAD = (19872.0, -11981.0)
RELAYS = {20: (-11520.0, -1152.0), 21: (2995.0, -7661.0), 22: (12960.0, 15840.0)}
WEST_ARRIVAL = (-22406.0, -2592.0)
NORTH_ARRIVAL = (2880.0, 22406.0)
WRECK = cw(*terrain.WRECK)
MESA_CENTRE = cw(*terrain.MESA)
PENS_CENTRE = cw(terrain.PENS[0], terrain.PENS[1])
PENS_HALF = (terrain.PENS[2] * CU, terrain.PENS[3] * CU)
FOUNDRY_DEPTH = 2400.0
FOUNDRY_CENTRE = (GATE_D8[0], GATE_D8[1] + FOUNDRY_DEPTH / 2)
CONVEYOR = [cw(*p) for p in detail.CONVEYOR]
DECK_Z = float(detail.CONVEYOR_DECK)

# Building pads (centre, half x, half y, yaw): levelled before the roads are graded; roads go round them.
SITES = {
    'foundry': (FOUNDRY_CENTRE, 2600 + 300, 1200 + 250, 0.0),
    'foundry_annex': ((GATE_D8[0] + 2600 + 900, GATE_D8[1] + FOUNDRY_DEPTH * 0.45), 1000, 900, 0.0),
    'depot': (DEPOT, 1700, 1700, 0.0),
    'thrix': ((THRIX[0], THRIX[1] + 300), 750, 650, 0.0),
    'tarro': (TARRO, 500, 450, 0.0),
}
OPEN_SITES = {'depot'}                       # open yards the roads run into
for name, (centre, hx, hy, yaw) in SITES.items():
    flatten(centre, hx, hy, yaw, falloff=600)

# D3's forecourt: the mesa top between the Outer Gate and the ramp's top, level at the mesa (2 750), P1 on it.
mesa_level = float(terrain.WORLD_MESA)
flatten(((GATE_D3[0] + PYLON_P1[0] + 400) / 2, (GATE_D3[1] + PYLON_P1[1]) / 2 - 150), 750, 600, falloff=350,
        level=mesa_level, raise_only=True)


def roads_under_buildings(lines, half_width):
    """A road goes round a building, never under it; its last 500 at either end may reach a pad (it arrives at the
    door). The open yards are exempt."""
    problems = []
    for index, line in enumerate(lines):
        points = resample(line, 128.0)
        for x, y in points[4:-4]:
            for name, (centre, hx, hy, yaw) in SITES.items():
                if name in OPEN_SITES:
                    continue
                c, s_ = math.cos(-yaw), math.sin(-yaw)
                lx = (x - centre[0]) * c - (y - centre[1]) * s_
                ly = (x - centre[0]) * s_ + (y - centre[1]) * c
                if abs(lx) < hx + half_width and abs(ly) < hy + half_width:
                    problems.append(f'road {index} at ({x:.0f}, {y:.0f}) crosses {name}')
                    break
    return problems


for kind, lines, half_width in (('paved', paved, 350), ('haul', haul + rim, 300), ('track', tracks, 200)):
    crossings = roads_under_buildings(lines, half_width)
    if crossings:
        raise SystemExit(f'build_out2: a {kind} road passes under a building: ' + '; '.join(crossings))
for line in paved:
    grade(line, 700, 600, 0.18)
grade(haul[0], 640, 600, 0.18)                              # the Kreegan Road, the Crown's width
for index, line in enumerate(haul[1:], 1):
    if index != MESA_RAMP_ROAD:
        grade(line, 600, 500, 0.3)
for line in rim:
    grade(line, 600, 400, 0.3)
for line in tracks:
    grade(line, 500, 500, 0.3)

# The work camps (work_camps_plan.json): each yard level; camp 4's upper shanties and perch a terrace step (280) up,
# the step's slope the ramp; camp 5's yard is the duelling ring.
camp_levels = {}
for n, camp in CAMPS.items():
    cx, cy = camp['centre']
    camp_levels[n] = flatten((cx, cy), 1900, 1900, falloff=800)
for n, camp in CAMPS.items():
    for part in camp['parts']:
        if part.get('level'):
            px, py = part['position']
            flatten((px, py), 420, 420, math.radians(part['facing_degrees']), falloff=420,
                    level=camp_levels[n] + part['level'])
    if n == 4:                                                    # the perch stands on the upper terrace too
        perch = next(p for p in camp['parts'] if p['kind'] == 'perch')
        flatten(tuple(perch['position']), 400, 400, falloff=420, level=camp_levels[n] + 280)

# The Pens' sunken yard (D4) lies level at 880 right to its walls: the 3 x 3 averaging rounded its edges, and the
# Pit Stairs door in its south wall stood on the slope.
inside_pens = (np.abs(sample_x - PENS_CENTRE[0]) <= PENS_HALF[0]) & (np.abs(sample_y - PENS_CENTRE[1]) <= PENS_HALF[1])
heights[inside_pens] = float(terrain.WORLD_PENS)

# The depot's pad and the Foundry's apron are level after the roads came in.
flatten(DEPOT, 1500, 1500, falloff=600)
foundry_level = flatten(FOUNDRY_CENTRE, 2600 + 250, 1200 + 200, falloff=600)
flatten((GATE_D8[0], GATE_D8[1] - 700), 900, 700, falloff=500, level=foundry_level)

# The tunnel portal is set into the canyon's west wall: the rock behind and beside it rises 1 100 above the canyon
# floor (as Starport Reach's Pumping Station), the floor in front of it level.
# On the 512 grid the floor reaches the first vertex behind the portal's face (x -22 016), so no terrain triangle
# climbs over the shutter; the rock rises from there to full height 500 further back, behind the portal's block.
tunnel_floor = height_at(*TUNNEL_ARRIVAL)
behind = np.maximum.reduce([sample_x - (TUNNEL[0] - 900), np.abs(sample_y - TUNNEL[1]) - 1400,
                            (TUNNEL[0] - 2600) - sample_x, np.zeros_like(sample_x)])
cliff = np.clip(1.0 - behind / 500.0, 0.0, 1.0)
heights[:] = np.maximum(heights, heights * (1 - cliff) + (tunnel_floor + 1100) * cliff)
flatten(((TUNNEL[0] - 430 + TUNNEL_ARRIVAL[0]) / 2, TUNNEL[1]), (TUNNEL_ARRIVAL[0] - TUNNEL[0] + 430) / 2 + 100, 600,
        falloff=200, level=tunnel_floor)
# Thrix's cave: the canyon's head rises behind his stall into a rock face (the cave's BModel stands in it).
thrix_floor = height_at(*THRIX)
CAVE_FACE_Y = THRIX[1] + 650                               # the cave's rock face (the thrix_cave BModel) stands here
behind = np.maximum.reduce([(CAVE_FACE_Y + 700) - sample_y, np.abs(sample_x - THRIX[0]) - 1300,
                            np.zeros_like(sample_x)])
cliff = np.clip(1.0 - behind / 500.0, 0.0, 1.0)            # level to the first vertex behind the face, then rock
heights[:] = np.maximum(heights, heights * (1 - cliff) + (thrix_floor + 1200) * cliff)

# The edge contracts (WORK_PACKAGES/README.md, edges/hes_out1_built_edges.json): the west crossing band levelled to
# Starport Reach's built east edge within 1 550 of the edge; the north gap a level floor at 1 200 between x 1 880 and
# 3 880 for 1 555 in.
edge_rows = json.loads((ROOT / 'design/kreegan_world/WORK_PACKAGES/edges/hes_out1_built_edges.json').read_text())
east = edge_rows['east_edge_x_23040']
profile_y, profile_h = np.array(east['y'][::-1], float), np.array(east['in_0'][::-1], float)
band_y = (-2592 - 3600, -2592 + 3300)                       # rows 4-6 round the road (the design's west band)
west_band = (sample_x <= -BOUND + 1550) & (sample_x >= -BOUND - 2048) & (sample_y > band_y[0]) & (sample_y < band_y[1])
heights[west_band] = np.interp(sample_y[west_band], profile_y, profile_h)
# On the 512 grid the floor's vertices run from 1 536 to 4 096, so the whole 1 880-3 880 floor is level.
north_gap = (sample_y >= BOUND - 1555) & (sample_y <= BOUND + 2048) & (sample_x >= 1536) & (sample_x <= 4096)
heights[north_gap] = float(terrain.EDGE_NORTH)

height_bytes = np.clip(np.round(heights / 32.0), 0, 255).astype(np.uint8)
heights = height_bytes.astype(np.float64) * 32.0          # the quantised heights everything else stands on

# --- Materials: tiles (one per cell), the molten slag, weights (16 texels per cell) ---------------------------------
# Tile ids through the lookups [volcanic 198, rock 342, sand 594, lava 378]: raw 90 + 36 * set + offset. The tile names
# key the plant rules (ash tufts on the ash) and the liquid (the lava set is the stage's molten_slag, its lvdr* shores
# picked as Starport Reach's brine shores); the ground itself is drawn by the material weights.
LOOKUPS = [198, 342, 594, 378]
TILES = {'ash': 90, 'spoil': 91, 'haul': 91, 'plating': 91, 'slag': 91, 'seam': 91, 'creep': 102, 'wall': 91,
         'rock': 126, 'molten': 198}
LAVA_EDGE = {'S': 216, 'N': 217, 'W': 214, 'E': 215}
LAVA_INNER = {'SW': 218, 'NW': 219, 'SE': 220, 'NE': 221}
LAVA_OUTER = {'SW': 210, 'NW': 211, 'SE': 212, 'NE': 213}
LAYERS = ['spoil', 'haul', 'plating', 'slag', 'seam', 'creep', 'ash']          # weighted; 'rock' is the slope layer
MIX = {'spoil': {'spoil': 1.0}, 'rock': {'spoil': 1.0}, 'wall': {'spoil': 1.0}, 'haul': {'haul': 1.0},
       'plating': {'plating': 1.0}, 'slag': {'slag': 1.0}, 'seam': {'seam': 1.0}, 'creep': {'creep': 1.0},
       'ash': {'ash': 1.0}, 'molten': {'slag': 1.0}}


def road_masks(xs, ys):
    """The mine road's pavers, the haul roads and the Rim Road, and the tracks' ruts at world points."""
    road = segment_distance_any(paved, xs, ys) < 350
    hauled = segment_distance_any(haul + rim, xs, ys) < 300
    track_d = segment_distance_any(tracks, xs, ys)
    ruts = np.abs(track_d - 150) < 55
    return road, hauled, ruts


def segment_distance_any(lines, xs, ys):
    best = np.full(np.shape(xs), 1e9)
    for line in lines:
        best = np.minimum(best, segment_distance(line, xs, ys))
    return best


def yard_masks(xs, ys):
    """The camps' ore yards (crushed ore) and the Pens' trampled yard."""
    mask = np.zeros(np.shape(xs), bool)
    for camp in CAMPS.values():
        part = camp['parts'][0]                               # the yard or the ring
        (px, py), (w, d), yaw = part['position'], part['size'], math.radians(part['facing_degrees'] - 90)
        c, s = math.cos(-yaw), math.sin(-yaw)
        lx, ly = (xs - px) * c - (ys - py) * s, (xs - px) * s + (ys - py) * c
        mask |= (np.abs(lx) <= w / 2) & (np.abs(ly) <= d / 2)
    return mask


cell_x, cell_y = np.meshgrid((gx - 64) * STEP + STEP / 2, (64 - gx) * STEP - STEP / 2)
_, cell_material = terrain.build_terrain(*to_px(cell_x, cell_y), return_world=True)
cell_material = cell_material.astype(object)


def lava_tiles(lava):
    """Shore tiles round the molten cells (rows run north to south), as Starport Reach's brine_tiles: land cells beside
    lava take the shore tile of the side or corner the lava lies on; a land cell with lava on opposite sides, three
    sides or two diagonals alone becomes lava. Returns the lava mask and the shore cells' tile ids (0 elsewhere)."""
    lava = lava.copy()
    while True:
        padded = np.pad(lava, 1)
        n, s_, w, e = padded[:-2, 1:-1], padded[2:, 1:-1], padded[1:-1, :-2], padded[1:-1, 2:]
        nw, ne, sw, se = padded[:-2, :-2], padded[:-2, 2:], padded[2:, :-2], padded[2:, 2:]
        sides = n.astype(int) + s_ + w + e
        fill = ~lava & ((n & s_) | (w & e) | (sides >= 3) | ((sides == 0) & ((nw.astype(int) + ne + sw + se) >= 2)))
        if not fill.any():
            break
        lava |= fill
    shore = np.zeros(lava.shape, np.uint8)
    land = ~lava
    for name, mask in (('S', s_), ('N', n), ('W', w), ('E', e)):
        shore[land & (sides == 1) & mask] = LAVA_EDGE[name]
    for name, (a, b) in {'SW': (s_, w), 'NW': (n, w), 'SE': (s_, e), 'NE': (n, e)}.items():
        shore[land & (sides == 2) & a & b] = LAVA_INNER[name]
    for name, mask in (('SW', sw), ('NW', nw), ('SE', se), ('NE', ne)):
        shore[land & (sides == 0) & mask] = LAVA_OUTER[name]
    return lava, shore


lava_mask, lava_shore = lava_tiles(cell_material == 'molten')
cell_material[lava_mask] = 'molten'
tile_bytes = np.vectorize(TILES.get)(cell_material).astype(np.uint8)
tile_bytes[lava_shore > 0] = lava_shore[lava_shore > 0]
# The molten slag runs in a cut channel (the integrator's review of build01: on the slope it read as spilled paint): its
# bed falls smoothly along the river from the Foundry's spout to the cooling pond, every corner of a lava or shore cell
# on the bed (so the liquid lies flat across the channel), the pond level; the corners round it stand at least 300
# above the bed, the channel's crust banks (slag crust in the weights).


def cell_corners(cells):
    corners = np.zeros(heights.shape, bool)
    for dy in (0, 1):
        for dx in (0, 1):
            corners[dy:GRID, dx:GRID] |= cells[:GRID - dy, :GRID - dx]
    return corners


RIVER = [cw(*p) for p in terrain.SLAG_RIVER] + [cw(*terrain.SLAG_POND[:2])]
river_points = np.array(resample(RIVER, 64.0))
river_along = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(river_points, axis=0).T))])
lava_corners = cell_corners(lava_mask)
hot_corners = cell_corners(lava_mask | (lava_shore > 0))
hot_index = np.nonzero(hot_corners)
nearest = np.argmin(np.hypot(sample_x[hot_index][:, None] - river_points[:, 0],
                             sample_y[hot_index][:, None] - river_points[:, 1]), axis=1)
pond_level = float(heights[lava_corners].min())
head = float(np.median(heights[hot_index][nearest == nearest.min()])) - 300.0
bed = head + (pond_level - head) * river_along[nearest] / river_along[-1]
POND_R = terrain.SLAG_POND[2] * CU + 700
in_pond = np.hypot(sample_x[hot_index] - RIVER[-1][0], sample_y[hot_index] - RIVER[-1][1]) < POND_R
heights[hot_index] = np.where(in_pond, pond_level, np.minimum(bed, heights[hot_index]))
banks = cell_corners(ndimage.binary_dilation(lava_mask | (lava_shore > 0), structure=np.ones((3, 3)))) & ~hot_corners
bank_index = np.nonzero(banks)
bank_bed = np.array([heights[hot_index][np.argmin(np.hypot(sample_x[hot_index] - x, sample_y[hot_index] - y))]
                     for x, y in zip(sample_x[bank_index], sample_y[bank_index])])
heights[bank_index] = np.maximum(heights[bank_index], bank_bed + 300.0)
height_bytes = np.clip(np.round(heights / 32.0), 0, 255).astype(np.uint8)
heights = height_bytes.astype(np.float64) * 32.0
# The attribute map: the lava cells burn (TerrainTileBurn, the engine's lava damage); nothing else.
attribute_bytes = np.where(lava_mask, 0x01, 0x00).astype(np.uint8)

size = GRID * TEXELS
units = 65536.0 / size
tx, ty = np.meshgrid(-32768.0 + (np.arange(size) + 0.5) * units, 32768.0 - (np.arange(size) + 0.5) * units)
_, texel_material = terrain.build_terrain(*to_px(tx, ty), return_world=True)
field = np.zeros((size, size, len(LAYERS)), dtype=np.float32)
for material, mix in MIX.items():
    where = texel_material == material
    for layer, weight in mix.items():
        field[..., LAYERS.index(layer)] += where * weight
del texel_material
softness = 110.0 / units
field = np.stack([ndimage.gaussian_filter(field[..., c], softness, mode='nearest') for c in range(len(LAYERS))], -1)
road_t, haul_t, ruts_t = road_masks(tx, ty)
yards_t = yard_masks(tx, ty)
apron_t = np.hypot(tx - TUNNEL_ARRIVAL[0] + 300, ty - TUNNEL[1]) < 700      # the tunnel mouth's apron of pavers
# The slag river's crust banks: dark slag crust within about 800 of the channel's cells.
channel = np.repeat(np.repeat(lava_mask | (lava_shore > 0), TEXELS, 0), TEXELS, 1)
crust_t = ndimage.binary_dilation(channel, iterations=int(800 / units)) & ~channel
for mask, layer, crisp in [(crust_t, 'slag', 2.5), (ruts_t, 'haul', 0.8), (yards_t, 'haul', 1.5),
                           (haul_t, 'haul', 0.8), (road_t, 'plating', 0.75), (apron_t, 'plating', 1.0)]:
    weight = np.clip(ndimage.gaussian_filter(mask.astype(np.float32), crisp, mode='nearest'), 0, 1)
    field *= (1 - weight)[..., None]
    field[..., LAYERS.index(layer)] += weight
# Spoil dust over the old pavers (the integrator's review of build01: the clean white paving glared like snow on the
# Scour's dun ground): crushed ore blown over the road, fading out toward the west edge so the crossing still meets
# Starport Reach's clean paving.
fade = np.clip((tx - (-BOUND + 1200)) / 2400.0, 0.0, 1.0)
dust = np.clip(ndimage.gaussian_filter((road_t | apron_t).astype(np.float32), 0.75, mode='nearest'), 0, 1) * 0.6 * fade
field[..., LAYERS.index('haul')] += dust * field[..., LAYERS.index('plating')]
field[..., LAYERS.index('plating')] *= 1.0 - dust
field /= np.maximum(field.sum(-1, keepdims=True), 1e-6)
field = np.concatenate([field, np.zeros((size, size, 8 - len(LAYERS)), dtype=np.float32)], -1)
quantized = np.clip(field * 255 + 0.5, 0, 255).astype(np.uint8)
del tx, ty

# --- Buildings (BModels) ---------------------------------------------------------------------------------------------
SIZES = {}                          # texture -> native size (master / 4)
for folder in ['textures_d0/blv', 'textures_out1/masters', 'textures_interiors/masters', 'textures_k5_grafted/masters',
               'textures_k6_foundry/masters', 'textures_k12_salvage/masters']:
    for png in (ROOT / 'design/kreegan_world/art' / folder).glob('*.png'):
        with Image.open(png) as image:
            SIZES[png.stem] = (image.width / 4, image.height / 4)
# World size of one repeat over the native size, for the textures whose detail reads too small at one native texel per
# world unit on buildings this large (Starport Reach's TEXTURE_SCALE, plus the Scour's tall kit faces).
TEXTURE_SCALE = {'hoterm': 1.25, 'hhscrapw': 1.5, 'hhprefab': 1.75, 'hhprefdk': 1.75, 'hhrock': 2.0,
                 'homstack': 2.0, 'hompier': 1.5, 'homshed': 1.75, 'homroof': 1.75, 'hokwall': 1.5, 'hokspine': 1.5,
                 'hmgantry': 1.25, 'hkcage': 1.25, 'hhkeptw': 1.25, 'hhkeptrf': 1.25}
for texture, scale in TEXTURE_SCALE.items():
    SIZES[texture] = (SIZES[texture][0] * scale, SIZES[texture][1] * scale)
models = []
EVENTS = {}                         # event id -> (title, handler body)


def ground(point):
    return height_at(*point)


# The conveyor line: piers every 0.3 cells along CONVEYOR (none on a road: a pier there moves along the line), the
# deck spans between them at world 2 900, the central hopper tower on the pit floor and the south loading hopper.
conveyor = Model('conveyor')
HOPPER_POINTS = [cw(x, y) for x, y, _ in detail.HOPPERS]
pier_points = []
for a, b in zip(CONVEYOR, CONVEYOR[1:]):
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    steps = max(1, round(length / (0.3 * CU)))
    for k in range(steps + (1 if b == CONVEYOR[-1] else 0)):
        pier_points.append((a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps))
road_points = [p for line in paved + haul + rim for p in resample(line, 128)]


def on_road(x, y, margin=420):
    return any(math.hypot(x - rx, y - ry) < margin for rx, ry in road_points)


piers = []
for x, y in pier_points:
    if any(math.hypot(x - hx, y - hy) < 300 for hx, hy in HOPPER_POINTS):
        piers.append((x, y, 'hopper'))
        continue
    if x >= CONVEYOR[-1][0] - 50 and abs(y - CONVEYOR[-1][1]) < 50:
        piers.append((x, y, 'intake'))                     # the deck enters the Foundry's west wall
        continue
    direction = (0.0, 1.0) if abs(x - CONVEYOR[0][0]) < 1 else (1.0, 0.0)
    for shift in (0, 300, -300, 600, -600, 900, -900):
        px, py = x + direction[0] * shift, y + direction[1] * shift
        if not on_road(px, py):
            break
    piers.append((px, py, 'pier'))
# The deck stands at 2 900 (the Foundry's intake height) and climbs to 760 over the ground where the spoil hills rise
# toward it (south of the pit, the north leg under the ridge), so the party walks under it everywhere.
deck_z = [max(DECK_Z, ground((x, y)) + 760) for x, y, _ in piers]
for k in range(len(deck_z)):                               # a belt rises gently: at most 300 a span
    deck_z[k] = max(deck_z[k], max(deck_z[j] - 300 * abs(j - k) for j in range(len(deck_z))))
for (ax, ay, _), (bx, by, kind), za, zb in zip(piers, piers[1:], deck_z, deck_z[1:]):
    kit.deck_span(conveyor, (ax, ay), (bx, by), za, zb)
for k, (x, y, kind) in enumerate(piers):
    if kind == 'pier':
        a = piers[max(k - 1, 0)]
        b = piers[min(k + 1, len(piers) - 1)]
        kit.pier(conveyor, x, y, ground((x, y)), deck_z[k], yaw=math.atan2(b[1] - a[1], b[0] - a[0]))
    elif kind == 'hopper':
        kit.hopper(conveyor, x, y, ground((x, y)), deck_z[k])
INTAKE_Z = deck_z[-1]
models.append(conveyor)

# The smokestacks (STACKS): tops at world 5 000-6 000 (the Foundry's own two the tallest).
stacks = Model('stacks')
STACK_TOPS = [6000, 5800, 5400, 5200, 5000]
stack_points = []
for (sx, sy), top in zip(detail.STACKS, STACK_TOPS):
    x, y = cw(sx, sy)
    kit.stack(stacks, x, y, ground((x, y)), top)
    stack_points.append((x, y, top))
models.append(stacks)

# The Foundry hall and annex (D8's Slag Gate, event 53), the conveyor's intake on its west wall.
models.append(kit.foundry('foundry', GATE_D8, foundry_level, 53, intake_y=CONVEYOR[-1][1], intake_z=INTAKE_Z))

# The supply depot's two works sheds, their open fronts north to the yard (the salvage crates stand inside).
CRATES = {33: cw(7.48, 6.20), 34: cw(7.22, 6.24)}
for k, (event, (x, y)) in enumerate(CRATES.items()):
    models.append(kit.depot_shed(f'depot_shed_{k}', (x, y - 260), ground((x, y)), math.pi / 2))

# D3's outer wall ring on the mesa top, the Outer Gate (event 50) on its east side.
gate_angle = math.atan2(GATE_D3[1] - MESA_CENTRE[1], GATE_D3[0] - MESA_CENTRE[0])
ring_radius = math.hypot(GATE_D3[0] - MESA_CENTRE[0], GATE_D3[1] - MESA_CENTRE[1]) - 80
models.append(kit.wall_ring('d03_wall', MESA_CENTRE, ring_radius / math.cos(math.pi / 12), mesa_level, gate_angle,
                            50))

# D4's sunken compound: the Pit Stairs door bay (event 51) in the yard's south wall, two cage rows inside.
pens_floor = float(terrain.WORLD_PENS)
models.append(kit.pens_door_bay('d04_door', DOOR_D4, pens_floor, 51))
cages = Model('d04_cages')
for side in (-1, 1):
    kit.cage_row(cages, (PENS_CENTRE[0] + side * (PENS_HALF[0] - 380), PENS_CENTRE[1] - 150), pens_floor, math.pi / 2)
models.append(cages)

# The work camps (work_camps_plan.json): the shanties (no events: homes of the Kept) and the camp gates.
camp_models = {}
for n, camp in CAMPS.items():
    m = Model(f'camp_{n}')
    for part in camp['parts']:
        px, py = part['position']
        if part['kind'] == 'shanty':
            z = camp_levels[n] + part.get('level', 0)
            kit.kept_shanty(m, px, py, z, math.radians(part['facing_degrees']))
        elif part['kind'] == 'post':
            kit.camp_gate(m, part['corners'], ground((px, py)))
    models.append(m)
    camp_models[n] = m

# Thrix's stall (house 9300, event 300) at his cave mouth, facing south down the canyon; the cave's rock face behind.
models.append(kit.thrix_stall('thrix_stall', THRIX[0], THRIX[1], thrix_floor, -math.pi / 2, 300))
cave = Model('thrix_cave')
cz = thrix_floor
for (xa, xb, za, zb, y0) in ((-900, -260, -60, 1100, 650), (260, 900, -60, 1100, 650), (-260, 260, 520, 1100, 650)):
    cave.facing([(THRIX[0] + xb, THRIX[1] + y0, cz + za), (THRIX[0] + xa, THRIX[1] + y0, cz + za),
                 (THRIX[0] + xa, THRIX[1] + y0, cz + zb), (THRIX[0] + xb, THRIX[1] + y0, cz + zb)], 'hhrock',
                (0, -1, 0))
cave.facing([(THRIX[0] + 260, THRIX[1] + 1100, cz), (THRIX[0] - 260, THRIX[1] + 1100, cz),
             (THRIX[0] - 260, THRIX[1] + 1100, cz + 520), (THRIX[0] + 260, THRIX[1] + 1100, cz + 520)], 'hhcliffdt',
            (0, -1, 0), fit=True)
for xs, out in ((-260, 1), (260, -1)):
    cave.facing([(THRIX[0] + xs, THRIX[1] + 650, cz), (THRIX[0] + xs, THRIX[1] + 1100, cz),
                 (THRIX[0] + xs, THRIX[1] + 1100, cz + 520), (THRIX[0] + xs, THRIX[1] + 650, cz + 520)], 'hhrock',
                (out, 0, 0))
cave.facing([(THRIX[0] - 260, THRIX[1] + 650, cz + 520), (THRIX[0] + 260, THRIX[1] + 650, cz + 520),
             (THRIX[0] + 260, THRIX[1] + 1100, cz + 520), (THRIX[0] - 260, THRIX[1] + 1100, cz + 520)], 'hhrock',
            (0, 0, -1))
models.append(cave)

# Tarro's lean-to (house 9301, event 301), its open front west toward the canyon track.
models.append(kit.tarro_lean_to('tarro_lean_to', TARRO[0], TARRO[1], ground(TARRO), math.pi, 301))

# The tunnel portal (event 52) in the canyon's west wall, facing east onto the canyon floor.
models.append(kit.tunnel_portal('tunnel_portal', TUNNEL[0], TUNNEL[1], tunnel_floor, 0.0, 52))

# --- Decorations ------------------------------------------------------------------------------------------------------
ids = json.loads((ROOT / 'output/hesper_stage/decoration_ids.json').read_text())
STAGE_DECORATIONS = yaml.safe_load((STAGE_INPUT / 'decorations.yml').read_text())
DECORATION_RADII = {d['name']: d.get('radius', 0) for d in STAGE_DECORATIONS['decorations']}
entities = []
model_placements = []                   # the big models the minimap draws
MINIMAP_MODELS = {'hes_derelict_hull_a', 'hes_derelict_hull_b', 'hes_overseer_perch', 'hes_alarm_pylon',
                  'hes_alarm_pylon_off', 'hes_spoil_heap', 'hes_slag_heap', 'hes_skull_ribs'}


def decoration(name, x, y, facing=None, event=0, sink=0.0, cog=0, z=None):
    """A decoration entity. A click runs `event` (the engine reads the secondary slot); `cog` (the primary) keys
    evt.SetSprite's swaps."""
    facing = int(rng.integers(0, 360)) if facing is None else int(round(facing)) % 360
    position = {'x': int(round(x)), 'y': int(round(y)),
                'z': int(round((height_at(x, y) if z is None else z) - sink))}
    if name in MINIMAP_MODELS:
        model_placements.append({'name': name, **position, 'facing': facing})
    entities.append({'entity_index': 0, 'name': name, 'decoration_list_id': ids[name] - 1, 'ai_attributes': 0,
                     'position': position, 'facing': facing, 'event_id_primary': cog,
                     'event_id_secondary': event, 'variable_primary': 0, 'variable_secondary': 0, 'special_trigger': 0,
                     'initial_decoration_flag': 0})
    return entities[-1]


def model_file(name):
    """The GLB a decoration is drawn with (its stage row's `model`, in the stage's source folders)."""
    entry = next(d for d in STAGE_DECORATIONS['decorations'] if d['name'] == name)
    model = entry.get('model', name)
    for folder in STAGE_DECORATIONS['source_dirs']:
        for suffix in ('', '_export'):
            path = ROOT / folder / f'{model}{suffix}.glb'
            if path.exists():
                return path
    raise FileNotFoundError(name)


DESIGNS = json.loads((ROOT / 'level_generation/props/hesper_decorations/designs.json').read_text())


def model_scale(name):
    """World units per glTF unit, and the model's glTF bounds (x, y up, z)."""
    data = model_file(name).read_bytes()
    gltf = json.loads(data[20:20 + int.from_bytes(data[12:16], 'little')])
    accessors = [gltf['accessors'][primitive['attributes']['POSITION']] for mesh in gltf['meshes']
                 for primitive in mesh['primitives']]
    low = np.min([a['min'] for a in accessors], 0)
    high = np.max([a['max'] for a in accessors], 0)
    return (DESIGNS[name]['length'] / max(high - low) if name in DESIGNS else 100.0), low, high


def model_bounds(name):
    scale, low, high = model_scale(name)
    return low * scale, high * scale


colliders = Model('colliders')


def collision_box(x, y, size_x, size_y, height, yaw=0.0):
    colliders.collider((x, y, height_at(x, y) - 60), (size_x, size_y, height + 60), yaw=yaw)


footprints = [(centre, max(hx, hy) + 200) for centre, hx, hy, _ in SITES.values()] + \
    [((float(c['centre'][0]), float(c['centre'][1])), 2100) for c in CAMPS.values()] + \
    [(MESA_CENTRE, ring_radius + 400), (PENS_CENTRE, 1900), (WRECK, 2400), (TUNNEL, 900)]


def clear(x, y, margin=0.0):
    """Open ground: inside the playable square, off the buildings, the camps and the roads."""
    if abs(x) > BOUND - 600 or abs(y) > BOUND - 600:
        return False
    if any(math.hypot(x - c[0], y - c[1]) < r + margin for c, r in footprints):
        return False
    road, hauled, ruts = road_masks(np.array([x]), np.array([y]))
    return not (road[0] or hauled[0] or ruts[0])


def level_ground(x, y, rise=80.0):
    z = height_at(x, y)
    return all(abs(height_at(x + dx, y + dy) - z) < rise for dx, dy in ((150, 0), (-150, 0), (0, 150), (0, -150)))


def spaced(x, y, gap):
    return all(math.hypot(x - e['position']['x'], y - e['position']['y']) >= gap for e in entities)


SLAG = [(cw(x, y), r * CU) for x, y, r in terrain.SLAG_FIELDS] + [(cw(6.2, 1.0), 0.75 * CU)]


def on_slag(x, y):
    return any(math.hypot(x - c[0], y - c[1]) < r for c, r in SLAG)


# The detail script's DECOR groups: (symbol, cell x, cell y, count, spread in cells).
SYMBOLS = {'cart': 'hes_ore_cart', 'salvage': 'hes_salvage_heap', 'part': 'hes_conveyor_parts', 'pod': 'hes_creep_pod',
           'vent': 'hes_ground_vent', 'bones': 'hes_skull_ribs', 'marker': 'hes_survey_marker',
           'brazier': 'hes_brazier_out', 'scrub': 'hes_wire_thicket'}
SIGN_EVENTS = {(0.62, 4.32): 10, (2.6, 4.68): 11, (3.3, 3.95): 12, (4.58, 1.88): 13}
dressing = {}
for symbol, cx, cy, count, spread in detail.DECOR:
    if symbol == 'tuft':
        continue                                   # ash tufts are the plant rules' (voltyl)
    centre = cw(cx, cy)
    if symbol == 'sign':
        decoration('hes_signpost', *centre, facing=int(rng.integers(0, 360)), event=SIGN_EVENTS[(cx, cy)])
        continue
    placed = 0
    for _ in range(count * 40):
        if placed == count:
            break
        dx, dy = rng.normal(0, spread * CU * 0.35, 2) if spread > 0 else (0.0, 0.0)
        x, y = centre[0] + dx, centre[1] + dy
        if symbol == 'heap':
            name = 'hes_slag_heap' if on_slag(x, y) else 'hes_spoil_heap'
        else:
            name = SYMBOLS[symbol]
        radius = DECORATION_RADII.get(name, 0)
        inside_place = symbol in ('cart', 'salvage', 'part', 'pod', 'vent', 'brazier', 'marker')
        if inside_place:
            road, hauled, ruts = road_masks(np.array([x]), np.array([y]))
            if road[0] or not spaced(x, y, radius + 120) or not level_ground(x, y, 160):
                continue
        elif not clear(x, y, radius + 100) or not spaced(x, y, radius + 200) or not level_ground(x, y, 160):
            continue
        decoration(name, x, y, sink=20 if symbol == 'bones' else 0)
        dressing[name] = dressing.get(name, 0) + 1
        placed += 1

# The open ground between the landmarks (the user's review of build01: "too empty"): a small group of the works'
# leavings beside the roads every ~1 500, sides alternating, and round the pit rim, its kind by what it stands on
# (slag, the rim, a camp's surroundings, the ash, the haul roads). Off the roads, the buildings and the lava.
GROUPS = {'rim': ['hes_spoil_heap', 'hes_survey_marker', 'hes_conveyor_parts', 'hes_wreck_plates'],
          'slag': ['hes_slag_heap', 'hes_ground_vent', 'hes_armour_plate'],
          'camp': ['hes_ore_crates', 'hes_ore_cart', 'hes_salvage_heap', 'hes_ore_sledge'],
          'ash': ['hes_wire_thicket', 'hes_salvage_heap', 'hes_wire_thicket'],
          'road': ['hes_ore_crates', 'hes_spoil_heap', 'hes_survey_marker', 'hes_wreck_plates', 'hes_conveyor_parts',
                   'hes_armour_plate', 'hes_ore_cart']}
KEEP_OPEN = [WEST_ARRIVAL, NORTH_ARRIVAL, TUNNEL_ARRIVAL] + [(x, y) for x, y in pier_points]
hot_cells = np.pad(lava_mask | (lava_shore > 0), 1)


def dress_ok(x, y, radius):
    col, row = int((x + 32768) // STEP), int((32768 - y) // STEP)
    if hot_cells[row:row + 3, col:col + 3].any() or any(math.hypot(x - kx, y - ky) < 900 for kx, ky in KEEP_OPEN):
        return False
    return clear(x, y, radius + 80) and spaced(x, y, radius + 160) and level_ground(x, y, 140)


def group_kind(x, y):
    col, row = int((x + 32768) // STEP), int((32768 - y) // STEP)
    if on_slag(x, y):
        return 'slag'
    if abs(math.hypot(x - PIT_CENTRE[0], y - PIT_CENTRE[1]) - PIT_RIM_R) < 1600:
        return 'rim'
    if any(math.hypot(x - c['centre'][0], y - c['centre'][1]) < 4200 for c in CAMPS.values()):
        return 'camp'
    return 'ash' if cell_material[min(row, GRID - 1), min(col, GRID - 1)] == 'ash' else 'road'


def dress_group(x, y, kind):
    """An anchor piece at (x, y) and one or two smaller pieces round it; returns the pieces placed."""
    palette = GROUPS[kind]
    names = [palette[int(rng.integers(0, len(palette)))] for _ in range(int(rng.integers(2, 4)))]
    count = 0
    for k, name in enumerate(names):
        radius = DECORATION_RADII.get(name, 0)
        for _ in range(8):
            if k == 0:
                px, py = x, y
            else:
                a, r = rng.uniform(0, 2 * math.pi), rng.uniform(260, 420) + radius
                px, py = x + r * math.cos(a), y + r * math.sin(a)
            if dress_ok(px, py, radius):
                decoration(name, px, py)
                dressing[name] = dressing.get(name, 0) + 1
                count += 1
                break
        if k == 0 and count == 0:
            return 0
    return count


side = 1
for line in paved + haul + rim + tracks:
    points = resample(line, 1500)
    for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
        length = math.hypot(bx - ax, by - ay)
        if length < 1:
            continue
        nx, ny = -(by - ay) / length, (bx - ax) / length
        side = -side
        for offset in (700, 900, 1150):
            x, y = ax + nx * offset * side, ay + ny * offset * side
            if dress_group(x, y, group_kind(x, y)):
                break
for k in range(28):                                          # the pit rim, outside the rim road
    a = 2 * math.pi * k / 28
    for out in (500, 900):
        x, y = PIT_CENTRE[0] + (PIT_RIM_R + out) * math.cos(a), PIT_CENTRE[1] + (PIT_RIM_R + out) * math.sin(a)
        if dress_group(x, y, 'slag' if on_slag(x, y) else 'rim'):
            break
for gx_ in np.arange(-BOUND + 1800, BOUND - 1000, 3000):    # the open ground away from the roads, a group per ~3 000
    for gy_ in np.arange(-BOUND + 1800, BOUND - 1000, 3000):
        x, y = gx_ + rng.uniform(-700, 700), gy_ + rng.uniform(-700, 700)
        if spaced(x, y, 1500):
            dress_group(x, y, group_kind(x, y))

# --- The camps' fixtures: the collar node, the Overseer's perch and its fire bowls, the freed camp's brazier --------
PERCH_DECK = 905                                           # the perch model's deck (hes_overseer_perch, 1 000 high)
# Cogs (THE_SCOUR.md section 17): 171-175 the nodes, 176-180 the bowls (camp n = 175 + n), 181-185 the braziers.
camp_fixtures = {}
for n, camp in CAMPS.items():
    parts = {p['kind']: p for p in camp['parts'] if p['kind'] in ('node', 'perch', 'post')}
    node = parts['node']['position']
    perch = parts['perch']['position']
    level = camp_levels[n]
    decoration('hes_collar_node', *node, facing=0, event=70 + n, cog=170 + n, z=level)
    collision_box(*node, 360, 360, 420)                    # the node's plinth (the model is 420 square)
    perch_z = level + (280 if n == 4 else 0)
    decoration('hes_overseer_perch', *perch, facing=0, z=perch_z)
    collision_box(*perch, 460, 460, PERCH_DECK)            # its four legs (560 apart at the feet) up to the deck
    toward = np.array(node, float) - np.array(perch, float)
    toward /= np.linalg.norm(toward)
    across = np.array([-toward[1], toward[0]])
    bowls = []
    for side in (-1, 1):
        bx, by = np.array(perch, float) + toward * 380 + across * side * 320
        decoration('hes_fire_bowl_out', bx, by, facing=0, cog=175 + n, z=perch_z if n == 4 else None)
        bowls.append((bx, by))
    bx, by = np.array(node, float) + toward * -420 + across * 420
    decoration('hes_brazier_out', bx, by, facing=0, cog=180 + n, z=level)
    camp_fixtures[n] = {'node': node, 'perch': perch, 'perch_z': perch_z, 'bowls': bowls, 'brazier': (bx, by),
                        'gate': parts['post']['position'], 'toward': toward.tolist(), 'across': across.tolist()}


def camp_point(n, along, side):
    """A point of camp n in its own frame: `along` from the node toward the gate (the road in), `side` across."""
    camp = CAMPS[n]
    node = np.array(camp_fixtures[n]['node'], float)
    gate = np.array(camp_fixtures[n]['gate'], float)
    out = (gate - node) / np.linalg.norm(gate - node)
    return tuple(node + out * along + np.array([-out[1], out[0]]) * side)


# Each camp's own touch (the camp plan's variations).
for k, (along, side) in enumerate([(-600, 700), (200, -750)]):
    decoration('hes_wreck_plates', *camp_point(1, along, side), facing=int(rng.integers(0, 360)), z=camp_levels[1])
for along, side, name in [(-500, -700, 'hes_slag_heap'), (500, 650, 'hes_ore_sledge'), (650, 450, 'hes_ore_sledge')]:
    decoration(name, *camp_point(2, along, side), z=camp_levels[2])
for along, side in [(700, -900), (900, -650), (1050, -400)]:
    decoration('hes_ore_cart', *camp_point(3, along, side), z=camp_levels[3])
decoration('hes_corpse_kept', *camp_point(3, -350, 800), z=camp_levels[3])
# Camp 5's duelling ring: eight bone posts round the node at 450, fire bowls beside two of them.
ring_node = camp_fixtures[5]['node']
for k in range(8):
    a = 2 * math.pi * k / 8 + math.pi / 8
    px, py = ring_node[0] + 450 * math.cos(a), ring_node[1] + 450 * math.sin(a)
    decoration('hes_duel_post', px, py, facing=math.degrees(a), z=camp_levels[5])
    if k in (1, 5):                                # the ring's own two bowls stay lit when the camp is freed
        decoration('hes_fire_bowl_out', px + 90 * math.cos(a), py + 90 * math.sin(a), facing=0, z=camp_levels[5])

# The depot: the pylon (event 80, cog 186), six closed drop pods on the pad (cogs 140-145), salvage, creep pods.
decoration('hes_alarm_pylon', *DEPOT_PYLON, facing=200, event=80, cog=186)
collision_box(*DEPOT_PYLON, 220, 220, 1400)
pods = []
for k in range(6):
    px, py = DEPOT_PAD[0] - 500 + (k % 3) * 500, DEPOT_PAD[1] + (-260 if k < 3 else 260)
    decoration('hes_drop_pod', px, py, facing=90, cog=140 + k)
    pods.append((px, py))
# D3's forecourt: pylon P1 (event 81, cog 187) beside the Outer Gate.
decoration('hes_alarm_pylon', *PYLON_P1, facing=180, event=81, cog=187)
collision_box(*PYLON_P1, 220, 220, 1400)

# D4's Pit Stairs door, lit (the integrator's review of build01: the door bay read black): a fire bowl either side.
for side in (-1, 1):
    decoration('hes_fire_bowl_out', DOOR_D4[0] + side * 340, DOOR_D4[1] + 190, facing=0)

# The relay posts (events 20-22; dark until M3), the tablet plinths (events 23-25, the tablets on top).
for event, (x, y) in RELAYS.items():
    decoration('hes_relay_post', x, y, facing=0, event=event)
TABLETS = {23: (cw(2.47, 4.38), 11363), 24: (cw(7.42, 3.48), 11364), 25: (cw(5.45, 7.38), 11365)}
for event, ((x, y), _) in TABLETS.items():
    decoration('hes_tablet_plinth', x, y, facing=0, event=event)

# Thrix's and Tarro's braziers are the DECOR's; the survey markers round the F8 tablet too.

# The derelict swarmship (B1-B2): its two hull halves along a line through the wreck's centre, half buried, with
# invisible collision boxes along them and the ribs' columns (BUILD-READY 4).
WRECK_YAW = math.radians(18)
HULL_SINK = 150
# The Meshy hulls (designs.json): a 2 200 x 942 x 926 high, b 1 900 x 1 074 x 1 201 high, long along the model's x.
hull_parts = [('hes_derelict_hull_a', -1250, 2200, 942, 926), ('hes_derelict_hull_b', 1150, 1900, 1074, 1201)]
for name, offset, length, width, height in hull_parts:
    x, y = WRECK[0] + math.cos(WRECK_YAW) * offset, WRECK[1] + math.sin(WRECK_YAW) * offset
    decoration(name, x, y, facing=math.degrees(WRECK_YAW) + (0 if offset < 0 else 180), sink=HULL_SINK)
    collision_box(x, y, length * 0.92, width * 0.9, height - HULL_SINK, yaw=WRECK_YAW)
    for end in (-0.5, 0.5):
        rx = x + math.cos(WRECK_YAW) * length * end * 1.02
        ry = y + math.sin(WRECK_YAW) * length * end * 1.02
        collision_box(rx, ry, 200, 200, height - HULL_SINK, yaw=WRECK_YAW)
decoration('hes_corpse_kept', WRECK[0] + 900, WRECK[1] - 1300)

# --- Chests (events 30-39), the caches (45, 46) ------------------------------------------------------------------------
CHEST_MODELS = {'chest_c': 'hes_colonial_locker', 'chest_k': 'hes_kreegan_pod_chest', 'chest_a': 'hes_ashrunner_crate',
                'chest_x': 'hes_kcrate_chest'}
loot = []
chest_event = 30
for kind, cx, cy, label, group in detail.PLACES:
    if kind not in CHEST_MODELS:
        continue
    x, y = cw(cx, cy)
    if (round(cx, 2), round(cy, 2)) in [(7.48, 6.2), (7.22, 6.24)]:
        y -= 260                                          # inside its shed's open front
    index = len(loot)
    locked = (cx, cy) == (3.3, 3.32)                      # the Upper Bench's survey locker: Hacking Expert
    decoration(CHEST_MODELS[kind], x, y, facing=int(rng.integers(0, 360)), event=chest_event)
    loot.append({'source_id': f'hesper:out2:chest_{index}', 'source_object_index': index,
                 'source_name': label.split(':')[0].split(',')[0], 'position': {'x': int(x), 'y': int(y),
                                                                               'z': int(height_at(x, y))},
                 'container_id': index, 'kind': 'chest', 'presentation': CHEST_MODELS[kind].replace('hes_', ''),
                 'random_treasure_level': 2, 'treasure_type': 0, 'gold': 300 if locked else 200, 'gold_only': False,
                 'random': True, 'ai_drop': False, 'trap_level': 0, 'should_repopulate': False, 'fixed_items': [],
                 'remove_when_empty': False})
    body = f'evt.OpenChest({index})'
    if locked:
        body = (f'if evt.CheckSkill(const.Skills.Hacking, const.SkillCheck.Expert, 1) then evt.OpenChest({index}) '
                'else evt.StatusText("A colony survey locker, its keypad live. It needs an Expert hacker.") end')
    EVENTS[chest_event] = (label.split(':')[0].split(',')[0], body)
    chest_event += 1
assert chest_event == 40, chest_event
CACHES = {45: (cw(3.30, 3.82), 'hes_colonial_locker', 4,
               'A colony survey locker: two Shield Cells and a Stim.'),
          46: (cw(6.80, 5.60), 'hes_ashrunner_crate', 5,
               'A Kept stash: two Shield Cells and a Stim, hidden under the scrap.')}
for event, ((x, y), model, var, text) in CACHES.items():
    decoration(model, x, y, facing=int(rng.integers(0, 360)), event=event)
    EVENTS[event] = ('Cache', f'if IsAtLeast(MapVar({var}), 1) then evt.StatusText("Empty.") return end '
                     f'SetValue(MapVar({var}), 1) AddValue(InventoryItem(11300), 11300) '
                     f'AddValue(InventoryItem(11300), 11300) AddValue(InventoryItem(11302), 11302) '
                     f'evt.SimpleMessage({json.dumps(text)})')

# --- People and monsters ---------------------------------------------------------------------------------------------
# Actors of the Hesper monster rows the stage installs (hesper_stage/monsters.yml). The design's groups (THE_SCOUR.md
# section 17): 1-5 the camps' guards, 6 the Pens' door Troopers, 7 the depot's garrison, 8 D3's forecourt, 9 and 10
# the Kreegan Road posts, 11 the wreck's gang, 12 the Harvester, 21-25 the camps' Kept, 26 the Pens' yard, 31-35 the
# camps' Overseers, 41 and 42 the depot's pod waves (hidden), 51-55 the freed pairs (hidden), 56 Ansel (hidden);
# 60 the friendly people of the west (Thrix, Tarro); the encounter spawn points 61 and up.
MONSTER_ROWS = {int(row[0]): row for row in (line.split('\t') for line in
                (ROOT / 'design/kreegan_world/data/monster_data.txt').read_text().splitlines()) if row[0].isdigit()}
MONSTER_SIZES = {m['id']: (m['radius'], m['height']) for m in yaml.safe_load(
    (STAGE_INPUT / 'monsters.yml').read_text())['monsters']}
KEPT_A, KEPT_B, TROOPER, VETERAN, OVERSEER = 10060, 10061, 10010, 10011, 10030
DRUDGE, BRUTE, HARVESTER = 10000, 10001, 10104
FREED_MAN, FREED_WOMAN, THRIX_ROW, SCOUT_ROW = 10260, 10261, 10263, 10264
INVISIBLE = 0x00010000
sys.path.insert(0, str(OUT1))
from spawns import Ground, encounter_index  # noqa: E402  (Starport Reach's free-ground test)


def on_lava(placement):
    col, row = int((placement['x'] + 32768) // STEP), int((32768 - placement['y']) // STEP)
    hot = np.pad(lava_mask | (lava_shore > 0), 1)
    return bool(hot[row:row + 3, col:col + 3].any())


colliders_for_ground = [m for m in models] + [colliders]
free_ground = Ground(colliders_for_ground, entities, height_at, road_masks, on_lava, BOUND)
actors = []
moved = []
QUIET = [(cw(*centre), radius, name) for centre, radius, name in detail.QUIET]


def quiet(x, y):
    return all(math.hypot(x - qx, y - qy) >= radius for (qx, qy), radius, _ in QUIET)


def taken(x, y, radius, gap):
    return any(math.hypot(x - a['position']['x'], y - a['position']['y']) < radius + a['radius'] + gap for a in actors)


def find_spot(name, x, y, radius, walker=True, gap=40, hostile=True, rings=24, step=80):
    """The nearest free spot to (x, y): rings of `step` outward (Starport Reach's spawns.py rule)."""
    def ok(px, py):
        return (not hostile or quiet(px, py)) and free_ground.free(px, py, radius, walker) and \
            not taken(px, py, radius, gap)
    if ok(x, y):
        return x, y
    for ring in range(1, rings + 1):
        r = ring * step
        for a in np.linspace(0, 2 * math.pi, 8 + 4 * ring, endpoint=False):
            px, py = x + r * math.cos(a), y + r * math.sin(a)
            if ok(px, py):
                moved.append((name, round(r)))
                return px, py
    raise SystemExit(f'build_out2: no room for {name} near {x:.0f}, {y:.0f}')


def actor(monster, x, y, facing, group, name='', posted=False, z=None, search=True, npc=0, hidden=False,
          walker=True):
    """Place a monster actor at (x, y) facing `facing` (degrees, 0 east, counter-clockwise); a ground actor whose spot
    is taken moves to the nearest free one. Posted actors are placed immobile (their `post` tactic holds the spot)."""
    radius, height = MONSTER_SIZES[monster]
    if z is None and search:
        x, y = find_spot(name or str(monster), x, y, radius, walker=walker,
                         hostile=monster not in (FREED_MAN, FREED_WOMAN, THRIX_ROW, SCOUT_ROW))
    row = MONSTER_ROWS[monster]
    actors.append({'actor_index': len(actors), 'name': name, 'npc_id': npc, 'attributes': INVISIBLE if hidden else 0,
                   'hp': int(row[4]), 'hostility_type': int(row[12]), 'monster_info_id': monster,
                   'monster_id': monster, 'radius': radius, 'height': height,
                   'move_speed': 0 if posted else int(row[13]),
                   'position': {'x': int(round(x)), 'y': int(round(y)),
                                'z': int(round(height_at(x, y) if z is None else z))},
                   'initial_yaw_units': int(round((facing % 360) / 360 * 2048)) % 2048, 'immobile': posted,
                   'sprite_ids': [0, 0, 0, 0], 'sector_id': 0, 'current_action_animation': 0, 'carried_item_id': 0,
                   'group': group, 'ally': 0, 'unique_name_index': 0})
    return actors[-1]


def heading(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


# The five camps (section 7): Kept in the yard round the node, the guard in front of the gate facing the road, the
# Overseer on his perch; the freed pair (hidden) by the yard's brazier; Ansel (hidden) by camp 5's ring.
CAMP_ROSTER = {1: ([KEPT_A] * 7, [TROOPER] * 3), 2: ([KEPT_A] * 5 + [KEPT_B] * 3, [TROOPER] * 2 + [VETERAN]),
               3: ([KEPT_A] * 6 + [KEPT_B] * 4, [TROOPER] * 4), 4: ([KEPT_A] * 4 + [KEPT_B] * 4, [VETERAN] * 3),
               5: ([KEPT_B] * 6, [VETERAN] * 3)}
FREED_NPCS = {1: (9590, 9591), 2: (9592, 9593), 3: (9594, 9595), 4: (9596, 9597), 5: (9598, 9599)}
for n, (kept, guards) in CAMP_ROSTER.items():
    fx = camp_fixtures[n]
    node = np.array(fx['node'], float)
    gate = np.array(fx['gate'], float)
    out = (gate - node) / np.linalg.norm(gate - node)
    side = np.array([-out[1], out[0]])
    for k, monster in enumerate(kept):
        a = 2 * math.pi * k / len(kept) + 0.4
        r = 520 if n == 5 else 700
        x, y = node + np.array([math.cos(a), math.sin(a)]) * r
        actor(monster, x, y, float(rng.uniform(0, 360)), 20 + n, name=f'camp {n} Kept')
    for k, monster in enumerate(guards):
        x, y = gate + out * 420 + side * (k - (len(guards) - 1) / 2) * 260
        actor(monster, x, y, math.degrees(math.atan2(out[1], out[0])), n, name=f'camp {n} guard', posted=True)
    px, py = fx['perch']
    actor(OVERSEER, px, py, heading(fx['perch'], fx['node']), 30 + n, name=f'camp {n} Overseer', posted=True,
          z=fx['perch_z'] + PERCH_DECK, search=False)
    bx, by = fx['brazier']
    man, woman = FREED_NPCS[n]
    actor(FREED_MAN, bx + side[0] * 260, by + side[1] * 260, heading((bx, by), fx['node']), 50 + n,
          name=f'camp {n} freed', posted=True, npc=man, hidden=True)
    actor(FREED_WOMAN, bx - side[0] * 260, by - side[1] * 260, heading((bx, by), fx['node']), 50 + n,
          name=f'camp {n} freed', posted=True, npc=woman, hidden=True)
ring_node = camp_fixtures[5]['node']
ansel = actor(FREED_MAN, ring_node[0] + 700, ring_node[1] + 300, heading((ring_node[0] + 700, ring_node[1] + 300),
                                                                          ring_node), 56, name='Ansel', posted=True,
              npc=9221, hidden=True)

# The Pens' sunken yard: four collared Kept B wandering, the two door Troopers either side of the Pit Stairs door.
for k in range(4):
    a = 2 * math.pi * k / 4 + 0.5
    actor(KEPT_B, PENS_CENTRE[0] + math.cos(a) * 700, PENS_CENTRE[1] + math.sin(a) * 450, float(rng.uniform(0, 360)),
          26, name='Pens Kept')
for side in (-1, 1):
    actor(TROOPER, DOOR_D4[0] + side * 420, DOOR_D4[1] + 300, 90, 6, name='Pens door', posted=True)

# The supply depot's garrison round the pylon and the pad; the pod waves hidden on the pad.
for k, monster in enumerate([TROOPER] * 4 + [VETERAN] * 2):
    a = 2 * math.pi * k / 6
    actor(monster, DEPOT[0] + math.cos(a) * 1100, DEPOT[1] + 400 + math.sin(a) * 900, math.degrees(a), 7,
          name='depot garrison', posted=True)
GARRISON = [a['actor_index'] for a in actors if a['group'] == 7]
for wave, group in ((0, 41), (1, 42)):
    for k in range(3):
        px, py = pods[wave * 3 + k]
        actor(TROOPER, px, py - 200 if wave == 0 else py + 200, 90, group, name=f'pod wave {wave + 1}', hidden=True,
              search=False)

# D3's forecourt, the Kreegan Road's two posts, the wreck's salvage gang.
for side in (-1, 1):
    actor(TROOPER, PYLON_P1[0] + 250, PYLON_P1[1] + side * 260 - 200, 0, 8, name='D3 forecourt', posted=True)
# The Kreegan Road's two patrols (section 7; the engine's waypoint patrols, scene `patrol`): group 9 walks the road
# from the cut to the junction and back (haul road 0), group 10 from the junction to the Slag Gate and back (haul road
# 1), each in its pairs' formation, at their monsters' leashes when they fight.
ROAD_PATROLS = {9: [(2880.0, 18400.0), (2880.0, 15840.0), (2592.0, 12384.0), (2880.0, 15840.0)],
                10: [(2592.0, 12384.0), (8064.0, 11635.0), (12096.0, 13709.0), (14112.0, 16000.0), (12096.0, 13709.0),
                     (8064.0, 11635.0)]}


def patrol(group, dx, dy):
    return [[int(round(x + dx)), int(round(y + dy)), int(round(height_at(x + dx, y + dy)))]
            for x, y in ROAD_PATROLS[group]]


for k, monster in enumerate([TROOPER, TROOPER, VETERAN, VETERAN]):
    x, y = cw(4.62, 0.92)
    dx, dy = (k % 2) * 300 - 150, -(k // 2) * 260
    actor(monster, x + dx, y + dy, 270, 9, name='Kreegan Road, the cut')['patrol'] = patrol(9, dx, dy)
for k, monster in enumerate([TROOPER] * 3 + [VETERAN]):
    x, y = cw(4.7, 1.8)
    dx, dy = (k % 2) * 320 - 160, -(k // 2) * 280
    actor(monster, x + dx, y + dy, 270, 10, name='Kreegan Road, the junction')['patrol'] = patrol(10, dx, dy)
for k, monster in enumerate([DRUDGE] * 4 + [BRUTE] * 2):
    a = 2 * math.pi * k / 6
    actor(monster, WRECK[0] + math.cos(a) * 1900, WRECK[1] + math.sin(a) * 1500, math.degrees(a) + 180, 11,
          name='wreck gang')

# The Harvester on the pit floor by the central hopper (posted: its post tactic, leash 2 400).
hx, hy = cw(*terrain.PIT)
harvester = actor(HARVESTER, hx + 900, hy - 600, 135, 12, name='The Harvester', posted=True)
HARVESTER_INDEX = harvester['actor_index']

# The friendly people of the west: Thrix outside his cave, Tarro outside his lean-to.
thrix = actor(THRIX_ROW, THRIX[0] + 650, THRIX[1] - 150, 250, 60, name='Thrix', posted=True, npc=9509)
tarro = actor(SCOUT_ROW, TARRO[0] - 700, TARRO[1] + 350, 180, 60, name='Tarro', posted=True, npc=9514)

# The encounter spawn points (SPAWNS: slot, cells, count range): on free ground off the roads, in their quiet rings'
# rule; the groups 61 and up, one a point.
spawns = []
for k, (slot, sx, sy, count) in enumerate(detail.SPAWNS):
    x, y = cw(sx, sy)
    flier = slot == 3
    x, y = find_spot(f'spawn {k}', x, y, 260, walker=not flier, gap=200)
    if not flier:
        road, hauled, ruts = road_masks(np.array([x]), np.array([y]))
        if road[0] or hauled[0]:
            x, y = find_spot(f'spawn {k} off road', x + 500, y, 260, walker=True, gap=200)
    spawns.append({'spawn_index': len(spawns), 'position': {'x': round(x), 'y': round(y), 'z': round(height_at(x, y))},
                   'radius': 128, 'type_id': 3, 'index': encounter_index(slot, None), 'attributes': 0,
                   'group': 61 + k})

# R5 Ashkite wildlife: two flocks over the spoil on the Great Pit rim; append to preserve existing indices.
for flock, angle in enumerate((25, 205)):
    a = math.radians(angle)
    cx, cy = (PIT_CENTRE[0] + (PIT_RIM_R + 500) * math.cos(a),
              PIT_CENTRE[1] + (PIT_RIM_R + 500) * math.sin(a))
    for k in range(5):
        t = k * 2 * math.pi / 5
        actor(10310, cx + 380 * math.cos(t), cy + 380 * math.sin(t), angle + 180, 150 + flock,
              name=f'Ashkite Great Pit rim flock {flock + 1}', walker=False)

# --- Arrivals and the party start ------------------------------------------------------------------------------------
ARRIVALS = {
    'west': (WEST_ARRIVAL, 0), 'north': (NORTH_ARRIVAL, 270),
    'tunnel_arrival': (TUNNEL_ARRIVAL, 0), 'd03_return': (D3_RETURN, 0), 'd04_return': (D4_RETURN, 90),
    'd08_return': (D8_RETURN, 270)}
arrivals = {key: {'position': [round(x), round(y), round(height_at(x, y))], 'direction_degrees': facing}
            for key, ((x, y), facing) in ARRIVALS.items()}
for index, entity in enumerate(entities):
    entity['entity_index'] = index + 1
wx, wy = WEST_ARRIVAL
entities.insert(0, {'entity_index': 0, 'name': 'Party Start', 'decoration_list_id': 14, 'ai_attributes': 2,
                    'position': {'x': int(wx), 'y': int(wy), 'z': int(height_at(wx, wy))}, 'facing': 0,
                    'event_id_primary': 0, 'event_id_secondary': 0, 'variable_primary': 0, 'variable_secondary': 0,
                    'special_trigger': 0, 'initial_decoration_flag': 2})


def smoke(x, y, z):
    entities.append({'entity_index': len(entities), 'name': 'smoke', 'decoration_list_id': 22, 'ai_attributes': 0,
                     'position': {'x': int(x), 'y': int(y), 'z': int(z)}, 'facing': 0, 'event_id_primary': 0,
                     'event_id_secondary': 0, 'variable_primary': 0, 'variable_secondary': 0, 'special_trigger': 0,
                     'initial_decoration_flag': 0})


for x, y, top in stack_points:                            # the stacks smoke
    smoke(x, y, top + 60)

# --- Events -----------------------------------------------------------------------------------------------------------


def dungeon_entry(project, map_file, arrival, missing):
    """The Lua that moves the party to a Hesper map's arrival (its semantic record), or a status text while the map
    is not built."""
    path = ROOT / 'level_generation/projects' / project / 'source' / (Path(map_file).stem + '.semantic.json')
    if not path.exists():
        return f'evt.StatusText({json.dumps(missing)})'
    a = json.loads(path.read_text())['arrivals'][arrival]
    x, y, z = a['position']
    direction = round(a['direction_degrees'] / 360 * 2048) % 2048
    return f'evt.MoveToMap({x}, {y}, {z}, {direction}, 0, 0, 0, 0, "{map_file}")'


def aster(before, after=None, after_bit=None):
    """A relay post (P4's ASTER): dead before M3 (100003) and after Tear it out (100034)."""
    dead = 'evt.StatusText("A dead relay post; something hums inside.")'
    text = f'evt.SimpleMessage({json.dumps("Aster, through the relay: " + chr(34) + before + chr(34))})'
    if after:
        text = (f'if IsQBitSet(QBit({after_bit})) then evt.SimpleMessage('
                f'{json.dumps("Aster, through the relay: " + chr(34) + after + chr(34))}) else {text} end')
    return f'if IsQBitSet(QBit(100034)) or not IsQBitSet(QBit(100003)) then {dead} else {text} end'


EVENTS.update({
    10: ('Signpost', 'evt.SimpleMessage("Colony survey post: north, Service Tunnel 4 and the west workings; east, the '
                     'Great Pit. A Hesperian hand added a note beneath it. \\"Tarro\'s here. Water and Cells. - T.\\"")'),
    11: ('Signpost', 'evt.SimpleMessage("Colony survey post: east, the Great Pit; south-west, Shaft 9. Scratched under '
                     'it. \\"Shaft 9 is a devil camp now. Stay off the ridge.\\"")'),
    12: ('Signpost', 'evt.SimpleMessage("Colony Safety Notice: open-cast pit. Benches are not walkways; use the ramp. '
                     'A note is scratched below. \\"Something big digs down there. It stops sometimes.\\"")'),
    13: ('Signpost', 'evt.SimpleMessage("Colony survey post: north, the Foundry road; south, the Great Pit. Scratched '
                     'over it. \\"North is their city. Don\'t.\\"")'),
    20: ('Aster relay post', aster("The Quarry Outpost. My makers cut stone here for the starport. The devils made it "
                                   "a fort. Two pylons watch the ground, one on the gate and one in the yard; a "
                                   "watched party brings the pods down. Kill the pylons' eyes or keep to cover. Krav "
                                   "sits on his roost above the yard. While he lives, his troopers' shields come back "
                                   "fast. Kill him first.", "The Quarry is silent. The salvage crews can return.", 100024)),
    21: ('Aster relay post', aster("The Labor Pens. They keep my people in cages in the pit and make them fight for "
                                   "their keepers with collars on. The collars answer to a control room inside. Open "
                                   "it, and the cages fight for you. Every one you kill in a collar was a prisoner. "
                                   "Remember that.", "The Pens' cages stand open. My people are going home.", 100027)),
    22: ('Aster relay post', aster("The Foundry holds my makers' fabricators, black with soot and still working, for them. "
                                   "Molten slag runs in the floor's channels; the coolant valves stop it for a while, "
                                   "if you have the hands for them. And there are nobles inside, and their shields laugh "
                                   "at your old weapons, so bring theirs.")),
    50: ('Quarry Outpost', dungeon_entry('hesper_d03', 'hes_d03.blv', 'd03_outer_gate',
                                         'The stolen Ancient blast door is sealed.')),
    51: ('Labor Pens', dungeon_entry('hesper_d04', 'hes_d04.blv', 'd04_pit_stairs',
                                     'The orange seal on the resin doorway holds fast.')),
    53: ('The Foundry', dungeon_entry('hesper_d08', 'hes_d08.blv', 'd08_slag_gate',
                                      'The Slag Gate is closed.')),
    300: ("Thrix's stall", 'if IsQBitSet(QBit(100105)) then evt.EnterHouse(9300) else evt.StatusText("An empty '
                           'counter of scrap at a cave mouth. Someone lives here.") end'),
    301: ("Tarro's lean-to", 'evt.EnterHouse(9301)'),
})
undervault = json.loads((ROOT / 'level_generation/projects/hesper_undervault/source/hes_undervault.semantic.json')
                        .read_text())['arrivals']['water_works']
uw = undervault['position']
EVENTS[52] = ('The tunnel mouth', 'if not IsQBitSet(QBit(100102)) then evt.StatusText("An Ancient service shutter, '
              'sealed from the far side. Somewhere behind it, water drips.") return end '
              'if not IsQBitSet(QBit(100420)) then SetQBit(QBit(100420)) SetAutonote(10102) end '
              f'evt.MoveToMap({uw[0]}, {uw[1]}, {uw[2]}, {round(undervault["direction_degrees"] / 360 * 2048) % 2048}, '
              '0, 0, 0, 0, "hes_undervault.blv")')
for event, (_, item) in TABLETS.items():
    var = 20 + event - 23
    EVENTS[event] = ('Colony log tablet', f'if IsAtLeast(MapVar({var}), 1) then evt.StatusText("An empty plinth; its '
                     f'slab is gone.") return end SetValue(MapVar({var}), 1) if not HasItem({item}) then '
                     f'AddValue(InventoryItem({item}), {item}) end evt.StatusText("A crystal slab, its lines faintly '
                     'blue: a colony log.")')
for n in range(1, 6):
    EVENTS[70 + n] = (f'Collar node, camp {n}', f'if IsQBitSet(QBit({100114 + n})) then evt.StatusText("The node is '
                      'dark.") elseif evt.CheckSkill(const.Skills.Hacking, const.SkillCheck.Novice, 1) then '
                      f'FreeCamp({n}) else evt.StatusText("A collar node, its sockets glowing violet-red. A hacker '
                      'could open it; so would the death of the Overseer who holds its key.") end')
for event, bit, cog in ((80, 100400, 186), (81, 100401, 187)):
    EVENTS[event] = ('Alarm pylon', f'if IsQBitSet(QBit({bit})) then evt.StatusText("The eye is dark.") elseif '
                     'evt.CheckSkill(const.Skills.Hacking, const.SkillCheck.Novice, 1) then '
                     f'SetQBit(QBit({bit})) evt.SetSprite({cog}, 1, "hes_alarm_pylon_off") '
                     'evt.StatusText("The eye dims to a cinder.") else evt.StatusText("The pylon\'s eye turns slowly. '
                     'A hacker could kill it.") end')
EVENTS[156] = ('The depot\'s alarm', 'Alarm()')
EVENTS[157] = ('The second wave', 'SecondWave()')

KEPT_GROUP_OF = {a['actor_index']: a['group'] for a in actors if a['group'] in range(21, 27)}
# Every evt.SetSprite is literal (the lighting bake reads them statically, tools/lighting/bake_decorations.py): each
# camp's fixtures freed and held, the pods opened.
CAMP_SPRITES = ''.join(
    f'CAMP_FIXTURES[{n}] = {{freed = function() evt.SetSprite({170 + n}, 1, "hes_collar_node_off") '
    f'evt.SetSprite({175 + n}, 1, "hes_fire_bowl_out_off") evt.SetSprite({180 + n}, 1, "hes_brazier_out") end, '
    f'held = function() evt.SetSprite({180 + n}, 0, "hes_brazier_out") end}}\n' for n in range(1, 6))
POD_SPRITES = ('local function OpenPods(wave)\n    if wave == 1 then '
               + ' '.join(f'evt.SetSprite({140 + k}, 1, "hes_drop_pod_open")' for k in range(3)) + '\n    else '
               + ' '.join(f'evt.SetSprite({143 + k}, 1, "hes_drop_pod_open")' for k in range(3)) + ' end\nend\n')
LUA_HEAD = f'''-- Generated by level_generation/projects/hesper_out2/build_out2.py (THE_SCOUR.md section 17).
local HARVESTER = {HARVESTER_INDEX}
local GARRISON = {{{', '.join(str(i) for i in GARRISON)}}}
local KEPT_GROUP = {{{', '.join(f'[{i}] = {g}' for i, g in sorted(KEPT_GROUP_OF.items()))}}}

local function bit(id) return IsQBitSet(QBit(id)) end
local CAMP_FIXTURES = {{}}
{CAMP_SPRITES}{POD_SPRITES}
-- Free camp n (events 71-75 or its Overseer's death, 151-155): S6's camp bit, the collars off, the node and the
-- perch's bowls dark, the yard's brazier lit, the freed pair shown (camp 5: Ansel too), reputation -2 once.
function FreeCamp(n)
    if bit(100114 + n) then return end
    SetQBit(QBit(100114 + n))
    evt.SetMonGroupBit(20 + n, MonsterBits.Hostile, false)
    CAMP_FIXTURES[n].freed()
    evt.SetMonGroupBit(50 + n, MonsterBits.Invisible, false)
    if n == 5 then evt.SetMonGroupBit(56, MonsterBits.Invisible, false) end
    SetValue(MapVar(10 + n), 1)
    if not bit(100720 + n) then
        SetQBit(QBit(100720 + n))
        AddValue(ReputationInCurrentLocation, -2)
    end
    local all = true
    for k = 1, 5 do
        if not bit(100114 + k) then all = false end
    end
    if all and not bit(100106) then
        SetQBit(QBit(100106))
        SetAutonote(10105)
    end
    evt.SimpleMessage("The collars fall open. The camp goes quiet, then someone laughs.")
end

-- The depot's alarm (event 156) and its second wave (event 157): the pods on the pad open, the hidden Troopers land.
function Alarm()
    if bit(100405) then return end
    SetQBit(QBit(100405))
    OpenPods(1)
    evt.SetMonGroupBit(41, MonsterBits.Invisible, false)
    SetValue(MapVar(2), 1)
    SetAutonote(10103)
    evt.StatusText("A horn howls from the depot's pylon. Something streaks down out of the smoke.")
end

function SecondWave()
    OpenPods(2)
    evt.SetMonGroupBit(42, MonsterBits.Invisible, false)
    SetValue(MapVar(2), 0)
end

local function onLoad()
    for n = 1, 5 do
        local freed = bit(100114 + n)
        evt.SetMonGroupBit(20 + n, MonsterBits.Hostile, not freed)
        evt.SetMonGroupBit(50 + n, MonsterBits.Invisible, not freed)
        if freed then
            CAMP_FIXTURES[n].freed()
            -- The camp's other Kept left for the Undervault after the freeing visit.
            if IsAtLeast(MapVar(10 + n), 1) then evt.SetMonGroupBit(20 + n, MonsterBits.Invisible, true) end
        else
            CAMP_FIXTURES[n].held()
        end
    end
    evt.SetMonGroupBit(56, MonsterBits.Invisible, not bit(100119))
    evt.SetMonGroupBit(26, MonsterBits.Hostile, not bit(100027))
    if not bit(100404) then
        evt.SetActorBehavior(HARVESTER, "hesper/bosses/harvester")
        evt.SetMonsterItem(HARVESTER, 11476)
    end
    if bit(100400) then evt.SetSprite(186, 1, "hes_alarm_pylon_off") end
    if bit(100401) then evt.SetSprite(187, 1, "hes_alarm_pylon_off") end
    evt.SetMonGroupBit(41, MonsterBits.Invisible, not bit(100405))
    evt.SetMonGroupBit(42, MonsterBits.Invisible, not bit(100405))
    if bit(100405) then
        OpenPods(1)
        OpenPods(2)
    end
end
'''
EVENTS[1] = ('The Scour on load', 'ScourOnLoad()')
EVENTS[2] = ('First visit', 'if not IsAtLeast(MapVar(7), 1) then SetValue(MapVar(7), 1) SetAutonote(10100) end')
LUA_TAIL = f'''
ScourOnLoad = onLoad

-- Event 4, every real second (30 game seconds): the depot's watch while its pylon is up, then the second wave's count.
RegisterMapTimerEvent(4, 30, function()
    if bit(100405) then
        if IsAtLeast(MapVar(2), 1) then
            AddValue(MapVar(2), 1)
            if IsAtLeast(MapVar(2), 20) then SecondWave() end
        end
        return
    end
    if bit(100400) then return end
    local near = false
    for _, index in ipairs(GARRISON) do
        if not evt.CheckMonstersKilled(ActorKillCheck.ActorIdOe, index, 0, false)
            and evt.IsMapActorWithinPartyDistance(index, 3000) then
            near = true
            break
        end
    end
    local _, red = evt.GetEnemyDetectorState()
    if near and red then
        AddValue(MapVar(1), 1)
        if IsAtLeast(MapVar(1), 3) then Alarm() end
    else
        SetValue(MapVar(1), 0)
    end
end, "The depot's watch", "", 30)

-- 150: the Harvester dead: its core drops with the body (its carried item, set on load).
RegisterMonsterKilledHook(150, "The Harvester", function()
    if bit(100404) or not evt.CheckMonstersKilled(ActorKillCheck.Group, 12, 0, false) then return end
    SetQBit(QBit(100404))
    SetAutonote(10101)
    evt.SimpleMessage("The Harvester grinds to a stop. In its torn housing something white and gold still glows: a lander core.")
end)
-- 151-155: a camp's Overseer dead frees his camp.
for n = 1, 5 do
    RegisterMonsterKilledHook(150 + n, "A camp's Overseer", function()
        if not bit(100114 + n) and evt.CheckMonstersKilled(ActorKillCheck.Group, 30 + n, 0, false) then FreeCamp(n) end
    end)
end
-- 160: the first collared Kept killed (the reputation is the engine's kill rule).
RegisterMonsterKilledHook(160, "A collar dims", function()
    local group = KEPT_GROUP[evt.GetHookContext().actorIndex]
    if group == nil or IsAtLeast(MapVar(6), 1) then return end
    if group == 26 and bit(100027) then return end
    if group ~= 26 and bit(100094 + group) then return end
    SetValue(MapVar(6), 1)
    evt.StatusText("A collar dims. The Hesperians will hear of this.")
end)
'''

# --- Write the sources, build with the editor, verify -----------------------------------------------------------------
if SOURCE.exists():
    shutil.rmtree(SOURCE)
(SOURCE / 'models').mkdir(parents=True)
bmodel_records = []
interactive = []
if colliders.faces:
    models.append(colliders)
for index, model in enumerate(models):
    write_obj(model, SOURCE / 'models' / f'{model.name}.obj', SIZES)
    textures = sorted({texture for _, texture, _ in model.faces})
    bmodel_records.append({'geometry_id': f'hes_out2:{model.name}', 'runtime_bmodel_index': index,
                           'source': {'asset_path': str(SOURCE / 'models' / f'{model.name}.obj'), 'scale': 128,
                                      'merge_coplanar_faces': False, 'preserve_source_winding': True},
                           'materials': {'default_texture': textures[0], 'remaps': {t: t for t in textures}}})
    for event, faces in model.events.items():
        if not event:
            continue
        for face in faces:
            interactive.append({'bmodel_index': index, 'face_index': face, 'legacy_attributes': 0x2000000,
                                'cog_number': 0, 'cog_triggered_number': event, 'cog_trigger': 0})
    for face in model.invisible:                        # FaceAttribute::Invisible: blocks, not drawn
        interactive.append({'bmodel_index': index, 'face_index': face, 'legacy_attributes': 0x2000,
                            'cog_number': 0, 'cog_triggered_number': 0, 'cog_trigger': 0})
(SOURCE / 'hes_out2.geometry.yml').write_text(json.dumps({'version': 1, 'map_file': MAP, 'bmodels': bmodel_records},
                                                         indent=1) + '\n')
(SOURCE / 'hes_out2.terrain.yml').write_text(json.dumps({
    'version': 1, 'map_file': MAP, 'height_map_hex': height_bytes.tobytes().hex().upper(),
    'tile_map_hex': tile_bytes.tobytes().hex().upper(),
    'attribute_map_hex': attribute_bytes.tobytes().hex().upper()}) + '\n')

# Ground items: sprite objects carrying the item (the object of the item's sprite index, as Starport Reach's).
staged_item_rows = {int(row[0]): row for row in (line.split('\t') for line in
                    (STAGE / 'worlds/hesper/data_tables/items.txt').read_text().splitlines()) if row[0].isdigit()}
engine_item_rows = {int(row[0]): row for row in (line.split('\t') for line in
                    (ROOT / 'assets_dev/engine/data_tables/items.txt').read_text(encoding='latin-1').splitlines())
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


# The colony log tablets IV-VI on their plinths (P4's ITEM_PLACEMENT: "Ground, on a plinth").
plinth_top = model_bounds('hes_tablet_plinth')[1][1]
for event, ((x, y), item) in TABLETS.items():
    ground_item(item, x, y, height_at(x, y) + plinth_top + 2)
# The salvage (section 15): four pieces at each of five spots, the Engram Shard on the Lower Bench.
SALVAGE = {(3.6, 2.5): [11350, 11350, 11351, 11351], (4.4, 3.42): [11350, 11350, 11350, 11351, 11330],
           (1.55, 1.62): [11350, 11350, 11350, 11351], (4.3, 6.35): [11350, 11350, 11351, 11351],
           (5.85, 0.9): [11350, 11350, 11351, 11351]}
salvage_spots = {}
for (cx, cy), items in SALVAGE.items():
    x0, y0 = cw(cx, cy)
    spots = []
    for k, item in enumerate(items):
        a = 2 * math.pi * k / len(items)
        x, y = x0 + math.cos(a) * 160, y0 + math.sin(a) * 160
        ground_item(item, x, y, height_at(x, y) + 4)
        spots.append([round(x), round(y)])
    salvage_spots[f'{cx},{cy}'] = spots
# The gold piles (LOOT_RULES, medium): 1 000 by camp 3's dead Kept, 800 on the Lower Bench, 1 200 at the wreck, 1 500 at
# the slag pond's edge, 900 on the Kreegan Road by a dead scout.
GOLD = [((4.70, 4.62), 1000), ((4.30, 3.30), 800), ((1.80, 1.30), 1200), ((5.10, 1.45), 1500), ((4.55, 1.40), 900)]
for (cx, cy), amount in GOLD:
    x, y = cw(cx, cy)
    ground_item(188 if amount <= 1000 else 189, x, y, height_at(x, y) + 4, gold=amount)
decoration('hes_corpse_colonist', *cw(4.60, 1.40), facing=80)       # the dead scout by the Kreegan Road

reference = yaml.safe_load((ROOT / 'assets_dev/worlds/mm8/maps/out02.scene.yml').read_text())
environment = reference['environment']
environment['tile_set_lookup_indices'] = LOOKUPS
scene = {'format_version': 1, 'kind': 'outdoor_scene', 'source': {'geometry_file': MAP},
         'environment': environment, 'terrain': {'attribute_overrides': [], 'footstep_sound_overrides': []},
         'bmodel_faces': {'interactive_faces': interactive}, 'entities': entities, 'spawns': spawns,
         'initial_state': {'location': {'respawn_count': 0, 'last_respawn_day': 0, 'reputation': 0,
                                        'alert_status': 0},
                           'face_attribute_overrides': [], 'actors': actors, 'sprite_objects': ground_items,
                           'chests': [],
                           'variables': {'map': [0] * 75, 'decor': [0] * 125}},
         'loot_containers': loot, 'world_items': []}
for index, entity in enumerate(entities):
    entity['entity_index'] = index
(SOURCE / 'hes_out2.scene.yml').write_text(json.dumps(scene, indent=1) + '\n')
package = {'format_version': 1, 'kind': 'outdoor_map_package', 'package_id': 'hesper:the_scour',
           'display_name': 'The Scour', 'map_file': MAP, 'scene_file': 'hes_out2.scene.yml',
           'geometry_metadata_file': 'hes_out2.geometry.yml', 'terrain_metadata_file': 'hes_out2.terrain.yml',
           'script_module': 'maps/hes_out2.lua', 'map_stats_id': MAP_ID, 'redbook_track': 0,
           'environment_name': 'grassland', 'is_top_level_area': True,
           'outdoor_bounds': {'enabled': True, 'min_x': -BOUND, 'max_x': BOUND, 'min_y': -BOUND, 'max_y': BOUND}}
(SOURCE / 'hes_out2.map.yml').write_text(json.dumps(package, indent=1) + '\n')

if TREE.exists():
    shutil.rmtree(TREE)
for folder in ['maps', 'events/maps', 'terrain_materials', 'terrain_decorations', 'behaviors/bosses']:
    (TREE / folder).mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='hes-out2-') as directory:
    temp = Path(directory)
    for name in ['hes_out2.map.yml', 'hes_out2.scene.yml', 'hes_out2.geometry.yml', 'hes_out2.terrain.yml']:
        shutil.copy2(SOURCE / name, temp / name)
    log = PROJECT / 'build.log'
    with log.open('w') as stream:
        subprocess.run([str(ROOT / 'build/editor/openyamm-editor'), '--asset-root', str(STAGE), '--headless-build-map',
                        str(temp / 'hes_out2.map.yml')], check=True, stdout=stream, stderr=subprocess.STDOUT)
    shutil.copy2(temp / MAP, TREE / 'maps' / MAP)
shutil.copy2(SOURCE / 'hes_out2.scene.yml', TREE / 'maps/hes_out2.scene.yml')
if (PROJECT / 'work/hes_out2.bmp').exists():            # the minimap (finish_minimap.py) survives a rebuild of the map
    (TREE / 'icons_x2').mkdir(exist_ok=True)
    shutil.copy2(PROJECT / 'work/hes_out2.bmp', TREE / 'icons_x2/hes_out2.bmp')
shutil.copy2(PROJECT / 'harvester.lua', TREE / 'behaviors/bosses/harvester.lua')

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

# The edge contracts, checked on the built heights (within 32 of the contract along the crossings).
for y in range(-2592 - 1500, -2592 + 1501, 256):
    for x in (-BOUND, -BOUND + 512, -BOUND + 1024, -BOUND + 1536):
        want = float(np.interp(y, profile_y, profile_h))
        assert abs(height_at(x, y) - want) <= 32, ('west edge', x, y, height_at(x, y), want)
for x in range(1880, 3881, 250):
    for y in (BOUND, BOUND - 512, BOUND - 1024, BOUND - 1536):
        assert abs(height_at(x, y) - terrain.EDGE_NORTH) <= 32, ('north gap', x, y, height_at(x, y))

# Where a scenario stands to click an event face: 240 out from the face's centre along its normal, facing it.
door_poses = {}
for model in models:
    for event, faces in model.events.items():
        if event:
            points = np.array(model.faces[faces[0]][0])
            centre = points.mean(0)
            n = normal([tuple(p) for p in points])
            px, py = centre[0] + n[0] * 240, centre[1] + n[1] * 240
            door_poses[event] = [round(px), round(py), round(height_at(px, py)), round(math.atan2(-n[1], -n[0]), 4)]

# Lua.
text = LUA_HEAD
text += 'SetMapMetadata({onLoad = {1, 2}, onLeave = {}, openedChestIds = {'
text += ', '.join(f'[{30 + index}] = {{{index}}}' for index in range(len(loot))) + '}})\n'
for event in sorted(EVENTS):
    title, body = EVENTS[event]
    text += f'RegisterEvent({event}, {json.dumps(title)}, function() {body} end, {json.dumps(title)})\n'
text += LUA_TAIL
(TREE / 'events/maps/hes_out2.lua').write_text(text)

# Ground materials: the slot file (the design's draft, the new materials' tints set from their library colours) and
# the weights.
slot = yaml.safe_load((DESIGN / 'terrain_materials.yml').read_text())
hesper_library = yaml.safe_load((STAGE_INPUT / 'terrain_library.yml').read_text())['materials']
targets = {'slag': (58, 44, 40), 'seam': (60, 46, 42)}       # the seam's crust; its veins glow (library emissive)
for layer in slot['layers']:
    if layer['name'] in targets:
        mean = np.array(hesper_library[layer['library']]['mean_color'])
        layer['tint'] = [round(float(v), 4) for v in np.array(targets[layer['name']]) / 255.0 / mean]
# The pavers dulled toward the spoil dust (the integrator's review of build01), darker than Starport Reach's clean
# tint (0.917, 1.062, 1.244): the crossing shows a change of tone where the dust begins.
next(layer for layer in slot['layers'] if layer['name'] == 'plating')['tint'] = [0.66, 0.68, 0.74]
order = [layer['name'] for layer in slot['layers']]
slot['layers'] = [next(layer for layer in slot['layers'] if layer['name'] == name) for name in LAYERS + ['rock']]
slot['weights'] = ['hes_out2_weights0.png', 'hes_out2_weights1.png']
slot['weighted_layers'] = len(LAYERS)
slot['slope'] = {'layer': len(LAYERS), 'start': slot['slope']['start'], 'end': slot['slope']['end']}
(TREE / 'terrain_materials/hes_out2.yml').write_text(
    '# Generated by level_generation/projects/hesper_out2/build_out2.py from design/kreegan_world/zone2/'
    'terrain_materials.yml.\n# weights: RGBA images covering the 128x128 cell map, channels in layer order (north '
    'row first).\n' + yaml.safe_dump(slot, sort_keys=False))
for index in range(2):
    Image.fromarray(quantized[..., index * 4:index * 4 + 4], 'RGBA').save(
        TREE / f'terrain_materials/hes_out2_weights{index}.png', optimize=True)

# Plants: the ash tufts on the ash only (the west edge, the canyon, the dunes); spoil grows nothing (K13).
shutil.copy2(ROOT / 'design/kreegan_world/art/ground_plants/hesper_plants_v1.png',
             TREE / 'terrain_decorations/hesper_plants_v1.png')
shutil.copy2(OUT1 / 'families.yml', TREE / 'terrain_decorations/families.yml')
# None on the roads (the plant rule keys the tile texture, which the road layers paint over): a density mask, 0 on
# the cells within reach of a road, one value per cell centre, north row first.
mask_x, mask_y = np.meshgrid((np.arange(GRID) - 64) * STEP + STEP / 2, (64 - np.arange(GRID)) * STEP - STEP / 2)
off_road = (segment_distance_any(paved, mask_x, mask_y) > 350 + 450) & \
    (segment_distance_any(haul + rim, mask_x, mask_y) > 300 + 450) & (segment_distance_any(tracks, mask_x, mask_y) > 500)
Image.fromarray(np.where(off_road, 255, 0).astype(np.uint8), 'L').save(
    TREE / 'terrain_decorations/hes_out2_density.png', optimize=True)
(TREE / 'terrain_decorations/hes_out2.yml').write_text(yaml.safe_dump({
    'version': 2, 'families_file': 'families.yml', 'seed': 1023, 'near_distance': 3072, 'minimum_normal_z': 0.7,
    'density_mask': 'hes_out2_density.png',
    'density_variation': 0.9, 'patch_size': 1024, 'tall_grass_chance': 0.0, 'tall_grass_scale': 1.0,
    'rules': [{'texture': 'voltyl', 'family': 'ash_tufts', 'density': 0.65, 'tint': [1.0, 1.0, 1.0]}]},
    sort_keys=False))

# The ground's colour as it reads in the game, for the minimap (as Starport Reach's): each layer's design colour with
# its photo's light and dark detail, by the weights, rock on steep slopes, the molten slag glowing.
library = yaml.safe_load((ROOT / 'assets_dev/engine/terrain_materials/library.yml').read_text())['materials']
library.update(hesper_library)
DESIGN_COLOURS = {name: terrain.MATERIALS[name][0] for name in LAYERS + ['rock']}


def layer_colour(layer):
    with Image.open(ROOT / 'assets_source/engine/terrain_materials' / layer['library'] / 'albedo_height.png') as image:
        tile_size = max(2, int(round(layer['repeat'] / units)))
        tile = np.asarray(image.convert('L').resize((tile_size, tile_size), Image.BOX), dtype=np.float32)
    detail_ = (tile / max(tile.mean(), 1.0)) ** 0.6
    tile = (np.array(DESIGN_COLOURS[layer['name']], dtype=np.float32) / 255) ** 2.2 * detail_[..., None]
    reps = size // tile_size + 1
    return np.tile(tile, (reps, reps, 1))[:size, :size]


colour = np.zeros((size, size, 3), dtype=np.float32)
for index, layer in enumerate(slot['layers'][:len(LAYERS)]):
    colour += field[..., index:index + 1] * layer_colour(layer)
texel_heights = ndimage.gaussian_filter(ndimage.zoom(heights, size / GRID, order=3), 6)
gy_, gx_ = np.gradient(texel_heights, units)
steep = np.clip((np.hypot(gx_, gy_) - slot['slope']['start']) / (slot['slope']['end'] - slot['slope']['start']), 0,
                1)[..., None]
colour = colour * (1 - steep) + layer_colour(slot['layers'][len(LAYERS)]) * steep
lava_texels = np.repeat(np.repeat(lava_mask, TEXELS, 0), TEXELS, 1)[..., None]
colour = np.where(lava_texels, (np.array([255, 110, 20], np.float32) / 255) ** 2.2, colour)
(PROJECT / 'work').mkdir(exist_ok=True)
for placement in model_placements:
    placement['model'] = str(model_file(placement['name']))
    placement['scale'] = model_scale(placement['name'])[0]
(PROJECT / 'work/minimap_models.json').write_text(json.dumps(model_placements, indent=1) + '\n')
Image.fromarray(np.clip(colour ** (1 / 2.2) * 255 + 0.5, 0, 255).astype(np.uint8), 'RGB').save(
    PROJECT / 'work/ground_colour.png')

# Previews and the build record (every arrival and door the dungeons, the Undervault and the scenarios read).
review = PROJECT / 'review'
review.mkdir(exist_ok=True)
low, high = heights.min(), heights.max()
Image.fromarray(((heights - low) / (high - low) * 255).astype(np.uint8), 'L').resize((512, 512)).save(
    review / 'heights.png')
Image.fromarray(np.clip(colour[::4, ::4] ** (1 / 2.2) * 255, 0, 255).astype(np.uint8), 'RGB').save(
    review / 'ground.png')
report = {'map': MAP, 'map_id': MAP_ID, 'bmodels': len(models), 'faces': sum(len(m.faces) for m in models),
          'entities': len(entities), 'actors': len(actors), 'spawn_points': len(spawns), 'chests': len(loot),
          'events': sorted(EVENTS), 'height_range': [int(heights.min()), int(heights.max())],
          'arrivals': arrivals,
          'camps': {str(n): {'level': round(camp_levels[n]), **{k: [round(v) for v in fx[k]] if k in ('node', 'perch',
                                                                                                       'brazier', 'gate')
                                                               else fx[k] for k in ('node', 'perch', 'perch_z',
                                                                                    'brazier', 'gate')}}
                    for n, fx in camp_fixtures.items()},
          'actors_by_group': {str(g): [a['actor_index'] for a in actors if a['group'] == g]
                              for g in sorted({a['group'] for a in actors})},
          'harvester': HARVESTER_INDEX, 'garrison': GARRISON, 'thrix': thrix['actor_index'],
          'tarro': tarro['actor_index'], 'ansel': ansel['actor_index'],
          'pylons': {'depot': list(DEPOT_PYLON), 'p1': list(PYLON_P1)}, 'pods': [list(map(round, p)) for p in pods],
          'tablets': {str(e): [round(v) for v in xy] for e, (xy, _) in TABLETS.items()},
          'relays': {str(e): list(xy) for e, xy in RELAYS.items()}, 'salvage': salvage_spots,
          'chest_positions': [[c['position']['x'], c['position']['y']] for c in loot],
          'door_poses': door_poses, 'stacks': [list(map(round, s)) for s in stack_points],
          'piers': [[round(x), round(y), kind] for x, y, kind in piers],
          'wreck': [round(v) for v in WRECK], 'moved': moved, 'dressing': dressing,
          'lava_cells': int(lava_mask.sum())}
(PROJECT / 'out2_build.json').write_text(json.dumps(report, indent=1) + '\n')
print(json.dumps({k: report[k] for k in ('map', 'bmodels', 'faces', 'entities', 'actors', 'spawn_points', 'chests',
                                          'height_range', 'lava_cells')}))
print('moved', moved)
