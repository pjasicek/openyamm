"""Build Starport Reach (hes_out1.odm) from its design: terrain, ground materials, plants, buildings, decorations,
chests, events, then the ODM through the editor's writer, into runtime/worlds/hesper for the shared Hesper stage.

    python3 level_generation/projects/hesper_out1/build_out1.py
    python3 level_generation/projects/hesper_stage/stage.py

The design is the authority: the terrain fields of design/kreegan_world/zone1/starport_terrain.py and the roads,
places and decoration groups of make_starport_detail.py (the detailed map), so the map image and the map agree.
The editor needs the stage as its asset root (the Hesper textures and decorations live only there), so run the stage
once before the first build. Nothing is written to assets_dev.
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
DESIGN = ROOT / 'design/kreegan_world/zone1'
STAGE = ROOT / 'output/hesper_stage/assets_editor_dev'
SOURCE = PROJECT / 'source'
TREE = PROJECT / 'runtime/worlds/hesper'
MAP = 'hes_out1.odm'
sys.path.insert(0, str(DESIGN))
sys.path.insert(0, str(PROJECT))
import make_starport_detail as detail  # noqa: E402
from bmodels import Model, normal, rotate, write_obj  # noqa: E402
import houses  # noqa: E402
from starport_terrain import CANYON_LINE, CELL, CELL_UNITS, CRATER, at, build_terrain  # noqa: E402

GRID = 128
STEP = 512
TEXELS = 16                                   # weight texels per terrain cell
BOUND = 4 * CELL_UNITS                        # the playable square: +-23 040
rng = np.random.default_rng(20261020)


# --- Coordinates ----------------------------------------------------------------------------------------------------
def to_px(x, y):
    return (np.asarray(x) / CELL_UNITS + 4) * CELL, (4 - np.asarray(y) / CELL_UNITS) * CELL


def to_world(px, py):
    return (np.asarray(px) / CELL - 4) * CELL_UNITS, (4 - np.asarray(py) / CELL) * CELL_UNITS


def place(cell, fx=0.5, fy=0.5):
    x, y = to_world(*at(cell, fx, fy))
    return float(x), float(y)


def game_height(h):
    """The design's relative height in world units: 800 + 1500 h, the outer dune walls flattened above 6000."""
    z = 800.0 + 1500.0 * h
    return np.minimum(np.where(z > 6000.0, 6000.0 + (z - 6000.0) * 0.3, z), 8000.0)


# --- Terrain heights ------------------------------------------------------------------------------------------------
gx = np.arange(GRID)
sample_x, sample_y = np.meshgrid((gx - 64) * STEP, (64 - gx) * STEP)        # [gy, gx]
heights = np.zeros((GRID, GRID))
for dx in (-170, 0, 170):
    for dy in (-170, 0, 170):
        h, _ = build_terrain(*to_px(sample_x + dx, sample_y + dy))
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


def polyline(points_px):
    return [tuple(float(v) for v in to_world(*p)) for p in points_px]


def resample(points, spacing=256.0):
    out = [points[0]]
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
            d = np.hypot(px[:, 0] - x, px[:, 1] - y)
            k = int(np.argmin(d))
            if d[k] > width / 2 + falloff:
                continue
            weight = 1.0 if d[k] <= width / 2 else 1.0 - (d[k] - width / 2) / falloff
            heights[iy, ix] = heights[iy, ix] * (1 - weight) + profile[k] * weight


def flatten(centre, half_x, half_y, yaw=0.0, falloff=700.0, level=None):
    """Level a building pad (the median height under it unless given), blended over falloff."""
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
    return level


# Buildings and their pads (world units). Positions are the detailed map's.
SITES = {
    'terminal': (place('F4', 0.55, 0.5), 1500, 1300, 0.0),
    'archive_dome': (place('C1', 0.5, 0.45), 1250, 1250, 0.0),
    'hangar_west': (place('D3', 0.3, 0.45), 850, 1250, 0.0),
    'hangar_east': (place('D3', 0.72, 0.45), 850, 1250, 0.0),
    'hangar_ruins': (place('C4', 0.45, 0.45), 1750, 1050, 0.0),
    'gantries': (place('E3', 0.5, 0.35), 2600, 950, 0.0),
    'camp': (place('B3', 0.5, 0.5), 1900, 1700, 0.0),
    'scrapyard': (place('G4', 0.5, 0.5), 2400, 2400, 0.0),
    'outpost': (place('H4', 0.4, 0.45), 500, 500, 0.0),
}
for name, (centre, hx, hy, yaw) in SITES.items():
    flatten(centre, hx, hy, yaw)
# Landfall, the Hesperians' town in the south-west corner: its layout is design/kreegan_world/zone1/landfall_plan.py's
# (world units). The town stands on one level pad, cliffs rising behind it west and south, its wall north and east.
LANDFALL = json.loads((DESIGN / 'landfall_plan.json').read_text())
TOWN_LO, TOWN_HI = np.array(LANDFALL['town'][:2]), np.array(LANDFALL['town'][2:])
TOWN_CENTRE = tuple((TOWN_LO + TOWN_HI) / 2)
TOWN_HALF = tuple((TOWN_HI - TOWN_LO) / 2)
EAST_GATE, NORTH_GATE = (tuple(LANDFALL['wall']['gates'][k]) for k in ('east', 'north'))

# The Crew Ramp door of Hangar Nine on the crash crater's south-west rim, facing Landfall's East Gate.
crater_centre = place(*CRATER[:3])
toward = np.array(EAST_GATE) - np.array(crater_centre)
toward /= np.linalg.norm(toward)
crew_door = tuple(np.array(crater_centre) + toward * CRATER[3] * CELL_UNITS * 1.02)
crew_yaw = math.atan2(toward[1], toward[0])
flatten(crew_door, 450, 450, crew_yaw, falloff=500)
flatten(crater_centre, 640, 580, falloff=500)        # the roof hatch's frame and grille lie on a level floor


# --- The arrival (1): the shelf the party's lander cut (README "The arrival") -------------------------------------
# The lander ploughed the crater from the north-east and slewed up its south-west wall, its nose ending by the Crew
# Ramp door (which the crash cracked open). The hull rests on a shelf it cut into the wall, along the wall, its hatch
# toward the rim; the party starts on the rim above its nose, looking down at Landfall.
def crater_point(degrees, r):
    """A point of the crash crater: direction (degrees, 0 east, counter-clockwise) and radius (crater radii)."""
    a = math.radians(degrees)
    return (crater_centre[0] + math.cos(a) * r * CRATER[3] * CELL_UNITS,
            crater_centre[1] + math.sin(a) * r * CRATER[3] * CELL_UNITS)


WRECK_DIRECTION = -142.0                             # from the crater's centre; the Crew Ramp door is at -124
wreck_centre = crater_point(WRECK_DIRECTION, 0.86)
wreck_nose = WRECK_DIRECTION + 90.0                  # along the wall, toward the Crew Ramp door
wreck_level = flatten(wreck_centre, 720, 360, math.radians(wreck_nose), falloff=420,
                      level=height_at(*crater_point(WRECK_DIRECTION, 0.9)))

# Roads: the service road and the Ashrunner tracks cut gentle grades; the canyon track becomes the ramp to D2.
paved = [polyline(line) for line in detail.ROADS['paved']]


def run_on(line, distance=11000.0):
    """A road that leaves the playable square at an end runs on past the map's edge, so it reads as going
    somewhere: its end segment continued outward."""
    for end, inner in ((0, 1), (-1, -2)):
        (x, y), (ix, iy) = line[end], line[inner]
        if max(abs(x), abs(y)) > BOUND - 600:
            dx, dy = x - ix, y - iy
            length = math.hypot(dx, dy)
            point = (x + dx / length * distance, y + dy / length * distance)
            line = [point] + line if end == 0 else line + [point]
    return line


paved = [run_on(line) for line in paved]


OPEN_SITES = ('scrapyard', 'camp')                  # open yards the roads run into


def roads_under_buildings(lines, half_width):
    """The roads that pass over a building's pad (SITES): a road goes round a building, never under it. A road's last
    500 units at either end may reach a pad (it arrives at the door); the open yards are exempt."""
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



tracks = [polyline(line) for line in detail.ROADS['track']]
resin = [polyline(line) for line in detail.ROADS['resin']]
for kind, lines, half_width in (('paved', paved, 330), ('track', tracks, 200)):
    crossings = roads_under_buildings(lines, half_width)
    if crossings:
        raise SystemExit(f'build_out1: a {kind} road passes under a building: ' + '; '.join(crossings))
for line in paved:
    grade(line, 700, 600, 0.18)
for line in tracks + resin:
    grade(line, 500, 500, 0.3)
# The apron stays one flat plateau over its plating.
(ax0, ay0), (ax1, ay1) = [to_world(*p) for p in [at('D4', 0.05, 0.1), at('E4', 0.95, 0.92)]]
apron_level = flatten(((ax0 + ax1) / 2, (ay0 + ay1) / 2), abs(ax1 - ax0) / 2, abs(ay1 - ay0) / 2, falloff=600)
centre, hx, hy, yaw = SITES['terminal']             # the Terminal stands at the apron's level
flatten(centre, hx, hy, yaw, falloff=600, level=apron_level)
town_level = flatten(TOWN_CENTRE, TOWN_HALF[0] + 250, TOWN_HALF[1] + 250, falloff=1100)
# The cliffs: from the town floor's west and south edges the rock climbs CLIFF_RISE over CLIFF_RUN, steepest at the
# foot, and runs on 900 past the wall's ends (into which the wall is built) before it falls back to the ground.
cliffs = LANDFALL['cliffs']


def cliff_rise(d):
    u = np.clip(d / cliffs['run'], 0.0, 1.0)
    return cliffs['rise'] * (1.0 - (1.0 - u) ** 2) * (d > 0)


rise = np.maximum(cliff_rise(TOWN_LO[0] - sample_x) * np.clip((TOWN_HI[1] + 900 - sample_y) / 900, 0, 1),
                  cliff_rise(TOWN_LO[1] - sample_y) * np.clip((TOWN_HI[0] + 900 - sample_x) / 900, 0, 1))
heights[:] = np.where(rise > 0, np.maximum(heights, town_level + rise), heights)
# A cliff home's front stands 250 out from the foot; the triangles from the first raised row would still climb over
# its threshold, so the ground in front of it and under its front half is the town floor.
for house in LANDFALL['houses']:
    if house['style'] != 'cliff':
        continue
    (hx, hy), front = house['position'], {'north': math.pi / 2, 'south': -math.pi / 2, 'east': 0.0,
                                          'west': math.pi}[house['door']]
    fx, fy = hx + math.cos(front) * house['depth'] / 2, hy + math.sin(front) * house['depth'] / 2
    out_x, out_y = math.cos(front), math.sin(front)
    ahead = (sample_x - fx) * out_x + (sample_y - fy) * out_y           # + toward the town, - into the rock
    across = -(sample_x - fx) * out_y + (sample_y - fy) * out_x
    level = (ahead > -400) & (ahead < 700) & (np.abs(across) < house['width'] / 2 + 150)
    heights[level] = town_level

# D2's entrance: a notch cut into the canyon's east wall at floor level, beside its south end. Walk from the canyon's
# centre line toward the design's hatch until the wall stands 700 above the floor; the notch reaches 400 past that.
hatch_point = np.array(place('G6', 0.68, 0.5))
canyon_line = [np.array(p) for p in polyline(CANYON_LINE)]
nearest = None
for a, b in zip(canyon_line, canyon_line[1:]):
    t = np.clip(np.dot(hatch_point - a, b - a) / np.dot(b - a, b - a), 0, 1)
    point = a + (b - a) * t
    if nearest is None or np.linalg.norm(hatch_point - point) < np.linalg.norm(hatch_point - nearest):
        nearest = point
east = (hatch_point - nearest) / np.linalg.norm(hatch_point - nearest)
station_level = height_at(*nearest)
wall_d = next(d for d in range(0, 4000, 50) if height_at(*(nearest + east * d)) > station_level + 700)
# The rock behind and beside the station rises to a cliff above it, so the plant is set into the wall, not standing
# in front of the canyon's end; then the notch is cut back to the floor in front of it.
along_e = (sample_x - nearest[0]) * east[0] + (sample_y - nearest[1]) * east[1]
across = -(sample_x - nearest[0]) * east[1] + (sample_y - nearest[1]) * east[0]
outside = np.maximum.reduce([wall_d + 250 - along_e, np.abs(across) - 1000, along_e - (wall_d + 2200),
                             np.zeros_like(along_e)])
cliff = np.clip(1.0 - outside / 450.0, 0.0, 1.0)
heights[:] = np.maximum(heights, heights * (1 - cliff) + (station_level + 1250) * cliff)
flatten(tuple(nearest + east * wall_d), 400, 750, math.atan2(east[1], east[0]), falloff=250, level=station_level)
station = (tuple(nearest + east * (wall_d + 200)), wall_d, tuple(-east))

height_bytes = np.clip(np.round(heights / 32.0), 0, 255).astype(np.uint8)
heights = height_bytes.astype(np.float64) * 32.0          # the quantised heights everything else stands on

# --- Materials: tiles (one per cell) and weights (16 texels per cell) ----------------------------------------------
# Tile ids through the lookups [volcanic 198, sand 594, rock 342, water 126]: raw 90 + 36 * set + offset. The tile
# names key the plant rules; the ground itself is drawn by the material weights. The fourth set is the MM8 water
# tiles: the stage's liquids.yml makes them Hesper's rust brine (a shallow liquid: waded, never drowned in), and
# brine_tiles() picks their shore tiles, whose coverage masks the stage copies from MM8.
LOOKUPS = [198, 594, 342, 126]
TILES = {'ash': 90, 'crust': 91, 'creep': 102, 'crater': 103, 'dune': 126, 'wall': 128, 'rock': 162,
         'canyon': 164, 'brine': 198, 'glass': 175, 'plating': 1}
# Brine shore tiles (wtrdr*, raw 210-221) by where the brine lies around a land cell: an edge (one side), an inner
# corner (two sides) or an outer corner (one diagonal). MM8's own shores pair them so (wtrdrN: brine to the south).
BRINE_EDGE = {'S': 216, 'N': 217, 'W': 214, 'E': 215}
BRINE_INNER = {'SW': 218, 'NW': 219, 'SE': 220, 'NE': 221}
BRINE_OUTER = {'SW': 210, 'NW': 211, 'SE': 212, 'NE': 213}
LAYERS = ['ash', 'ash_dune', 'glass', 'plating', 'canyon', 'scree', 'creep']           # weighted; 'cliff' is slope
MIX = {'ash': {'ash': 1.0}, 'crust': {'ash': 0.55, 'scree': 0.45}, 'dune': {'ash_dune': 1.0},
       'wall': {'ash_dune': 1.0}, 'glass': {'glass': 1.0}, 'crater': {'glass': 0.85, 'scree': 0.15},
       'plating': {'plating': 1.0}, 'rock': {'scree': 0.6, 'ash': 0.4}, 'canyon': {'canyon': 1.0},
       'creep': {'creep': 1.0}, 'brine': {'scree': 0.5, 'canyon': 0.5}}


def road_masks(xs, ys):
    """Paved road, crawler ruts and the resin path at world points."""
    def distance(lines):
        best = np.full(xs.shape, 1e9)
        for line in lines:
            for (ax, ay), (bx, by) in zip(line, line[1:]):
                dx, dy = bx - ax, by - ay
                t = np.clip(((xs - ax) * dx + (ys - ay) * dy) / (dx * dx + dy * dy), 0, 1)
                best = np.minimum(best, np.hypot(xs - (ax + t * dx), ys - (ay + t * dy)))
        return best
    road = distance(paved) < 330
    track_d = distance(tracks)
    ruts = (np.abs(track_d - 150) < 55)
    return road, ruts, distance(resin) < 170


# Landfall's streets, as MM towns draw theirs into the ground: the two gate streets paved like the service road that
# runs in through the East Gate, the lanes gravel.
PAVED_STREETS = ('Main Street', 'North Street')
DOOR_ANGLE = {'north': math.pi / 2, 'south': -math.pi / 2, 'east': 0.0, 'west': math.pi}


def street_rect(a, b, width):
    (ax, ay), (bx, by) = a, b
    half = width / 2
    return (min(ax, bx) - (half if ax == bx else 0), min(ay, by) - (half if ay == by else 0),
            max(ax, bx) + (half if ax == bx else 0), max(ay, by) + (half if ay == by else 0))


street_rects = {name: street_rect(a, b, LANDFALL['street_width']) for name, (a, b) in LANDFALL['streets'].items()}


def street_masks(xs, ys):
    """Landfall's paved streets and its gravel lanes at world points (the doors have steps down to the ground, not
    paths: painted paths missed the doors and blotted the paving where they met it)."""
    def inside(rects):
        return np.logical_or.reduce([(xs >= x0) & (xs <= x1) & (ys >= y0) & (ys <= y1) for x0, y0, x1, y1 in rects])
    paved_t = inside([street_rects[name] for name in PAVED_STREETS])
    gravel_t = inside([r for name, r in street_rects.items() if name not in PAVED_STREETS])
    return paved_t, gravel_t & ~paved_t


cell_x, cell_y = np.meshgrid((gx - 64) * STEP + STEP / 2, (64 - gx) * STEP - STEP / 2)
_, cell_material = build_terrain(*to_px(cell_x, cell_y))
road, _, path = road_masks(cell_x, cell_y)
cell_material[road] = 'plating'
cell_material[path] = 'creep'
town_paved, town_gravel = street_masks(cell_x, cell_y)
cell_material[town_paved | town_gravel] = 'plating'            # no plants on the streets
tile_bytes = np.vectorize(TILES.get)(cell_material).astype(np.uint8)


def brine_tiles(brine):
    """Shore tiles round the brine cells (rows run north to south): land cells beside brine take the shore tile of
    the side or corner the brine lies on. A land cell with brine on opposite sides, three sides or two diagonals
    alone has no tile and becomes brine; repeated until every shore cell has one. Returns the brine mask and the
    shore cells' tile ids (0 elsewhere)."""
    brine = brine.copy()
    while True:
        padded = np.pad(brine, 1)
        n, s_, w, e = padded[:-2, 1:-1], padded[2:, 1:-1], padded[1:-1, :-2], padded[1:-1, 2:]
        nw, ne, sw, se = padded[:-2, :-2], padded[:-2, 2:], padded[2:, :-2], padded[2:, 2:]
        sides = n.astype(int) + s_ + w + e
        fill = ~brine & ((n & s_) | (w & e) | (sides >= 3)
                         | ((sides == 0) & ((nw.astype(int) + ne + sw + se) >= 2)))
        if not fill.any():
            break
        brine |= fill
    shore = np.zeros(brine.shape, np.uint8)
    land = ~brine
    for name, mask in (('S', s_), ('N', n), ('W', w), ('E', e)):
        shore[land & (sides == 1) & mask] = BRINE_EDGE[name]
    for name, (a, b) in {'SW': (s_, w), 'NW': (n, w), 'SE': (s_, e), 'NE': (n, e)}.items():
        shore[land & (sides == 2) & a & b] = BRINE_INNER[name]
    for name, mask in (('SW', sw), ('NW', nw), ('SE', se), ('NE', ne)):
        shore[land & (sides == 0) & mask] = BRINE_OUTER[name]
    return brine, shore


brine_mask, brine_shore = brine_tiles(cell_material == 'brine')
cell_material[brine_mask] = 'brine'
tile_bytes = np.vectorize(TILES.get)(cell_material).astype(np.uint8)
tile_bytes[brine_shore > 0] = brine_shore[brine_shore > 0]
# The brine lies level in its bed: every corner of a brine or shore cell sinks to the lowest brine corner within a
# cell of it. The liquid's planes are drawn at their cell's corners, so a shore cell with a corner up the bank would
# tilt its sheet of brine up the slope (up the cliff at the Pumping Station); its land part is a flat margin instead.


def cell_corners(cells):
    corners = np.zeros(heights.shape, bool)
    for dy in (0, 1):
        for dx in (0, 1):
            corners[dy:GRID, dx:GRID] |= cells[:GRID - dy, :GRID - dx]
    return corners


brine_corners = cell_corners(brine_mask)
wet_corners = cell_corners(brine_mask | (brine_shore > 0))
padded = np.pad(np.where(brine_corners, heights, np.inf), 1, constant_values=np.inf)
lowest = np.min([padded[1 + dy:GRID + 1 + dy, 1 + dx:GRID + 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)],
                axis=0)
heights[wet_corners] = np.minimum(heights, lowest)[wet_corners]
# A pool (brine whose bed spans at most 160 in height) lies wholly level, at its lowest brine corner.
pool_labels, pool_count = ndimage.label(brine_mask | (brine_shore > 0), structure=np.ones((3, 3)))
for label in range(1, pool_count + 1):
    pool_wet = cell_corners(pool_labels == label)
    pool_brine = pool_wet & brine_corners
    if pool_brine.any() and np.ptp(heights[pool_brine]) <= 160:
        heights[pool_wet] = heights[pool_brine].min()
height_bytes = np.clip(np.round(heights / 32.0), 0, 255).astype(np.uint8)

size = GRID * TEXELS
units = 65536.0 / size
tx, ty = np.meshgrid(-32768.0 + (np.arange(size) + 0.5) * units, 32768.0 - (np.arange(size) + 0.5) * units)
_, texel_material = build_terrain(*to_px(tx, ty))
field = np.zeros((size, size, len(LAYERS)), dtype=np.float32)
for material, mix in MIX.items():
    where = texel_material == material
    for layer, weight in mix.items():
        field[..., LAYERS.index(layer)] += where * weight
# The cliff raised round the Pumping Station is canyon rock.
texel_along = (tx - nearest[0]) * east[0] + (ty - nearest[1]) * east[1]
texel_across = -(tx - nearest[0]) * east[1] + (ty - nearest[1]) * east[0]
texel_outside = np.maximum.reduce([wall_d - 300 - texel_along, np.abs(texel_across) - 1300,
                                   texel_along - (wall_d + 2500), np.zeros_like(texel_along)])
station_rock = texel_outside <= 0
field[station_rock] = 0
field[station_rock, LAYERS.index('canyon')] = 1
softness = 110.0 / units
field = np.stack([ndimage.gaussian_filter(field[..., c], softness, mode='nearest') for c in range(len(LAYERS))], -1)
road_t, ruts_t, path_t = road_masks(tx, ty)
paved_t, gravel_t = street_masks(tx, ty)
for mask, layer, crisp in [(path_t, 'creep', 1.2), (ruts_t, 'scree', 0.8), (road_t, 'plating', 0.75),
                           (paved_t, 'plating', 0.75), (gravel_t, 'scree', 0.9)]:
    weight = np.clip(ndimage.gaussian_filter(mask.astype(np.float32), crisp, mode='nearest'), 0, 1)
    field *= (1 - weight)[..., None]
    field[..., LAYERS.index(layer)] += weight
# Dust over the old road's pavers toward the map crossings (the integrator, 2026-10-23: the white paving met the
# Scour's dulled, dusted pavers and the Brood Spires' pass in a hard change of tone): 85 % at the east and north edges,
# gone 4 800 in. Ash, warmed toward the Scour by a little of its rust-red ore.
east_fade = np.clip(1.0 - (BOUND - tx) / 4800.0, 0.0, 1.0)
north_fade = np.clip(1.0 - (BOUND - ty) / 4800.0, 0.0, 1.0)
paved_weight = field[..., LAYERS.index('plating')] * np.clip(
    ndimage.gaussian_filter(road_t.astype(np.float32), 0.75, mode='nearest'), 0, 1)
for fade, mix in ((east_fade, {'canyon': 0.15, 'ash': 0.85}), (north_fade, {'ash': 1.0})):
    moved = paved_weight * 0.85 * fade
    field[..., LAYERS.index('plating')] -= moved
    for layer, share in mix.items():
        field[..., LAYERS.index(layer)] += moved * share
    paved_weight = paved_weight - moved
field /= np.maximum(field.sum(-1, keepdims=True), 1e-6)
field = np.concatenate([field, np.zeros((size, size, 8 - len(LAYERS)), dtype=np.float32)], -1)
quantized = np.clip(field * 255 + 0.5, 0, 255).astype(np.uint8)
del texel_material, tx, ty

# --- Buildings --------------------------------------------------------------------------------------------------------
SIZES = {}                          # texture -> native size (master / 4)
for folder in ['textures_d0/blv', 'textures_out1/masters', 'textures_interiors/masters']:
    for png in (ROOT / 'design/kreegan_world/art' / folder).glob('*.png'):
        with Image.open(png) as image:
            SIZES[png.stem] = (image.width / 4, image.height / 4)
# World size of one repeat over the native size, for the textures whose detail (corrugation, plates, rivets) reads
# too small at one native texel per world unit on buildings this large; hhmodule's repeat is the hab's wall height.
TEXTURE_SCALE = {'hohangar': 2.0, 'hoplate': 1.5, 'hoterm': 1.25, 'hiwall': 1.25, 'hopylon': 1.25, 'hhscrapw': 1.5,
                 'hhmodule': 2.5, 'hhprefab': 1.75, 'hhprefdk': 1.75, 'hhwallpf': 1.75, 'hhwalldk': 1.75, 'hhrock': 2.0}
for texture, scale in TEXTURE_SCALE.items():
    SIZES[texture] = (SIZES[texture][0] * scale, SIZES[texture][1] * scale)
models = []
EVENTS = {}                         # event id -> (title, handler body)


def ground(point):
    return height_at(*point)


def terminal():
    """The domed hall: its west front a gold-trimmed portal with the tall arched glass doors (D1), flanked by curved
    glass curtain walls on slim mullions, a light strip on either side of the doors and three steps to the apron."""
    (cx, cy), _, _, _ = SITES['terminal']
    z = ground((cx, cy))
    m = Model('terminal')
    w, d, h = 2600.0, 2200.0, 760.0
    west = cx - w / 2
    m.box((cx, cy, z), (w, d, h), 'hoterm', top='hoplate', skip=('west',))
    # The portal: a block standing out of the front, taller than the hall, the doors in its face.
    pw, pd, ph = 760.0, 260.0, 1000.0
    px = west - pd / 2
    m.box((px, cy, z), (pd, pw, ph), 'hoterm', top='hoplate', skip=('west',))
    front = px - pd / 2
    door_w, door_h = 512.0, 1024.0 * 0.82
    y0, y1 = cy - door_w / 2, cy + door_w / 2
    for (a, b, lo, hi) in [(cy - pw / 2, y0, 0, ph), (y1, cy + pw / 2, 0, ph), (y0, y1, door_h, ph)]:
        m.face([(front, b, z + lo), (front, a, z + lo), (front, a, z + hi), (front, b, z + hi)], 'hoterm')
    m.face([(front - 2, y1, z), (front - 2, y0, z), (front - 2, y0, z + door_h), (front - 2, y1, z + door_h)],
           'hodoorgl', event=11, fit=True)
    for y in (y0 - 40, y1 + 40):                              # gold jambs and the light strips beside them
        m.box((front - 20, y, z), (40, 50, door_h + 20), 'hogold')
        m.box((front - 8, y + (-90 if y < cy else 90), z + 120), (16, 40, door_h - 200), 'hcstripd')
    m.box((front - 25, cy, z + ph - 70), (50, pw + 40, 70), 'hogold')
    for k in range(3):                                          # steps down to the apron
        m.box((front - 120 - 110 * k, cy, z - 40 * (k + 1) + 40), (120, pw - 60 + 80 * k, 40), 'hoplate')
    # The curtain walls: curved glass on mullions from the portal to the hall's corners, a ceramic band above.
    for side in (-1, 1):
        start, end = cy + side * pw / 2, cy + side * d / 2
        segments = 5
        points = []
        for k in range(segments + 1):
            t = k / segments
            y = start + (end - start) * t
            x = west - 260 * math.sin(math.pi * (0.5 + 0.5 * t)) - 0 * t
            points.append((x, y))
        for k in range(segments):
            (xa, ya), (xb, yb) = points[k], points[k + 1]
            if side > 0:                                # wound counter-clockwise seen from the west
                (xa, ya), (xb, yb) = (xb, yb), (xa, ya)
            m.face([(xa, ya, z), (xb, yb, z), (xb, yb, z + 620), (xa, ya, z + 620)], 'hoglassl')
            m.face([(xa, ya, z + 620), (xb, yb, z + 620), (xb, yb, z + h), (xa, ya, z + h)], 'hoterm')
        for x, y in points:
            m.box((x, y, z), (40, 40, 640), 'hogold')
        roof = [(x, y, z + h) for x, y in points] + [(west, end, z + h), (west, start, z + h)]
        m.face(roof[::-1] if side > 0 else roof, 'hoplate')
    m.dome((cx + 200, cy, z), 900, 520, 16, 5, 'hodome', z0=h)
    m.prism((cx + 200, cy, z), 960, 60, 16, 'hogold', z0=h)
    return m


def crew_ramp():
    m = Model('crew_ramp')
    cx, cy = crew_door
    z = ground(crew_door)
    yaw = crew_yaw + math.pi                       # the door faces away from the crater, toward the Lift Head
    m.box((cx, cy, z - 120), (420, 520, 460), 'hoterm', yaw=yaw, top='hoplate')
    c, s = math.cos(crew_yaw), math.sin(crew_yaw)
    fx, fy = cx + c * 212, cy + s * 212            # the face toward the Lift Head
    px, py = -s, c
    corners = [(fx - px * 130, fy - py * 130), (fx + px * 130, fy + py * 130)]
    m.face([(corners[0][0], corners[0][1], z), (corners[1][0], corners[1][1], z),
            (corners[1][0], corners[1][1], z + 280), (corners[0][0], corners[0][1], z + 280)], 'hcdoor', event=10)
    return m


def archive_dome():
    (cx, cy), _, _, _ = SITES['archive_dome']
    z = ground((cx, cy))
    m = Model('archive_dome')
    m.dome((cx, cy, z), 1250, 1250, 20, 7, 'hodome', z0=-560, from_ring=1)
    m.box((cx, cy - 1050, z), (520, 300, 360), 'hoterm', top='hoplate', skip=('north',))
    m.face([(cx - 140, cy - 1201, z), (cx + 140, cy - 1201, z), (cx + 140, cy - 1201, z + 300),
            (cx - 140, cy - 1201, z + 300)], 'hcshutter', event=13)
    return m


def hangar(name):
    """A barrel vault open at both ends: its roof in bays, two or three of them torn out, a rib over each bay joint."""
    (cx, cy), hx, hy, _ = SITES[name]
    z = ground((cx, cy))
    m = Model(name)
    radius, length, sides, bays = 760.0, 2300.0, 8, 6
    holes = {'hangar_west': {(2, 3), (5, 1)}, 'hangar_east': {(1, 4), (6, 2), (6, 3)}}[name]

    def arc(k, r=radius):
        a = math.pi * k / sides
        return cx + r * math.cos(a), z + r * math.sin(a) * 1.1
    for k in range(sides):
        (x0, z0), (x1, z1) = arc(k), arc(k + 1)
        for b in range(bays):
            if (k, b) in holes:
                continue
            y0, y1 = cy - length / 2 + length * b / bays, cy - length / 2 + length * (b + 1) / bays
            m.both([(x0, y0, z0), (x1, y0, z1), (x1, y1, z1), (x0, y1, z0)], 'hohangar')
    for b in range(bays + 1):                              # ribs standing out of the shell
        y = cy - length / 2 + length * b / bays
        for k in range(sides):
            (x0, z0), (x1, z1) = arc(k, radius + 6), arc(k + 1, radius + 6)
            (u0, w0), (u1, w1) = arc(k, radius + 60), arc(k + 1, radius + 60)
            mid = math.pi * (k + 0.5) / sides
            m.facing([(u0, y - 40, w0), (u1, y - 40, w1), (u1, y + 40, w1), (u0, y + 40, w0)], 'hopylon',
                     (math.cos(mid), 0, math.sin(mid)))
            for side in (-40, 40):
                m.facing([(x0, y + side, z0), (x1, y + side, z1), (u1, y + side, w1), (u0, y + side, w0)],
                         'hopylon', (0, side, 0))
    return m


def hangar_ruins():
    (cx, cy), hx, hy, _ = SITES['hangar_ruins']
    z = ground((cx, cy))
    m = Model('hangar_ruins')
    walls = [((-1300, -800), (1300, -800), 520), ((1300, -800), (1300, 200), 380), ((-1300, 800), (-200, 800), 300),
             ((300, 800), (1300, 800), 460), ((-1300, -800), (-1300, 300), 610), ((-400, -200), (400, -200), 240)]
    for (x0, y0), (x1, y1), top in walls:
        length = math.hypot(x1 - x0, y1 - y0)
        pieces = max(1, int(length / 520))
        for k in range(pieces):
            t0, t1 = k / pieces, (k + 1) / pieces
            px0, py0 = cx + x0 + (x1 - x0) * t0, cy + y0 + (y1 - y0) * t0
            px1, py1 = cx + x0 + (x1 - x0) * t1, cy + y0 + (y1 - y0) * t1
            height = top * (0.55 + 0.45 * rng.random())
            centre = ((px0 + px1) / 2, (py0 + py1) / 2, z)
            yaw = math.atan2(py1 - py0, px1 - px0)
            m.box(centre, (math.hypot(px1 - px0, py1 - py0) - 30, 90, height), 'hoterm', yaw=yaw, top='hosalvage')
    return m


def gantries():
    (cx, cy), _, _, _ = SITES['gantries']
    m = Model('gantries')
    for i in range(4):
        x, y = place('E3', 0.2 + i * 0.2, 0.35)
        z = ground((x, y))
        height = 1500.0 + 150 * (i % 2)
        for lx in (-170, 170):
            for ly in (-170, 170):
                m.box((x + lx, y + ly, z), (60, 60, height), 'hopylon', top='hogold')
        for level in (400, 900, height - 60):
            m.box((x, y - 170, z + level), (400, 50, 50), 'hopylon')
            m.box((x, y + 170, z + level), (400, 50, 50), 'hopylon')
        m.box((x, y + 650, z + height), (110, 1700, 90), 'hopylon', top='hogold')     # the boom, to the north
    return m


def pumping_station():
    """D2's entrance set into the canyon's east wall: a ceramic plate wall in a notch cut into the rock, the round
    vault hatch in a brass rim, brass pipes along its top, an outflow pipe over the brine bed and a grate step."""
    m = Model('pumping_station')
    centre, wall, facing = station
    cx, cy = centre
    z = station_level
    n = np.array(facing)                                # out of the wall, toward the canyon
    r = np.array([-n[1], n[0]])                          # along the wall

    def at_wall(along, out, up=0.0):
        p = np.array(centre) + r * along + n * out
        return (p[0], p[1], z + up)
    yaw = math.atan2(n[1], n[0])
    m.box(at_wall(0, -160), (320, 1300, 920), 'hiwall', yaw=yaw, top='hoplate')
    for along in (-600, 600):                            # buttresses
        m.box(at_wall(along, 40), (180, 140, 960), 'hiwall', yaw=yaw, top='hogold')
    m.disc(at_wall(0, 0, 380), 320, facing, 'hohatch', event=12, rim=60, rim_depth=50, rim_texture='hogold')
    m.box(at_wall(0, 160), (320, 760, 36), 'higrate', yaw=yaw, top='higrate')
    m.tube(at_wall(-650, 90, 860), at_wall(650, 90, 860), 55, 'hogold')          # the pipe run along the top
    m.tube(at_wall(-540, 90, 860), at_wall(-540, 90, 0), 45, 'hogold')           # down to the ground
    m.tube(at_wall(450, 60, 620), at_wall(450, 360, 620), 70, 'hogold')          # the outflow, over the brine bed
    m.tube(at_wall(450, 360, 620), at_wall(450, 360, 380), 70, 'hogold')
    return m


def hatch():
    """The torn roof hatch of Hangar Nine in the crater floor: a gold-rimmed frame and its fallen grille plates."""
    cx, cy = crater_centre
    z = ground((cx, cy))
    m = Model('roof_hatch')
    for (dx, dy, sx, sy) in [(0, -520, 1200, 90), (0, 520, 1200, 90), (-560, 0, 90, 1040), (560, 0, 90, 1040)]:
        m.box((cx + dx, cy + dy, z - 30), (sx, sy, 90), 'hoterm', top='hogold')
    m.face([(cx - 515, cy - 475, z + 10), (cx + 515, cy - 475, z + 10), (cx + 515, cy + 475, z + 10),
            (cx - 515, cy + 475, z + 10)], 'hcgrille')
    return m


for build in [terminal, crew_ramp, archive_dome, lambda: hangar('hangar_west'),
              lambda: hangar('hangar_east'), hangar_ruins, gantries, pumping_station, hatch]:
    models.append(build())

# --- Decorations, chests and the party start -------------------------------------------------------------------------
ids = json.loads((ROOT / 'output/hesper_stage/decoration_ids.json').read_text())
footprints = [(centre, max(hx, hy) + 200) for centre, hx, hy, _ in SITES.values()] + [(TOWN_CENTRE,
                                                                                        math.hypot(*TOWN_HALF) + 400),
                                                                                        (crew_door, 500),
                                                                                        (station[0], 900)]


def clear(x, y, margin=0.0):
    if abs(x) > BOUND - 400 or abs(y) > BOUND - 400:
        return False
    if any(math.hypot(x - c[0], y - c[1]) < r + margin for c, r in footprints):
        return False
    road, ruts, path = road_masks(np.array([x]), np.array([y]))
    return not (road[0] or ruts[0])


entities = []
model_placements = []                   # the big models the minimap draws (build_minimap_blender.py)
MINIMAP_MODELS = {'hes_ash_watchtower', 'hes_salvage_crane', 'hes_kreegan_outpost', 'hes_alarm_pylon',
                  'hes_resin_rib', 'hes_skull_ribs'}


def decoration(name, x, y, facing=None, event=0, sink=0.0, cog=0):
    """A decoration entity. A click runs `event` (the engine reads the secondary slot); `cog` (the primary) keys
    evt.SetSprite's swaps."""
    facing = int(rng.integers(0, 360)) if facing is None else int(round(facing)) % 360
    position = {'x': int(round(x)), 'y': int(round(y)), 'z': int(round(height_at(x, y) - sink))}
    if name in MINIMAP_MODELS:
        model_placements.append({'name': name, **position, 'facing': facing})
    entities.append({'entity_index': 0, 'name': name, 'decoration_list_id': ids[name] - 1, 'ai_attributes': 0,
                     'position': position, 'facing': facing, 'event_id_primary': cog,
                     'event_id_secondary': event, 'variable_primary': 0, 'variable_secondary': 0, 'special_trigger': 0,
                     'initial_decoration_flag': 0})


RIB_YAW = 0          # the rib model's curve direction relative to its facing (set from the model's review)
SYMBOLS = {'shard': ['hes_glass_shards'], 'boulder': ['hes_glass_boulder'], 'container': ['hes_container'],
           'tank': ['hes_fuel_tank'], 'wreck': ['hes_drone_wreck'], 'bones': ['hes_skull_ribs'],
           'pod': ['hes_creep_pod'], 'totem': ['hes_ashrunner_totem'], 'brazier': ['hes_brazier'],
           'sign': ['hes_signpost']}
signs = 0
for symbol, cell, fx, fy, count, spread in detail.DECOR:
    if symbol not in SYMBOLS:
        continue                                   # tufts and scrub are the plant system's
    centre = place(cell, fx, fy)
    placed = 0
    for _ in range(count * 6):
        if placed == count:
            break
        if spread > 0:
            dx, dy = rng.normal(0, spread * CELL_UNITS * 0.28, 2)
        else:
            dx, dy = 0.0, 0.0
        x, y = centre[0] + dx, centre[1] + dy
        if spread > 0 and not clear(x, y, 150):
            continue
        event = 0
        if symbol == 'sign':
            event = 30 + signs
            signs += 1
        decoration(SYMBOLS[symbol][0], x, y, event=event, sink=20 if symbol == 'bones' else 0)
        placed += 1
for cell, fx, fy in detail.PYLONS:
    decoration('hes_pylon', *place(cell, fx, fy))
# The founder statue (event 34; cog 34 keys its swap to the intact model once the head is back, CR-P3-11).
decoration('hes_founder_statue', *place('E4', 0.75, 0.75), facing=180, event=34, cog=34)
decoration('hes_relay_post', *place('F4', 0.18, 0.72), event=38)
TABLET_PLINTHS = [place(*cell) for cell in [('B2', 0.5, 0.5), ('B6', 0.4, 0.5), ('H3', 0.5, 0.4)]]
for k, (x, y) in enumerate(TABLET_PLINTHS):
    decoration('hes_tablet_plinth', x, y, event=35 + k)
(cx, cy), _, _, _ = SITES['scrapyard']
ribs = 20
for k in range(ribs):                              # the resin rib fence, the ribs curving in over the yard
    a = 2 * math.pi * k / ribs
    if math.cos(a - math.pi) > 0.94 or math.cos(a) > 0.96:  # the west gate and the drag path east
        continue
    x, y = cx + 2100 * math.cos(a), cy + 2100 * math.sin(a)
    decoration('hes_resin_rib', x, y, facing=(math.degrees(a) + 180 + RIB_YAW) % 360)
for _ in range(6):                                 # salvage heaps in the scrapyard
    (cx, cy), _, _, _ = SITES['scrapyard']
    a, r = rng.uniform(0, 2 * math.pi), rng.uniform(500, 1500)
    decoration('hes_salvage_heap', cx + r * math.cos(a), cy + r * math.sin(a))
for k in range(4):                                 # toppled gantry segments by the hangar ruins
    x, y = place('C4', 0.2 + 0.2 * k, 0.85)
    decoration('hes_gantry_segment', x, y)
(cx, cy), _, _, _ = SITES['archive_dome']
# The four crystal sockets round the Archive door, dark until Aster's shard n is restored (100018-100021): the load
# event lights socket n (cog 90 + n, hes_crystal_socket_lit).
for n, dx in enumerate((-330, -200, 200, 330), 1):
    decoration('hes_crystal_socket', cx + dx, cy - 1240, cog=90 + n)
# D10's way back out (its exit reads this): 500 south of the dome door's face, facing it.
archive_arrival = (cx, cy - 1201 - 500, ground((cx, cy - 1701)), 90)

# --- The buildings that are 3D models: the camps, the scrapyard crane, the outpost ----------------------------------
# Each is a decoration with no collision cylinder, and its footprint an invisible box (or boxes) in the colliders
# BModel. Sizes come from the models: a Meshy model is scaled to its design's length, a Blender one is in metres.
DECORATIONS = ROOT / 'level_generation/props/hesper_decorations'
designs = json.loads((DECORATIONS / 'designs.json').read_text())
colliders = Model('colliders')
# Degrees added to a model's facing so that its front (door, gate opening, the palisade's outer face) faces the
# direction asked for. 270 for a model whose front is its glTF +z side (the side codex_texture.py's guides call the
# front), found from the review (review/facing/: every model stood with its back to the plaza at 90).
FRONT_YAW = {'hes_low_pod_home': 0}             # the pod's doors are on its sides (glTF -x and +x)


def model_file(name):
    for path in [DECORATIONS / 'work/codex_tex' / f'{name}_export.glb',
                 DECORATIONS / 'work/hard_surface' / f'{name}.glb']:
        if path.exists():
            return path
    raise FileNotFoundError(name)


def model_scale(name):
    """World units per glTF unit, and the model's glTF bounds (x, y up, z)."""
    data = model_file(name).read_bytes()
    gltf = json.loads(data[20:20 + int.from_bytes(data[12:16], 'little')])
    accessors = [gltf['accessors'][primitive['attributes']['POSITION']] for mesh in gltf['meshes']
                 for primitive in mesh['primitives']]
    low = np.min([a['min'] for a in accessors], 0)
    high = np.max([a['max'] for a in accessors], 0)
    return (designs[name]['length'] / max(high - low) if name in designs else 100.0), low, high


def model_bounds(name):
    """The model's glTF bounds in world units at its game size."""
    scale, low, high = model_scale(name)
    return low * scale, high * scale


def building(name, x, y, front, event=0, collide=0.85, parts=None):
    """Place a model building with its front facing `front` (degrees, 0 east, counter-clockwise), its footprint
    box shrunk by `collide` (0: none), or `parts`: boxes as (along, across, length, depth) fractions of the
    footprint, in the model's own axes (x along its front, y out of its back)."""
    facing = (front + FRONT_YAW.get(name, 270)) % 360
    decoration(name, x, y, facing=facing, event=event)
    low, high = model_bounds(name)
    yaw = math.radians(facing)
    # glTF x is the game's local x, glTF z its local -y.
    centre = np.array([(low[0] + high[0]) / 2, -(low[2] + high[2]) / 2])
    size = np.array([high[0] - low[0], high[2] - low[2]])
    boxes = parts if parts is not None else ([(0.0, 0.0, collide, collide)] if collide else [])
    for along, across, length, depth in boxes:
        ox, oy = rotate(tuple(centre + size * (along, across)), yaw)
        colliders.collider((x + ox, y + oy, height_at(x, y) - 60), (size[0] * length, size[1] * depth,
                                                                       high[1] - low[1] + 60), yaw=yaw)
    return facing


def facing_to(x, y, target):
    return math.degrees(math.atan2(target[1] - y, target[0] - x))


# The Ashrunner camp: five homes facing the fire (BModels, houses.py: three crawler hulls and two salvage lean-tos),
# the trader's shop, the watchtower.
(cx, cy), _, _, _ = SITES['camp']
homes = [(0.3, 0.35, 'hull'), (0.55, 0.3, 'lean'), (0.7, 0.5, 'hull'), (0.4, 0.65, 'lean'), (0.6, 0.7, 'hull')]
camp_homes = []                                    # (x, y) of each home, for the camp folk (follow-up 39)
for k, (fx, fy, kind) in enumerate(homes):
    x, y = place('B3', 0.5 + (fx - 0.5) * 1.25, 0.5 + (fy - 0.5) * 1.25)
    camp_homes.append((x, y))
    front = math.radians(facing_to(x, y, (cx, cy)) + rng.uniform(-12, 12))
    if kind == 'hull':
        models.append(houses.hull_house(f'camp_{k}_hull', x, y, height_at(x, y), front, 20 + k, length=760))
    else:
        models.append(houses.salvage_house(f'camp_{k}_lean', x, y, height_at(x, y), front, 20 + k, 480, 400, 'lean',
                                           windows=1))
x, y = place('B3', 0.8, 0.25)
models.append(houses.shop_house('camp_shop', x, y, height_at(x, y), math.radians(facing_to(x, y, (cx, cy))), 25))
decoration('hes_ash_watchtower', *place('B3', 0.18, 0.55), facing=int(rng.integers(0, 360)))
# S1 (P4's QUESTS, the integrator's follow-ups 24 and 39). The stolen crawler stands in the scrapyard, its door the
# console (event 26); started, it rolls home: from S1 (100101) the scrapyard's is hidden and the camp's shown (their
# faces' cogs, CRAWLER_COGS: evt.SetFacetBit Invisible and Untouchable; the camp's starts hidden). The camp's stands
# at the end of the south track, its door toward the fire. Round the camp a ring of invisible pressure plates
# (event 27, CAMP_EDGE) a step above the ground: the sentry's warning shout, which gives S1.
CRAWLER_COGS = {'scrapyard_crawler': 9201, 'camp_crawler': 9202}
HIDDEN_MODELS = {'camp_crawler'}
FACE_ATTRIBUTES = {'camp_edge': 0x04002000}          # PressurePlate, Invisible
CONSOLE_EVENT, CAMP_EDGE_EVENT, BAY_EVENT = 26, 27, 28
models.append(houses.hull_house('camp_crawler', cx, cy - 1000, height_at(cx, cy - 1000), math.radians(90), 0,
                                length=820))
camp_crawler = (cx, cy - 1400)
edge = Model('camp_edge')
EDGE_RX, EDGE_RY, EDGE_W, EDGE_N = 2350.0, 2150.0, 300.0, 72
ring_points = []
for k in range(EDGE_N + 1):
    a = 2 * math.pi * k / EDGE_N
    ring_points.append([(cx + (EDGE_RX + d) * math.cos(a), cy + (EDGE_RY + d) * math.sin(a)) for d in (0.0, EDGE_W)])
for (p0, p1), (q0, q1) in zip(ring_points, ring_points[1:]):
    corners = [(px, py, height_at(px, py) + 10) for px, py in (p0, q0, q1, p1)]
    for tri in ((corners[0], corners[1], corners[2]), (corners[0], corners[2], corners[3])):
        edge.facing(list(tri), 'hoplate', (0, 0, 1), event=CAMP_EDGE_EVENT)
models.append(edge)

# The scrapyard's work crane and the forward outpost.
(cx, cy), _, _, _ = SITES['scrapyard']
decoration('hes_salvage_crane', cx + 300, cy - 200, facing=200)
# The stolen crawler (S1), its door toward the yard's west gate, the console (event 26); the salvage heaps scattered
# before it was placed stay off it.
scrap_crawler = (cx - 900, cy + 250)
models.append(houses.hull_house('scrapyard_crawler', *scrap_crawler, height_at(*scrap_crawler), math.radians(180),
                                CONSOLE_EVENT, length=820))
entities[:] = [e for e in entities if e['name'] != 'hes_salvage_heap'
               or math.hypot(e['position']['x'] - scrap_crawler[0] - 410, e['position']['y'] - scrap_crawler[1]) > 800]
# The crawler's bay: a low plating slab under the hull (event 28), the click left once she has gone: her track marks.
bay = Model('scrapyard_bay')
bay_x0, bay_x1, bay_y0, bay_y1 = scrap_crawler[0] - 60, scrap_crawler[0] + 900, scrap_crawler[1] - 330, \
    scrap_crawler[1] + 330
bay_top = height_at(*scrap_crawler) + 4
bay_low = min(height_at(px, py) for px in (bay_x0, bay_x1) for py in (bay_y0, bay_y1)) - 12
bay_corners = [(bay_x0, bay_y0), (bay_x1, bay_y0), (bay_x1, bay_y1), (bay_x0, bay_y1)]
for (ax, ay), (bx, by) in zip(bay_corners, bay_corners[1:] + bay_corners[:1]):
    out = (by - ay, ax - bx)                           # the outward normal (the corners run anticlockwise)
    bay.facing([(ax, ay, bay_low), (bx, by, bay_low), (bx, by, bay_top), (ax, ay, bay_top)], 'hoplate', (*out, 0))
bay.facing([(x, y, bay_top) for x, y in bay_corners], 'hoplate', (0, 0, 1), event=BAY_EVENT)
models.append(bay)
(ox, oy), _, _, _ = SITES['outpost']
decoration('hes_kreegan_outpost', ox, oy, facing=30)
decoration('hes_alarm_pylon', *place('H4', 0.62, 0.62))


# Landfall (design/kreegan_world/zone1/landfall_plan.py): the prefab wall north and east with its gates and towers,
# the houses on the square, the streets and the lanes, the homes cut into the cliffs, the Lift Head and the Landfall
# Stone in the square, the fungus beds and the crawler yard, and the wall turrets' mounts (the turrets themselves are
# actors: Landfall's people, after the dressing).
z = town_level
wall = LANDFALL['wall']
models.append(houses.town_wall('landfall_wall', wall['line'], z, [EAST_GATE, NORTH_GATE],
                               [t['position'] for t in LANDFALL['towers']], height=wall['height'], walk=wall['walk'],
                               gate_w=wall['gate_width'], tower_size=LANDFALL['towers'][0]['size'],
                               inside=TOWN_CENTRE))
TOWER_H = 900.0
TURRETS = {'Ward Turret': 'hes_ward_turret', 'Gate Bastion': 'hes_gate_bastion'}


def outward(x, y):
    """Degrees out of the town from a point on its wall (north or east): straight out, diagonally at the corner."""
    dx = 1 if x > TOWN_HI[0] - 400 else 0
    dy = 1 if y > TOWN_HI[1] - 400 else 0
    return math.degrees(math.atan2(dy, dx))


turret_posts = []                                   # (monster name, x, y, z, outward degrees): the actors, below
for tower in LANDFALL['towers']:                    # turrets on the towers' tops, facing out
    x, y = tower['position']
    turret_posts.append((tower['turret'], x, y, z + TOWER_H, outward(x, y)))
for turret in LANDFALL['walk_turrets']:             # and on the wall-walk between the gates and the corners
    x, y = turret['position']
    turret_posts.append((turret['turret'], x, y, z + wall['height'], outward(x, y)))
for kind, x, y, top, out in turret_posts:           # the fixed mount; the turret on it is a Stationary actor
    decoration(TURRETS[kind] + '_mount', x, y, facing=out + 270, sink=height_at(x, y) - top)

SIGNS = {1: 'hfsignarms', 2: 'hfsignemit', 3: 'hfsignprov', 4: 'hfsignlamp', 5: 'hfsignward'}   # services only;
                                                    # the teachers live in plain houses, as in MM6-8
for house in LANDFALL['houses']:
    number, kind, (hx, hy) = house['number'], house['kind'], house['position']
    width, depth, front = house['width'], house['depth'], DOOR_ANGLE[house['door']]
    fx, fy = hx + math.cos(front) * depth / 2, hy + math.sin(front) * depth / 2       # the front wall's middle
    name = f'landfall_{number}'
    style, skin = house['style'], 'prefab' if house['finish'] == 'light' else 'prefab_dark'
    if style == 'cliff':                            # its front 100 out from the cliff's foot, the rest in the rock
        models.append(houses.cliff_house(name, fx, fy, z, front, 50 + number, width, depth, skin=skin))
    elif style == 'hab':
        models.append(houses.hab_house(name, fx, fy, z, front, 50 + number, width, depth, sign=SIGNS.get(number)))
    elif style == 'tall':
        models.append(houses.tall_house(name, fx, fy, z, front, 50 + number, width, depth, skin=skin,
                                        sign=SIGNS.get(number)))
    elif style == 'hall':
        models.append(houses.hall_house(name, fx, fy, z, front, 50 + number, width, depth, skin=skin))
    elif number in SIGNS:                           # the gable and lean-to shops carry their sign over the door
        models.append(houses.shop_house(name, fx, fy, z, front, 50 + number, sign=SIGNS[number], width=width,
                                        depth=depth, skin=skin))
    else:
        models.append(houses.salvage_house(name, fx, fy, z, front, 50 + number, width, depth, style, windows=2,
                                           pipe=False, skin=skin))

# The square: the Lift Head facing Main Street, the Landfall Stone, the stalls, braziers and light posts.
lx, ly = LANDFALL['lift']
models.append(houses.lift_head('lift_head', lx + 330, ly, z, 0.0, event=14))
# Where the lift up from the Undervault sets the party down: in front of the cage, facing Main Street.
lift_arrival = (lx + 330 + 140 + 400, ly, z, 0)
decoration('hes_founder_intact', *LANDFALL['stone'], facing=270, event=50)        # 50: no house is number 0
for k, (x, y) in enumerate(LANDFALL['stalls']):
    decoration('hes_market_goods_colony', x, y, facing=270 + 90 * k)
sx0, sy0, sx1, sy1 = LANDFALL['square']
# Outdoor fixtures are the dimmer variants (decorations.yml), and few: two braziers by the Stone, a post on each street.
for x, y in ((sx0 + 150, sy1 - 150), (sx1 - 150, sy1 - 150)):
    decoration('hes_brazier_out', x, y)
for x, y in ((-12600, -15000), (-16220, -12900)):
    decoration('hes_light_post_out', x, y)           # on Main Street and North Street
# The fountain and two stat barrels (as MM7's: +2 to a stat once, then empty until the map is reset), in the open
# strip between Salvage & Arms and Stone Lane, west of the square.
FOUNTAIN = (-18300, -15530)
decoration('hes_fountain', *FOUNTAIN, facing=0, event=80)
STAT_BARRELS = [(81, 'red', 'Might', -18850), (82, 'green', 'Endurance', -17750)]
for event, colour, _, bx in STAT_BARRELS:
    decoration(f'hes_stat_barrel_{colour}', bx, FOUNTAIN[1] - 60, facing=270, event=event, cog=event)
# The fungus beds: four long beds of pale fungi on composted ash, water drums at their end.
yards = {y['name']: y for y in LANDFALL['yards']}
bx0, by0, bx1, by1 = yards['Fungus beds']['rect']
beds = Model('fungus_beds')
for k in range(4):
    yc = by0 + 150 + k * (by1 - by0 - 300) / 3
    houses.block(beds, houses.Frame(0, 0, z, -math.pi / 2), bx0 + 150, yc - 90, bx1 - 450, yc + 90, -20, 60,
                 'hhplinth', top='hofungus')
models.append(beds)
for k in range(3):
    decoration('hes_drum_clean', bx1 - 250, by0 + 250 + k * 300)
# The crawler yard: two parked crawlers, a repair gantry over them, fuel tanks and spares.
cx0, cy0, cx1, cy1 = yards['Crawler yard']['rect']
for k, yc in enumerate((cy0 + 450, cy1 - 450)):
    models.append(houses.hull_house(f'yard_crawler_{k}', cx0 + 200, yc, z, 0.0, 0, length=820, skin='prefab'))
decoration('hes_gantry_segment', (cx0 + cx1) / 2 + 300, (cy0 + cy1) / 2, facing=0)
for k in range(2):
    decoration('hes_fuel_tank', cx1 - 250, cy0 + 300 + k * 360)
decoration('hes_container', cx1 - 300, cy1 - 300, facing=90)

# --- Dressing: Landfall's greenery and props, and the wild growths ----------------------------------------------------
# From the MM towns' decorations (Ravenshore, Harmondale, New Sorpigal: tall growths alone 800-1300 apart on open
# ground, low clumps always in groups, beds by walls and rings round centrepieces, few street props) in Hesper's
# terms: nothing grows wild but black glass and wire scrub, so the town's greenery is what the settlers cultivate
# (fungus trees, clumps and planters), and the countryside has glass trees, wire thickets and ash-stone pillars.
dress = np.random.default_rng(1022)
DOOR_STEP_HALF = houses.DOOR_W / 2 + 50             # the door steps' half width (houses.door_steps)


def house_box(house):
    """A plan house's footprint (x0, y0, x1, y1)."""
    (hx, hy), across = house['position'], house['door'] in ('north', 'south')
    half_x, half_y = (house['width'] / 2, house['depth'] / 2) if across else (house['depth'] / 2, house['width'] / 2)
    return hx - half_x, hy - half_y, hx + half_x, hy + half_y


town_boxes = [house_box(house) for house in LANDFALL['houses']]
doors = [(h['position'][0] + math.cos(DOOR_ANGLE[h['door']]) * h['depth'] / 2,          # each door, facing out
          h['position'][1] + math.sin(DOOR_ANGLE[h['door']]) * h['depth'] / 2,
          math.cos(DOOR_ANGLE[h['door']]), math.sin(DOOR_ANGLE[h['door']])) for h in LANDFALL['houses']]
open_ground = list(street_rects.values()) + [tuple(LANDFALL['square'])] + [tuple(y['rect']) for y in LANDFALL['yards']]


def spaced(x, y, gap, kind=None):
    """No decoration of the same kind (its name, or a variant's: hes_fungus_tree_b is a hes_fungus_tree) within gap,
    nor any other within 200 (gap if smaller)."""
    return all(math.hypot(x - e['position']['x'], y - e['position']['y'])
               >= (gap if kind and e['name'].startswith(kind) else min(gap, 200.0)) for e in entities)


def in_town_clear(x, y, house_gap, gap, kind=None, street_gap=60):
    """A free spot on Landfall's floor: off the streets, the square and the yards, house_gap from every house (their
    door steps reach 320 out), away from the wall and the cliffs' feet, gap from other decorations."""
    if not (TOWN_LO[0] + 350 < x < TOWN_HI[0] - 450 and TOWN_LO[1] + 350 < y < TOWN_HI[1] - 450):
        return False
    if any(x0 - street_gap < x < x1 + street_gap and y0 - street_gap < y < y1 + street_gap
           for x0, y0, x1, y1 in open_ground):
        return False
    if any(x0 - house_gap < x < x1 + house_gap and y0 - house_gap < y < y1 + house_gap
           for x0, y0, x1, y1 in town_boxes):
        return False
    if any(-50 < (x - dx) * ox + (y - dy) * oy < 700 and abs(-(x - dx) * oy + (y - dy) * ox) < 450
           for dx, dy, ox, oy in doors):
        return False                                # the door steps and the way in: 700 out, 900 wide
    return spaced(x, y, gap, kind)


def level_ground(x, y, rise=60.0):
    z = height_at(x, y)
    return all(abs(height_at(x + dx, y + dy) - z) < rise for dx, dy in ((150, 0), (-150, 0), (0, 150), (0, -150)))


def scatter(name, count, region, accept, tries=4000, facing=None):
    """Place up to count of name (or, for a list, its variants in turn) at random spots the test accepts."""
    names = name if isinstance(name, list) else [name]
    placed = 0
    for _ in range(tries):
        if placed >= count:
            break
        x, y = dress.uniform(region[0], region[2]), dress.uniform(region[1], region[3])
        if accept(x, y):
            decoration(names[placed % len(names)], x, y, facing=facing)
            placed += 1
    return placed


dressing = {}
town_region = (*TOWN_LO, *TOWN_HI)
# A ring of eight fungus clumps round the fountain (New Sorpigal rings its fountains with flowers).
for k in range(8):
    a = k * math.pi / 4 + math.pi / 8
    decoration('hes_fungus_clump', FOUNTAIN[0] + math.cos(a) * 300, FOUNTAIN[1] + math.sin(a) * 300)
# Beds along the house fronts: four clumps beside the steps of every service, teacher and home with a front wall.
for house in LANDFALL['houses']:
    if house['style'] in ('cliff', 'hall'):
        continue
    (hx, hy), front = house['position'], DOOR_ANGLE[house['door']]
    out_x, out_y = math.cos(front), math.sin(front)
    along_x, along_y = -out_y, out_x
    w = house['width'] / 2
    door_x = {'hab': 0.0, 'tall': -w * 0.3}.get(house['style'], -w * 0.18 if house['number'] in SIGNS else -w * 0.25)
    fx, fy = hx + out_x * (house['depth'] / 2 + 90), hy + out_y * (house['depth'] / 2 + 90)
    for k in range(4):
        t = door_x + DOOR_STEP_HALF + 90 + k * 110
        if t > w - 50:
            break
        decoration('hes_fungus_clump', fx + along_x * t, fy + along_y * t)
# A formal bed of twelve on the square's north-east corner, opposite the stall in its north-west.
for i in range(4):
    for j in range(3):
        decoration('hes_fungus_clump', -14900 + i * 120, -15500 - j * 120)
# The fungus trees, alone on open ground (their caps, about 2 m across, clear of the streets and the houses: none on
# a street's verge); the planters by the paved streets; a condenser beside some homes.
dressing['hes_fungus_tree'] = scatter(
    ['hes_fungus_tree', 'hes_fungus_tree_b', 'hes_fungus_tree_c'], 24, town_region,
    lambda x, y: (in_town_clear(x, y, 400, 850, 'hes_fungus_tree', street_gap=350)
                  and level_ground(x, y)))
# The planters on the paved streets' verges, square to the street (their length along it), clear of the doors.
main, north = street_rects['Main Street'], street_rects['North Street']
verges = ([(x, y, 0) for x in np.arange(main[0] + 300, main[2] - 300, 500) for y in (main[3] + 130, main[1] - 130)] +
          [(x, y, 90) for y in np.arange(north[1] + 300, north[3] - 300, 500)
           for x in (north[0] - 130, north[2] + 130)])
planters = 0
for x, y, facing in verges:
    if planters < 8 and in_town_clear(x, y, 80, 1200, 'hes_fungus_planter'):
        decoration('hes_fungus_planter', x, y, facing=facing)
        planters += 1
dressing['hes_fungus_planter'] = planters
for house in LANDFALL['houses']:
    if house['kind'] != 'home' or house['style'] == 'cliff':
        continue
    x0, y0, x1, y1 = house_box(house)
    for x, y in ((x1 + 110, (y0 + y1) / 2), (x0 - 110, (y0 + y1) / 2)):
        if in_town_clear(x, y, 60, 300, 'hes_water_condenser'):
            decoration('hes_water_condenser', x, y)
            break
dressing['hes_hand_cart'] = scatter('hes_hand_cart', 2, town_region,
                                    lambda x, y: in_town_clear(x, y, 160, 1500, 'hes_hand_cart') and level_ground(x, y))
# Black glass along the cliffs' feet between the cliff homes (MM edges its plots with rocks).
for k in range(12):
    x, y = (TOWN_LO[0] + 220, dress.uniform(TOWN_LO[1] + 600, TOWN_HI[1] - 900)) if k % 2 else \
        (dress.uniform(TOWN_LO[0] + 600, TOWN_HI[0] - 1200), TOWN_LO[1] + 220)
    if spaced(x, y, 450, 'hes_glass_shards') and not any(x0 - 250 < x < x1 + 250 and y0 - 250 < y < y1 + 250
                                     for x0, y0, x1, y1 in town_boxes):
        decoration('hes_glass_shards', x, y)
# The wild: glass trees, wire thickets and ash-stone pillars across the zone, off the roads, the buildings and the
# steep ground, sparser than MM's countryside (a dead world), and a little thicker round Landfall's walls.
whole = (-BOUND + 500, -BOUND + 500, BOUND - 500, BOUND - 500)
def wild(gap, kind):
    return lambda x, y: clear(x, y, 300) and level_ground(x, y, 120) and spaced(x, y, gap, kind)



around_town = (TOWN_LO[0] - 600, TOWN_LO[1] - 600, TOWN_HI[0] + 2500, TOWN_HI[1] + 2500)
dressing['glass trees by Landfall'] = scatter('hes_glass_tree', 14, around_town, wild(700, 'hes_glass_tree'))
dressing['hes_glass_tree'] = scatter('hes_glass_tree', 110, whole, wild(900, 'hes_glass_tree'))
dressing['hes_wire_thicket'] = scatter('hes_wire_thicket', 150, whole, wild(600, 'hes_wire_thicket'))
dressing['hes_ash_hoodoo'] = scatter('hes_ash_hoodoo', 40, whole, wild(1500, 'hes_ash_hoodoo'))
# Nothing wild stands in the brine or on its shore cells: dropped after the scatter, so its draws stay as they were.
WILD = {'hes_glass_tree', 'hes_wire_thicket', 'hes_ash_hoodoo'}
wet = np.pad((brine_mask | (brine_shore > 0)), 1)


def on_brine(placement):
    col, row = int((placement['x'] + 32768) // STEP), int((32768 - placement['y']) // STEP)
    return bool(wet[row:row + 3, col:col + 3].any())


entities[:] = [e for e in entities if not (e['name'] in WILD and on_brine(e['position']))]
model_placements[:] = [m for m in model_placements if not (m['name'] in WILD and on_brine(m))]

# --- Landfall's people: the wall turrets, the town guard and the villagers -------------------------------------------
# Actors of the Hesper monster rows the stage installs (hesper_stage/monsters.yml; design/kreegan_world/MONSTERS.md:
# 10065-10066 the turrets, 10067-10069 the guard's three ranks, 10073-10078 the villagers' six outfits). Friendly:
# their ids lie past the relation table, so none is hostile to the party. Posted actors (the turrets, the gate
# guards, the Lift Head's and the Warden's Post's) are placed immobile: with their monsters' `post` tactic
# (hesper_stage/monsters.yml) they hold the spot and its facing but leave it to fight within a leash; the patrol and
# the villagers wander as MM's street people do (Med: 2 560 round their start). Density from MM's towns: a few guards at each post, villagers
# spread one or two to a street, none starting in front of a door.
MONSTER_ROWS = {int(row[0]): row for row in (line.split('\t') for line in
                (ROOT / 'design/kreegan_world/data/monster_data.txt').read_text().splitlines()) if row[0].isdigit()}
MONSTER_SIZES = {m['id']: (m['radius'], m['height']) for m in yaml.safe_load(
    (ROOT / 'level_generation/projects/hesper_stage/monsters.yml').read_text())['monsters']}
DECORATION_RADII = {d['name']: d.get('radius', 0) for d in yaml.safe_load(
    (ROOT / 'level_generation/projects/hesper_stage/decorations.yml').read_text())['decorations']}
WARD_TURRET, GATE_BASTION, GUARD, SERGEANT, WARDENS_GUARD = 10065, 10066, 10067, 10068, 10069
VILLAGERS = [10073, 10076, 10074, 10077, 10075, 10078]        # male A, female A, male B, ...: mixed in turn
GROUPS = {'turret': 20, 'guard': 21, 'villager': 22,           # for later scripting (alarms, the town turning)
          'ashrunner_folk': 33}                                # the camp's folk, shown from S1 (follow-up 39)
actors = []


def house_doors(house):
    """The house's door (its real place along the front) and the front wall's middle, each with its outward normal."""
    (hx, hy), front = house['position'], DOOR_ANGLE[house['door']]
    out_x, out_y = math.cos(front), math.sin(front)
    mid_x, mid_y = hx + out_x * house['depth'] / 2, hy + out_y * house['depth'] / 2
    w = house['width'] / 2
    door_x = {'hab': 0.0, 'tall': -w * 0.3, 'cliff': 0.0, 'hall': 0.0}.get(
        house['style'], -w * 0.18 if house['number'] in SIGNS else -w * 0.25)
    ex, ey = -math.sin(front), math.cos(front)                    # houses.Frame's local x
    return [(mid_x + ex * door_x, mid_y + ey * door_x, out_x, out_y), (mid_x, mid_y, out_x, out_y)]


door_ways = [door for house in LANDFALL['houses'] for door in house_doors(house)]
lift_axis = (lx, ly)                                            # the Lift Head's tower (houses.lift_head: radius 330)
x0_beds, y0_beds, x1_beds, y1_beds = yards['Fungus beds']['rect']


def actor_spot_clear(x, y, radius, posted):
    """Room for an actor: off every house and its door's way in (700 out, 900 wide; a wanderer only off the first
    350), off the Lift Head and the fungus beds, clear of the decorations' collision and of the other actors."""
    if any(x0 - radius - 30 < x < x1 + radius + 30 and y0 - radius - 30 < y < y1 + radius + 30
           for x0, y0, x1, y1 in town_boxes):
        return False
    reach = 700 if posted else 350
    if any(-50 < (x - dx) * ox + (y - dy) * oy < reach and abs(-(x - dx) * oy + (y - dy) * ox) < 450 + radius
           for dx, dy, ox, oy in door_ways):
        return False
    if math.hypot(x - lift_axis[0], y - lift_axis[1]) < 330 + 60 + radius or \
            (lx + 330 - 20 < x < lx + 330 + 140 + 500 and abs(y - ly) < 200 + radius):   # the cage and the arrival
        return False
    if x0_beds - radius < x < x1_beds + radius and y0_beds - radius < y < y1_beds + radius:
        return False
    for e in entities:
        r = DECORATION_RADII.get(e['name'], 0)
        if r and math.hypot(x - e['position']['x'], y - e['position']['y']) < r + radius + 30:
            return False
    gap = 200 if posted else 500                                 # posts may stand in pairs; wanderers spread out
    return all(math.hypot(x - a['position']['x'], y - a['position']['y']) >= gap for a in actors)


moved = []


def actor(monster, x, y, facing, top=None, posted=False, name='', group='guard', search=True):
    """Place a monster actor at (x, y) facing `facing` (degrees, 0 east, counter-clockwise), standing on `top` (a
    wall-walk or tower top) or the ground; a ground actor whose spot is taken moves to the nearest free one."""
    radius, height = MONSTER_SIZES[monster]
    if top is None and search and not actor_spot_clear(x, y, radius, posted):
        for step in range(1, 16):
            ring = [(x + 40 * step * math.cos(a), y + 40 * step * math.sin(a))
                    for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
            free = [p for p in ring if actor_spot_clear(*p, radius, posted)]
            if free:
                moved.append((name or monster, round(40 * step)))
                x, y = free[0]
                break
        else:
            raise SystemExit(f'no room for actor {monster} {name} near {x:.0f}, {y:.0f}')
    row = MONSTER_ROWS[monster]
    z_value = height_at(x, y) if top is None else top
    actors.append({'actor_index': len(actors), 'name': name, 'npc_id': 0, 'attributes': 0, 'hp': int(row[4]),
                   'hostility_type': 0, 'monster_info_id': monster, 'monster_id': monster, 'radius': radius,
                   'height': height, 'move_speed': 0 if posted else int(row[13]),
                   'position': {'x': int(round(x)), 'y': int(round(y)), 'z': int(round(z_value))},
                   'initial_yaw_units': int(round((facing % 360) / 360 * 2048)) % 2048, 'immobile': posted,
                   'sprite_ids': [0, 0, 0, 0], 'sector_id': 0, 'current_action_animation': 0, 'carried_item_id': 0,
                   'group': GROUPS[group], 'ally': 0, 'unique_name_index': 0})


# The turrets on their mounts (4 Gate Bastions on the gate towers, 7 Ward Turrets on the corner and end towers and
# the wall-walk), facing out.
for kind, x, y, top, out in turret_posts:
    actor(GATE_BASTION if kind == 'Gate Bastion' else WARD_TURRET, x, y, out, top=top, posted=True, group='turret')
# Density from MM7's and MM8's towns (README, Landfall's people): about 0.16 peasants per million square units of the
# houses' bounding box (0.12-0.23) and in the guarded towns (Ravenshore, Tatalia, Shadowspire) about one guard to two
# peasants. Landfall's houses cover about 10 800 x 8 150 (88 million): 16 villagers and 8 guards, 4 of them the gate
# posts. MM keeps no guards on its walls, so the wall-walk has the turrets only.
# The gates: each has one opening; two guards outside it, either side of the road, facing the way in. The East Gate's
# south guard is the arrival's contact (STARPORT_REACH.md: he sends the strangers to the Warden's Post; his talk
# waits for Hesper NPCs).
gate_out = LANDFALL['towers'][0]['size'] / 2 + 250                # beyond the gate towers' outer faces
ex_, ey_ = EAST_GATE
actor(GUARD, ex_ + gate_out, ey_ - 420, 0, posted=True, name='East Gate guard')
actor(GUARD, ex_ + gate_out, ey_ + 420, 0, posted=True, name='East Gate guard (north)')
nx_, ny_ = NORTH_GATE
for side in (-1, 1):
    actor(GUARD, nx_ + side * 420, ny_ + gate_out, 90, posted=True, name='North Gate guard')
# In the town: two sergeants either side of the Lift Head's cage, facing Main Street (the lift is closed to strangers
# until M2), one of the Warden's guard beside the Warden's Post's door, and a patrol on Main Street (it wanders; patrol
# routes wait for the engine).
for side in (-1, 1):
    actor(SERGEANT, lx + 330 + 220, ly + side * 340, 0, posted=True, name='Lift Head sergeant')
warden = next(h for h in LANDFALL['houses'] if h['number'] == 5)
wx0, wy0, wx1, wy1 = house_box(warden)
actor(WARDENS_GUARD, wx1 + 60, wy1 + 130, 90, posted=True, name="Warden's Post guard")       # the door's side
actor(GUARD, -12800, -15400, 180, name='Main Street patrol')
# The villagers, spread through the town as MM's peasants are: three on the square, two or three to a street, one
# to a lane, mixed outfits in turn.
VILLAGER_SPOTS = [(-16300, -16500), (-14900, -15500), (-16200, -15400),                       # the square
                  (-11600, -15300), (-13000, -15550), (-13900, -15250),                       # Main Street
                  (-15700, -13300), (-15900, -14600),                                         # North Street
                  (-18900, -16150), (-17400, -16300),                                         # Stone Lane
                  (-18600, -13950),                                                           # Hab Lane
                  (-19800, -14800), (-19750, -17800),                                         # Cliff Lane
                  (-17800, -19450), (-13600, -19450),                                         # South Lane
                  (-18700, -15950)]                                                           # by the fountain
for k, (x, y) in enumerate(VILLAGER_SPOTS):
    actor(VILLAGERS[k % len(VILLAGERS)], x, y, float(dress.uniform(0, 360)), name='villager', group='villager')
# Six villagers are Landfall's street people (P4's NPCS 9533-9538, hesper_stage/npcs_landfall.yml; the integrator's
# follow-up 36): villager k (VILLAGER_SPOTS' order: the square, Main Street, North Street, Stone Lane, Cliff Lane,
# South Lane), the outfit's sex matching the face (even k male, odd female).
STREET_PEOPLE = {1: 9533, 4: 9534, 7: 9535, 8: 9536, 11: 9537, 14: 9538}     # Lune, Merrit, Nessa, Kito, Pria, Quill
villager_actors = [a for a in actors if a['name'] == 'villager']
for k, npc in STREET_PEOPLE.items():
    villager_actors[k]['npc_id'] = npc
house_extent = (min(b[0] for b in town_boxes), min(b[1] for b in town_boxes),
                max(b[2] for b in town_boxes), max(b[3] for b in town_boxes))
population = {'turrets': len(turret_posts), 'guards': sum(a['monster_id'] in (GUARD, SERGEANT, WARDENS_GUARD)
                                                          for a in actors),
              'villagers': len(VILLAGER_SPOTS), 'moved': moved, 'house_extent': house_extent}

(tcx, tcy), _, _, _ = SITES['terminal']
terminal_arrival = (tcx - 1300 - 260 - 700, tcy, apron_level, 180)       # in front of the doors, facing the apron
(scx, scy), _, (snx, sny) = station[0], station[1], station[2]
station_arrival = (scx + snx * 650, scy + sny * 650, station_level, math.degrees(math.atan2(sny, snx)) % 360)


CHESTS = {'chest_c': 'hes_colonial_locker', 'chest_k': 'hes_kreegan_pod_chest', 'chest_a': 'hes_ashrunner_crate'}
loot = []
chest_event = 40
for kind, cell, fx, fy, label, group in detail.PLACES:
    if kind not in CHESTS:
        continue
    x, y = place(cell, fx, fy)
    index = len(loot)
    decoration(CHESTS[kind], x, y, event=chest_event)
    loot.append({'source_id': f'hesper:out1:chest_{index}', 'source_object_index': index,
                 'source_name': label.split(',')[0], 'position': {'x': int(x), 'y': int(y), 'z': int(height_at(x, y))},
                 'container_id': index, 'kind': 'chest', 'presentation': CHESTS[kind].replace('hes_', ''),
                 'random_treasure_level': 1, 'treasure_type': 0, 'gold': 80, 'gold_only': False, 'random': True,
                 'ai_drop': False, 'trap_level': 0, 'should_repopulate': False, 'fixed_items': [],
                 'remove_when_empty': False})
    EVENTS[chest_event] = (label.split(',')[0], f'evt.OpenChest({index})')
    chest_event += 1

# --- The arrival (2): the wreck, its debris trail, the stash, the drones, the party start (README "The arrival") -----
# The hull is a model building (invisible collision box); a click on it is the Pilot (event 85, his console in the
# open hatch). The debris trail runs from the first impact on the crater's north-east floor, past the roof hatch, to
# the hull: plates, the torn-off wing, an engine nacelle, cargo, smoke (the native emitter decoration).
WRECK_EVENT, ARRIVAL_LOAD_EVENT, DRONE_TIMER_EVENT = 85, 86, 87
ARRIVAL_DRONES, ARRIVAL_DRONE_GROUP = 10050, 70           # the Seeker Drones that come down on the smoke
building('hes_lander_wreck', *wreck_centre, WRECK_DIRECTION, event=WRECK_EVENT, parts=[(0.0, 0.05, 0.66, 0.5)])
# The crater rim's glass and the wild dressing scattered before the wreck was placed stay off the hull and its shelf
# (dropped after the scatter, so its draws are unchanged).
entities[:] = [e for e in entities if e['name'] not in WILD | {'hes_glass_shards', 'hes_glass_boulder'}
               or math.hypot(e['position']['x'] - wreck_centre[0], e['position']['y'] - wreck_centre[1]) > 900]
wreck_low, wreck_high = model_bounds('hes_lander_wreck')
out_x, out_y = math.cos(math.radians(WRECK_DIRECTION)), math.sin(math.radians(WRECK_DIRECTION))
nose_x, nose_y = math.cos(math.radians(wreck_nose)), math.sin(math.radians(wreck_nose))
hatch = (wreck_centre[0] + out_x * (wreck_high[2] - wreck_low[2]) * 0.36,
         wreck_centre[1] + out_y * (wreck_high[2] - wreck_low[2]) * 0.36)


def smoke(x, y, rise=150):
    entities.append({'entity_index': 0, 'name': 'smoke', 'decoration_list_id': 22, 'ai_attributes': 0,
                     'position': {'x': int(x), 'y': int(y), 'z': int(height_at(x, y) + rise)}, 'facing': 0,
                     'event_id_primary': 0, 'event_id_secondary': 0, 'variable_primary': 0,
                     'variable_secondary': 0, 'special_trigger': 0, 'initial_decoration_flag': 0})


for along, up in [(-0.3, 260), (0.05, 330), (0.32, 200)]:   # the hull smoulders: tail, back and the torn nacelle
    smoke(wreck_centre[0] + nose_x * along * (wreck_high[0] - wreck_low[0]),
          wreck_centre[1] + nose_y * along * (wreck_high[0] - wreck_low[0]), up)
debris = [('hes_fallen_plates', 18, 0.58, None), ('hes_fallen_plates', -20, 0.42, None),
          ('hes_lander_wing', -62, 0.38, 25.0), ('hes_fallen_plates', -95, 0.45, None),
          ('hes_lander_engine', -112, 0.6, 140.0), ('hes_container', -70, 0.62, None),
          ('hes_crate_clean', -100, 0.68, None), ('hes_crate_clean', -105, 0.72, None),
          ('hes_crate_clean', -150, 0.66, None), ('hes_drum_clean', -84, 0.6, None),
          ('hes_drum_clean', -160, 0.62, None), ('hes_luggage_pile', -128, 0.66, None)]
for name, degrees, r, facing in debris:
    x, y = crater_point(degrees, r)
    decoration(name, x, y, facing=facing)
    if name in ('hes_lander_wing', 'hes_lander_engine'):
        smoke(x, y, 80)
# The stash: the cargo locker under the hatch (the Pilot keys it to the party); a chest like the others.
stash = (hatch[0] + out_x * 140 - nose_x * 260, hatch[1] + out_y * 140 - nose_y * 260)
decoration('hes_colonial_locker', *stash, facing=WRECK_DIRECTION, event=chest_event)
loot.append({'source_id': f'hesper:out1:chest_{len(loot)}', 'source_object_index': len(loot),
             'source_name': "The Pilot's stash", 'position': {'x': int(stash[0]), 'y': int(stash[1]),
                                                               'z': int(height_at(*stash))},
             'container_id': len(loot), 'kind': 'chest', 'presentation': 'colonial_locker',
             'random_treasure_level': 1, 'treasure_type': 0, 'gold': 150, 'gold_only': True, 'random': False,
             'ai_drop': False, 'trap_level': 0, 'should_repopulate': False, 'fixed_items': [],
             'remove_when_empty': False})
EVENTS[chest_event] = ("The Pilot's stash", f'evt.OpenChest({len(loot) - 1})')
assert chest_event < 50, 'the chests run into the houses\' events'
# The drones: four Seekers waiting invisible over the crater's north-east floor; the timer (event 87, about 30 s
# after the first arrival) shows them and they come down on the smoke. Hostile by the Aggressor bit and by
# spawns.py's relation; Landfall's turrets and guards are set against them on load (event 86).
for k, (degrees, r) in enumerate([(55, 0.35), (75, 0.5), (35, 0.55), (95, 0.4)]):
    x, y = crater_point(degrees, r)
    actor(ARRIVAL_DRONES, x, y, WRECK_DIRECTION + 180, top=height_at(x, y) + 1100 + 80 * k,
          name='Seeker Drone (arrival)', search=False)
    actors[-1].update({'group': ARRIVAL_DRONE_GROUP, 'attributes': 0x00010000 | 0x00080000})   # Invisible, Aggressor
# The party starts on the rim above the hull's nose, facing Landfall's East Gate.
party_start = crater_point(WRECK_DIRECTION + 8, 1.02)
party_start_z = height_at(*party_start)
party_start_facing = int(round(facing_to(*party_start, EAST_GATE))) % 360
assert math.hypot(party_start[0] - crew_door[0], party_start[1] - crew_door[1]) > 450, 'start on the Crew Ramp door'

# D0's surface door brings the party out of the Crew Ramp door facing the Lift Head (out1_build.json 'arrival');
# the Party Start (new games) is the arrival's, by the wreck (above).
c, s = math.cos(crew_yaw), math.sin(crew_yaw)
arrival = (crew_door[0] + c * 520, crew_door[1] + s * 520)
arrival_z = height_at(*arrival)
direction = int(round(math.degrees(crew_yaw))) % 360            # entity facing is in degrees
for index, entity in enumerate(entities):
    entity['entity_index'] = index + 1
entities.insert(0, {'entity_index': 0, 'name': 'Party Start', 'decoration_list_id': 14, 'ai_attributes': 2,
                    'position': {'x': int(party_start[0]), 'y': int(party_start[1]), 'z': int(party_start_z)},
                    # the engine reads the Party Start's facing in yaw units (2048 a turn), not degrees
                    'facing': round(party_start_facing / 360 * 2048) % 2048, 'event_id_primary': 0,
                    'event_id_secondary': 0, 'variable_primary': 0,
                    'variable_secondary': 0, 'special_trigger': 0, 'initial_decoration_flag': 2})

# --- Hostile monsters: spawns.py places spawns.yml's spawn points and squads (README, "Hostile monsters") -------------
import spawns  # noqa: E402
hostiles = spawns.populate(
    place=place, height_at=height_at, models=models + [colliders], entities=entities, actors=actors,
    road_masks=road_masks, on_brine=on_brine, bound=BOUND, crew_door=crew_door, wall_line=LANDFALL['wall']['line'],
    town_box=(*TOWN_LO, *TOWN_HI),
    features={'chests': [[c['position']['x'], c['position']['y']] for c in loot],
              'dungeons': [list(terminal_arrival[:2]), list(station_arrival[:2]), list(SITES['archive_dome'][0])],
              'items': [list(place(cell, fx, fy)) for kind, cell, fx, fy, _, _ in detail.PLACES
                        if kind in ('item', 'log', 'tablet')],
              'houses': [list(door[:2]) for door in door_ways[::2]], 'start': [arrival[0], arrival[1]],
              'roads': [list(p) for line in paved + tracks for p in resample(line, 512)]})
print('hostiles', hostiles['summary'])

# Fit a thick rock overhang to the grounded pack; the native terrain is its floor.
# Placement's 2D wall mask cannot represent an overhang, so add it after ground placement.
den = Model('gloamling_den')
inner, outer = [], []
fractions = [-1, -.97, -.65, 0, .67, .98, 1]
for k, (x, cy, width) in enumerate([(15500, -10080, 700), (16350, -10100, 760), (17050, -10040, 650)]):
    floor = height_at(x, cy)
    inside, outside = [], []
    for j, (fraction, rise) in enumerate(zip(fractions, [-450, 250, 520, 680, 500, 240, -450])):
        y = cy + width * fraction
        z = min(floor, height_at(x, y)) - 450 if j in (0, 6) else floor + rise
        inside.append((x, y, z))
        outside.append((x + [-100, 0, 300][k], cy + (width + 250) * fraction,
                        z if j in (0, 6) else z + [180, 240, 160][k]))
    inner.append(inside)
    outer.append(outside)
for shell, inward in [(inner, True), (outer, False)]:
    for a, b in zip(shell, shell[1:]):
        for j in range(6):
            quad = [a[j], a[j+1], b[j+1], b[j]]
            wall_normal = np.array([0, (a[j][1] + a[j+1][1]) / 2 + 10080, 600.0])
            if inward:
                wall_normal = -wall_normal
            # Explicit triangles keep the shared rock edges closed on uneven terrain.
            den.facing(quad[:3], 'hicanyon', wall_normal)
            den.facing([quad[0], quad[2], quad[3]], 'hicanyon', wall_normal)
# A continuous mouth rim; rear walls extend well below every terrain triangle.
for j in range(6):
    quad = [inner[0][j], outer[0][j], outer[0][j+1], inner[0][j+1]]
    den.facing(quad[:3], 'hicanyon', (-1, 0, 0))
    den.facing([quad[0], quad[2], quad[3]], 'hicanyon', (-1, 0, 0))
for ring, wall_normal in [(inner[-1], (-1, 0, 0)), (outer[-1], (1, 0, 0))]:     # not `direction`: the arrival's facing
    den.facing(ring, 'hicanyon', wall_normal)
assert len(den.faces) == 62
models.append(den)

# The Ashrunner camp's folk (P4's row 10262, group 33; follow-up 39), after every other actor so the earlier indices
# hold: invisible until S1 (100101: the crawler's console and the load event show them), standing at their places:
# Garrow before the largest hull, Dace before his workbench hull, Old Ketter at the watchtower's foot, Juna by the
# returned crawler, Teg at the camp's south-east edge where the tracks come in. Dace is the teacher row 9224
# (hesper_stage/skills.yml).
ASHRUNNER_FOLK = 10262
(ccx, ccy), _, _, _ = SITES['camp']
toward = lambda home, f: (home[0] + (ccx - home[0]) * f, home[1] + (ccy - home[1]) * f)
CAMP_FOLK = [('Garrow', 9507, toward(camp_homes[2], 0.4)), ('Dace', 9224, toward(camp_homes[4], 0.5)),
             ('Old Ketter', 9581, (ccx - 1600, ccy - 250)), ('Juna', 9582, (camp_crawler[0] + 420, camp_crawler[1])),
             ('Teg', 9580, (ccx + 1500, ccy - 1400))]
for name, npc, (x, y) in CAMP_FOLK:
    actor(ASHRUNNER_FOLK, x, y, facing_to(x, y, (ccx, ccy)), posted=True, name=name, group='ashrunner_folk',
          search=False)
    actors[-1].update({'npc_id': npc, 'attributes': 0x00010000})                    # Invisible until S1

# Keep existing NPC/encounter indices stable when adding the wildlife den.
gloamers = [a for a in actors if a['monster_id'] == 10320]
actors[:] = [a for a in actors if a['monster_id'] != 10320] + gloamers
for index, a in enumerate(actors):
    a['actor_index'] = index

# --- Events -----------------------------------------------------------------------------------------------------------
d00 = json.loads((ROOT / 'level_generation/projects/hesper_d00/source/hes_d00.semantic.json').read_text())


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



door = d00['arrivals']['surface_door']
door_direction = int(round(door['direction_degrees'] / 360 * 2048)) % 2048
EVENTS.update({
    10: ('Crew Ramp door', f'evt.MoveToMap({door["position"][0]}, {door["position"][1]}, {door["position"][2]}, '
                           f'{door_direction}, 0, 0, 0, 0, "hes_d00.blv")'),
    11: ('Starport Terminal', dungeon_entry('hesper_d01', 'hes_d01.blv', 'apron_doors',
                                            "The Terminal's glass doors are jammed shut.")),
    12: ('Pumping Station', dungeon_entry('hesper_d02', 'hes_d02.blv', 'canyon_gate',
                                          'The round hatch will not open. Its valve wheel is seized.')),
    # D10 (hesper_d10 README, "Starport Reach integration"): the dome opens to two restored shards (100022).
    13: ('Colony Archive', 'if IsQBitSet(QBit(100022)) then '
         + dungeon_entry('hesper_d10', 'hes_d10.blv', 'dome_stair', 'The Colony Archive is sealed.')
         + ' else evt.StatusText("Sealed. Four crystal sockets ring the hatch.") end'),
    14: ('Lift Head', 'if IsQBitSet(QBit(100002)) then '
         + dungeon_entry('hesper_undervault', 'hes_undervault.blv', 'lift', '')
         + ' else evt.StatusText("The lift down to the Undervault. A Hesperian guard bars the cage: not until '
         'the Terminal\'s drones stop hunting along the walls.") end'),
    # The founder statue (CR-P3-11, the integrator's follow-up 40): carrying the Founder's Head (11511, D12's Trophy
    # Gallery West) the party sets it back: the item taken, 100301 (Pell's The founder's head, 9695, reads it),
    # autonote 10020, the model swapped to the intact statue (cog 34; the load event keeps it), and once (flag 100730)
    # reputation -5 (MM's sign: good; P4's REPUTATION).
    34: ('Founder statue', 'if IsQBitSet(QBit(100301)) then evt.StatusText("The founder looks out over the old '
         'landing ground again.") elseif HasItem(11511) then RemoveItem(11511) SetQBit(QBit(100301)) '
         'SetAutonote(10020) evt.SetSprite(34, 1, "hes_founder_intact") if not IsQBitSet(QBit(100730)) then '
         'SetQBit(QBit(100730)) AddValue(ReputationInCurrentLocation, -5) end evt.SimpleMessage("You set the '
         'founder\'s head back on its shoulders. For a moment the old landing ground looks like a place people '
         'lived.") else evt.StatusText("A robed colonist in white stone. The head is gone; the neck is broken '
         'clean.") end'),
    # P4's relay_out1_d01 (dialogue/ASTER.md): the relay post beside D1's doors speaks for Aster after M2; after Tear
    # it out (100034) Aster is silent and the post is dead again.
    38: ('Aster relay post', 'if IsQBitSet(QBit(100034)) then evt.StatusText("A dead relay post; something hums '
         'inside.") elseif IsQBitSet(QBit(100003)) then evt.SimpleMessage("Aster, through the relay: \\"I am with '
         'you, as far as my makers\' posts reach.\\"") elseif IsQBitSet(QBit(100002)) then evt.SimpleMessage("Aster, '
         "through the relay: \\\"The Terminal is quiet. Come down to me, travelers. Take the Lift Head in Landfall's square, "
         'then up the Chapel Steps.\\"") else evt.StatusText("A dead relay post; something hums inside.") end'),
})
for k in range(5):
    EVENTS[20 + k] = ('Ashrunner home', 'evt.StatusText("A crawler hull with a tarp door. Nobody answers.")')
# Kesh's stall (house 9458, a vendor: hesper_stage/npcs_landfall.yml), open from S1.
EVENTS[25] = ('Kesh\'s stall', 'if IsQBitSet(QBit(100101)) then evt.EnterHouse(9458) else evt.StatusText("The '
              'Ashrunner trader\'s shop. Shut until the camp trusts you.") end')
# S1 (follow-up 24): the stolen crawler's console in the scrapyard (100101 done, 100221 cleared, autonote 10413): the
# crawler rolls home (the scrapyard's hidden, the camp's shown), the camp's folk come out. The camp's edge: the
# sentry's shout (P4's QUESTS S1, Teg's voice), once a visit (map var 22, cleared on load), gives S1 (100221).
CRAWLER_LUA = ('evt.SetFacetBit(9201, FacetBits.Invisible, true) evt.SetFacetBit(9201, FacetBits.Untouchable, true) '
               'evt.SetFacetBit(9202, FacetBits.Invisible, false) evt.SetFacetBit(9202, FacetBits.Untouchable, false) '
               f'evt.SetMonGroupBit({GROUPS["ashrunner_folk"]}, MonsterBits.Invisible, false)')
# P4's texts (quests/dialogue/ASHRUNNERS.md, "The crawler's console"): the HOME rune, then the empty bay's tracks.
TRACK_MARKS = 'evt.StatusText("Track marks lead north-west, toward the Ashrunners\' camp.")'
EVENTS[CONSOLE_EVENT] = ('The stolen crawler', 'if IsQBitSet(QBit(100101)) then ' + TRACK_MARKS + ' return end '
                         'SetQBit(QBit(100101)) ClearQBit(QBit(100221)) SetAutonote(10413) ' + CRAWLER_LUA +
                         ' evt.SimpleMessage("The crawler\'s cab still smells of ash-smoke and old grease. Its '
                         'console is scratched with Ashrunner marks, and one painted word you can read: HOME. You '
                         'press it. The engine coughs, catches, and the crawler grinds out of the yard, north-west '
                         'across the ash, on its own.")')
EVENTS[BAY_EVENT] = ('The crawler bay', 'if IsQBitSet(QBit(100101)) then ' + TRACK_MARKS + ' end')
EVENTS[CAMP_EDGE_EVENT] = ('The camp\'s edge', 'if IsQBitSet(QBit(100101)) or IsAtLeast(MapVar(22), 1) then return '
                           'end SetValue(MapVar(22), 1) SetQBit(QBit(100221)) evt.SimpleMessage("A shout from the '
                           'camp: \\"Turn around, lamp-folk! Unless you\'ve come about our crawler. The black ones '
                           'dragged it to their scrapyard east of the apron. Bring it home and Garrow will talk to '
                           'you.\\"")')
# Landfall's houses (events 50 + the plan's number) until Hesper's house tables and teachers are in the engine; the
# teachers are PROGRESSION.md's.
TEACHERS = {7: ('Corra', 'Energy Guns', 'Expert'), 8: ('Halder', 'Energy Guns', 'Master'),
            9: ('Edda', 'Energy Blades', 'Expert'), 10: ('Rusk', 'Energy Blades', 'Master'),
            11: ('Fenna', 'Shield Tech', 'Expert'), 12: ('Tove', 'Shield Tech', 'Master'),
            13: ('Nim', 'Hacking', 'Expert'), 14: ('Hollis', 'Hacking', 'Master'),
            16: ('Yara', 'Cybernetics', 'Expert'), 17: ('Teodor', 'Cybernetics', 'Master')}
HOUSE_TEXTS = {
    1: "Salvage & Arms: Kreegan weapons, emitters and armor, and salvage bought by weight.",
    2: 'Emitters: shield emitters and Shield Cells, racked by grade.',
    5: "The Warden's Post: the town guard, the bounty board, and the Warden, who wants the Terminal's drones stopped.",
    15: "Venn's home: the scout keeps food, Stims and Shield Cells for newcomers.",
    28: 'The crawler shed: a stripped crawler on blocks, its tread laid out in pieces on the floor.',
}
CLIFF_TEXT = ('A home cut into the cliff, its door set in a white Ancient frame the settlers salvaged. The family '
              'is at the market.')
for house in LANDFALL['houses']:
    number = house['number']
    if number in TEACHERS:
        who, skill, mastery = TEACHERS[number]
        text = f"{who} teaches {skill} up to {mastery}."
    else:
        text = HOUSE_TEXTS.get(number, CLIFF_TEXT if house['style'] == 'cliff' else
                               'A Hesperian home, its door curtained. The family is at the market.')
    EVENTS[50 + number] = (house['name'], f'evt.StatusText({json.dumps(text)})')
EVENTS[50] = ('Landfall Stone', 'evt.SimpleMessage("The Landfall Stone: the Long Wake\'s landing ring, set in Ancient '
              'plating where the settlers first stepped down. Three names are cut round it, Ilen Varo, Sesha Mar and '
              'Torvan Ek, and for the fourth three small figures round a sphere for the Makers, who left this place '
              'ready for them.")')
EVENTS[80] = ('Drink from the fountain', 'AddValue(CurrentHealth, 25) evt.StatusText("The Ancients\' purifier '
              'still runs: cold, clean water. +25 hit points.")')
for k, (event, colour, stat, _) in enumerate(STAT_BARRELS, 1):
    EVENTS[event] = (f'{colour.title()} barrel', f'if IsAtLeast(MapVar({k}), 1) then evt.StatusText("Empty.") return '
                     f'end AddValue(Base{stat}, 2) SetValue(MapVar({k}), 1) evt.SetSprite({event}, 1, '
                     f'"hes_stat_barrel_empty") evt.StatusText("+2 {stat} (Permanent)")')
EVENTS[84] = hostiles['load_event']                  # the monsters' relations and quest gates (spawns.py)
EVENTS[83] = ('Landfall on load', ' '.join(f'if IsAtLeast(MapVar({k}), 1) then evt.SetSprite({event}, 1, '
                                           f'"hes_stat_barrel_empty") end'
                                           for k, (event, _, _, _) in enumerate(STAT_BARRELS, 1))
              + ' if IsQBitSet(QBit(100301)) then evt.SetSprite(34, 1, "hes_founder_intact") end'
              + ' SetValue(MapVar(22), 0) if IsQBitSet(QBit(100101)) then ' + CRAWLER_LUA + ' end'
              + ''.join(f' if IsQBitSet(QBit({100017 + n})) then evt.SetSprite({90 + n}, 1, '
                        '"hes_crystal_socket_lit") end' for n in range(1, 5)))
for k in range(3):
    EVENTS[35 + k] = ('Colony log tablet', 'evt.StatusText("A crystal slab with faint blue lines.")')
for k in range(signs):
    EVENTS[30 + k] = ('Signpost', 'evt.StatusText("Ancient glyphs point along the roads.")')

# --- The arrival (3): its talk and its events (README "The arrival"; NPCs and topics: hesper_stage/npcs.yml) -------
# 85 the hull: the Pilot (NPC 9001). 55 the Warden's Post: the Warden (9002). The East Gate's south guard is NPC 9003.
# 86 on load: the Pilot's call on the first arrival (map var 20). Landfall's turrets and guards against the drones
# (relation 2 one way, 1 the other: they engage a drone within 2 560, the drones by the walls and the crater rim do not
# march on the town) are world data since 2026-10-23: hesper_stage/relations.yml.
# 87 a timer, 900 game seconds (30 s) after the map loads: the first time (map var 21), the drones appear.
# The wreck goes dark when the Pilot gives the party his core (M4 given, 100204) and stays dark once he is aboard the
# derelict in Hangar Nine (M4 done, 100004: he speaks from D0's events 19 and 34). The stash (event 49) opens always.
# The opening's other people (2026-10-23, P4's dialogue/LANDFALL.md): Sergeant Ost (9521) on the first Lift Head
# sergeant, the North Gate guard (9522) on the first North Gate guard, Venn (9513) at her home's door (house 15,
# event 65; her shop, house 9460, waits for the scouts' houses).
PILOT, WARDEN, GATE_GUARD = 9001, 9002, 9003
OST, NORTH_GUARD, VENN = 9521, 9522, 9513
EVENTS[WRECK_EVENT] = ('The wrecked lander', 'if IsQBitSet(QBit(100004)) then evt.StatusText("The wreck\'s console '
                       'is dark. The Pilot is aboard the lander in Hangar Nine now.") elseif IsQBitSet(QBit(100204)) '
                       'then evt.StatusText("The wreck\'s console is dark. The Pilot rides in your pack.") else '
                       f'evt.SpeakNPC({PILOT}) end')
EVENTS[55] = ("The Warden's Post", f'evt.SpeakNPC({WARDEN})')
EVENTS[65] = ("Venn's home", 'evt.EnterHouse(9460)')        # her shop, the scouts' list (vendor 9460, follow-up 41)
# Houses 3 and 4 (hesper_stage/npcs_landfall.yml): Mother Ama's Provisions (vendor 9450) and Lorn's Last Lamp (the
# inn, house 9451). Houses 1 and 2 enter Salvage & Arms and the Emitters through skills.yml's events.
EVENTS[53] = ('Provisions', 'evt.EnterHouse(9450)')
EVENTS[54] = ('The Last Lamp', 'evt.EnterHouse(9451)')
# Landfall's home residents (P4's NPCS 9523-9532; follow-up 36): the cliff homes 18-24 and the family homes 25-27 are
# houses 9461-9470 (hesper_stage/npcs_landfall.yml), one resident each.
for number in range(18, 28):
    EVENTS[50 + number] = (EVENTS[50 + number][0], f'evt.EnterHouse({9461 + number - 18})')
next(a for a in actors if a['name'] == 'East Gate guard')['npc_id'] = GATE_GUARD
next(a for a in actors if a['name'] == 'Lift Head sergeant')['npc_id'] = OST
next(a for a in actors if a['name'] == 'North Gate guard')['npc_id'] = NORTH_GUARD
ARRIVAL_LUA = [
    f'RegisterMapOnLoadEvent({ARRIVAL_LOAD_EVENT}, "The arrival on load", function() '
    'if not IsAtLeast(MapVar(20), 1) then SetValue(MapVar(20), 1) evt.StatusText("A voice crackles from the wreck: '
    '\'Over here, the open hatch. Talk to me.\'") end end)\n',
    f'RegisterMapTimerEvent({DRONE_TIMER_EVENT}, 900, function() if IsAtLeast(MapVar(21), 1) then return end '
    f'SetValue(MapVar(21), 1) evt.SetMonGroupBit({ARRIVAL_DRONE_GROUP}, MonsterBits.Invisible, false) '
    'evt.StatusText("Engines whine overhead: drones, coming down on the smoke!") end, "The arrival\'s drones", '
    '"", 900)\n']

# --- Write the sources, build with the editor, verify -----------------------------------------------------------------
if SOURCE.exists():
    shutil.rmtree(SOURCE)
(SOURCE / 'models').mkdir(parents=True)
bmodel_records = []
interactive = []
if colliders.faces:                                     # the model buildings' boxes, if any are placed
    models.append(colliders)
for index, model in enumerate(models):
    write_obj(model, SOURCE / 'models' / f'{model.name}.obj', SIZES)
    textures = sorted({texture for _, texture, _ in model.faces})
    bmodel_records.append({'geometry_id': f'hes_out1:{model.name}', 'runtime_bmodel_index': index,
                           'source': {'asset_path': str(SOURCE / 'models' / f'{model.name}.obj'), 'scale': 128,
                                      'merge_coplanar_faces': False, 'preserve_source_winding': True},
                           'materials': {'default_texture': textures[0], 'remaps': {t: t for t in textures}}})
    # A model in CRAWLER_COGS carries its cog on every face (evt.SetFacetBit shows and hides it), a HIDDEN_MODELS one
    # starts Invisible and Untouchable; FACE_ATTRIBUTES replaces the clickable bit of its event faces (the plates).
    cog = CRAWLER_COGS.get(model.name, 0)
    hidden = 0x20002000 if model.name in HIDDEN_MODELS else 0
    face_events = {face: event for event, faces in model.events.items() for face in faces if event}
    for face in sorted(set(face_events) | (set(range(len(model.faces))) if cog else set())):
        event = face_events.get(face, 0)
        interactive.append({'bmodel_index': index, 'face_index': face,
                            'legacy_attributes': (FACE_ATTRIBUTES.get(model.name, 0x2000000) if event else 0) | hidden,
                            'cog_number': cog, 'cog_triggered_number': event, 'cog_trigger': 0})
    for face in model.invisible:                        # FaceAttribute::Invisible: blocks, not drawn
        interactive.append({'bmodel_index': index, 'face_index': face, 'legacy_attributes': 0x2000,
                            'cog_number': 0, 'cog_triggered_number': 0, 'cog_trigger': 0})
(SOURCE / 'hes_out1.geometry.yml').write_text(json.dumps({'version': 1, 'map_file': MAP, 'bmodels': bmodel_records},
                                                         indent=1) + '\n')
(SOURCE / 'hes_out1.terrain.yml').write_text(json.dumps({
    'version': 1, 'map_file': MAP, 'height_map_hex': height_bytes.tobytes().hex().upper(),
    'tile_map_hex': tile_bytes.tobytes().hex().upper(),
    'attribute_map_hex': bytes(GRID * GRID).hex().upper()}) + '\n')
# Ground items are sprite objects carrying the item; the object is the one of the item's sprite index (the stand-in
# engine icon's, which stage.py writes into the staged item row).
staged_item_rows = {int(row[0]): row for row in (line.split('\t') for line in
                    (STAGE / 'worlds/hesper/data_tables/items.txt').read_text().splitlines()) if row[0].isdigit()}
object_ids = [int(line.split('\t')[2]) for line in (ROOT / 'assets_dev/engine/data_tables/object_list.txt')
              .read_text(encoding='latin-1').splitlines()[1:] if line.strip()]
ground_items = []


def ground_item(item_id, x, y, z):
    sprite = int(staged_item_rows[item_id][11])
    item_bytes = item_id.to_bytes(4, 'little') + bytes(32)
    ground_items.append({
        'sprite_object_index': len(ground_items), 'sprite_id': sprite,
        'object_description_id': object_ids.index(sprite),
        'position': {'x': int(round(x)), 'y': int(round(y)), 'z': int(round(z))},
        'velocity': {'x': 0, 'y': 0, 'z': 0}, 'yaw_angle': int(rng.integers(0, 2048)), 'sound_id': 0,
        'attributes': 0, 'sector_id': 0, 'time_since_created': 0, 'temporary_lifetime': 0,
        'glow_radius_multiplier': 0, 'spell_id': 0, 'spell_level': 0, 'spell_skill': 0, 'field54': 0,
        'spell_caster_pid': 0, 'spell_target_pid': 0, 'lod_distance': 0, 'spell_caster_ability': 0,
        'initial_position': {'x': 0, 'y': 0, 'z': 0}, 'raw_containing_item_hex': item_bytes.hex().upper()})


# The black box's three Lander Log Cores (11486, the Pilot's Log cores 9005) lie on the floors of the small debris
# craters C5, D6, D7 (P4's ITEM_PLACEMENT.md; the design's 'log' places are the craters' centres).
LOG_CORE = 11486
for kind, cell, fx, fy, label, _ in detail.PLACES:
    if kind != 'log':
        continue
    x, y = place(cell, fx, fy)
    assert not on_brine({'x': x, 'y': y}), label
    ground_item(LOG_CORE, x, y, height_at(x, y))
assert len(ground_items) == 3, ground_items
# The colony log tablets I-III (11360-11362, S9; P4's READABLES, the integrator's follow-up 37) lie on their plinths
# (events 35-37), in the plinths' order (the design's tablet places).
plinth_top = model_bounds('hes_tablet_plinth')[1][1]
for k, (x, y) in enumerate(TABLET_PLINTHS):
    ground_item(11360 + k, x, y, height_at(x, y) + plinth_top + 2)
reference = yaml.safe_load((ROOT / 'assets_dev/worlds/mm8/maps/out02.scene.yml').read_text())
environment = reference['environment']
environment['tile_set_lookup_indices'] = LOOKUPS
scene = {'format_version': 1, 'kind': 'outdoor_scene', 'source': {'geometry_file': MAP},
         'environment': environment, 'terrain': {'attribute_overrides': [], 'footstep_sound_overrides': []},
         'bmodel_faces': {'interactive_faces': interactive}, 'entities': entities, 'spawns': hostiles['spawns'],
         'initial_state': {'location': {'respawn_count': 0, 'last_respawn_day': 0, 'reputation': 0,
                                        'alert_status': 0},
                           'face_attribute_overrides': [], 'actors': actors, 'sprite_objects': ground_items,
                           'chests': [],
                           'variables': {'map': [0] * 75, 'decor': [0] * 125}},
         'loot_containers': loot, 'world_items': []}
(SOURCE / 'hes_out1.scene.yml').write_text(json.dumps(scene, indent=1) + '\n')
package = {'format_version': 1, 'kind': 'outdoor_map_package', 'package_id': 'hesper:starport_reach',
           'display_name': 'Starport Reach', 'map_file': MAP, 'scene_file': 'hes_out1.scene.yml',
           'geometry_metadata_file': 'hes_out1.geometry.yml', 'terrain_metadata_file': 'hes_out1.terrain.yml',
           'script_module': 'maps/hes_out1.lua', 'map_stats_id': 9101, 'redbook_track': 0,
           'environment_name': 'grassland', 'is_top_level_area': True,
           'outdoor_bounds': {'enabled': True, 'min_x': -BOUND, 'max_x': BOUND, 'min_y': -BOUND, 'max_y': BOUND}}
(SOURCE / 'hes_out1.map.yml').write_text(json.dumps(package, indent=1) + '\n')

if TREE.exists():
    shutil.rmtree(TREE)
for folder in ['maps', 'events/maps', 'terrain_materials', 'terrain_decorations']:
    (TREE / folder).mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='hes-out1-') as directory:
    temp = Path(directory)
    for name in ['hes_out1.map.yml', 'hes_out1.scene.yml', 'hes_out1.geometry.yml', 'hes_out1.terrain.yml']:
        shutil.copy2(SOURCE / name, temp / name)
    log = PROJECT / 'build.log'
    with log.open('w') as stream:
        subprocess.run([str(ROOT / 'build/editor/openyamm-editor'), '--asset-root', str(STAGE), '--headless-build-map',
                        str(temp / 'hes_out1.map.yml')], check=True, stdout=stream, stderr=subprocess.STDOUT)
    shutil.copy2(temp / MAP, TREE / 'maps' / MAP)
shutil.copy2(SOURCE / 'hes_out1.scene.yml', TREE / 'maps/hes_out1.scene.yml')

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

# Where a scenario stands to click a door face (camp_and_homes.yml, landfall_keepers.yml): 240 out from the face's
# centre along its normal, at the ground, facing it (yaw in radians).
POSE_EVENTS = {25, CONSOLE_EVENT, 51, 52, 53, 54, 65, 68, 75}
door_poses = {}
for model in models:
    for event, faces in model.events.items():
        if event in POSE_EVENTS:
            points = np.array(model.faces[faces[0]][0])
            centre = points.mean(0)
            n = normal([tuple(p) for p in points])
            px, py = centre[0] + n[0] * 240, centre[1] + n[1] * 240
            door_poses[event] = [round(px), round(py), round(height_at(px, py)),
                                 round(math.atan2(-n[1], -n[0]), 4)]
# Lua.
text = '-- Generated by level_generation/projects/hesper_out1/build_out1.py.\n'
text += 'SetMapMetadata({onLoad = {83, 84}, onLeave = {}, openedChestIds = {'
text += ', '.join(f'[{40 + index}] = {{{index}}}' for index in range(len(loot))) + '}})\n'   # the chests' events
for event in sorted(EVENTS):
    title, body = EVENTS[event]
    text += f'RegisterEvent({event}, {json.dumps(title)}, function() {body} end, {json.dumps(title)})\n'
text += ''.join(ARRIVAL_LUA)                      # the arrival's load and timer events (above)
(TREE / 'events/maps/hes_out1.lua').write_text(text)

# Ground materials: the slot file and weights.
slot = yaml.safe_load((DESIGN / 'terrain_materials.yml').read_text())
slot['weights'] = ['hes_out1_weights0.png', 'hes_out1_weights1.png']
slot['weighted_layers'] = len(LAYERS)
slot['slope'] = {'layer': len(LAYERS), 'start': slot['slope']['start'], 'end': slot['slope']['end']}
assert [layer['name'] for layer in slot['layers']] == LAYERS + ['cliff']
(TREE / 'terrain_materials/hes_out1.yml').write_text(
    '# Generated by level_generation/projects/hesper_out1/build_out1.py from design/kreegan_world/zone1/'
    'terrain_materials.yml.\n# weights: RGBA images covering the 128x128 cell map, channels in layer order (north '
    'row first).\n' + yaml.safe_dump(slot, sort_keys=False))
for index in range(2):
    Image.fromarray(quantized[..., index * 4:index * 4 + 4], 'RGBA').save(
        TREE / f'terrain_materials/hes_out1_weights{index}.png', optimize=True)
(TREE / 'terrain_materials/world.yml').write_text(
    '# Hesper writes each map\'s slot file and weights from its design (level_generation/projects/hesper_out1);\n'
    '# tools/terrain_materials.py weights is not used for this world.\nversion: 1\nmaterials: {}\ntiles: []\n')

# Plants: the families and the rules by tile name.
shutil.copy2(ROOT / 'design/kreegan_world/art/ground_plants/hesper_plants_v1.png',
             TREE / 'terrain_decorations/hesper_plants_v1.png')
shutil.copy2(PROJECT / 'families.yml', TREE / 'terrain_decorations/families.yml')
RULES = [('voltyl', 'ash_tufts', 1.0), ('voltylx', 'lichen', 0.8), ('plsatyl', 'wire_scrub', 0.5),
         ('rktyl', 'lichen', 0.6), ('rktylx', 'lichen', 0.4), ('rkse', 'glass_grass', 0.7),
         ('volse', 'glass_grass', 0.3), ('volne', 'ember_moss', 0.9)]
(TREE / 'terrain_decorations/hes_out1.yml').write_text(yaml.safe_dump({
    'version': 2, 'families_file': 'families.yml', 'seed': 1020, 'near_distance': 3072, 'minimum_normal_z': 0.7,
    'density_variation': 0.9, 'patch_size': 1024, 'tall_grass_chance': 0.0, 'tall_grass_scale': 1.0,
    'rules': [{'texture': texture, 'family': family, 'density': density, 'tint': [1.0, 1.0, 1.0]}
              for texture, family, density in RULES]}, sort_keys=False))

# The ground's colour as it reads in the game, for the minimap's terrain (build_minimap_blender.py): each layer's
# design colour (the detailed map's, which the game's tinted ground plus the violet sky light produces) with its
# photo's light and dark detail, by the weights, cliffs on steep slopes.
library = yaml.safe_load((ROOT / 'assets_dev/engine/terrain_materials/library.yml').read_text())['materials']
library.update(yaml.safe_load((ROOT / 'level_generation/projects/hesper_stage/terrain_library.yml').read_text())
               ['materials'])


DESIGN_COLOURS = {'ash': (122, 113, 124), 'ash_dune': (150, 138, 142), 'glass': (40, 36, 48),
                  'plating': (206, 200, 186), 'canyon': (134, 66, 46), 'scree': (96, 88, 96), 'creep': (60, 30, 64),
                  'cliff': (104, 94, 100)}


def layer_colour(layer):
    with Image.open(ROOT / 'assets_source/engine/terrain_materials' / layer['library'] / 'albedo_height.png') as image:
        tile_size = max(2, int(round(layer['repeat'] / units)))
        tile = np.asarray(image.convert('L').resize((tile_size, tile_size), Image.BOX), dtype=np.float32)
    detail = (tile / max(tile.mean(), 1.0)) ** 0.6
    tile = (np.array(DESIGN_COLOURS[layer['name']], dtype=np.float32) / 255) ** 2.2 * detail[..., None]
    reps = size // tile_size + 1
    return np.tile(tile, (reps, reps, 1))[:size, :size]


colour = np.zeros((size, size, 3), dtype=np.float32)
for index, layer in enumerate(slot['layers'][:len(LAYERS)]):
    colour += field[..., index:index + 1] * layer_colour(layer)
texel_heights = ndimage.gaussian_filter(ndimage.zoom(heights, size / GRID, order=3), 6)
gy_, gx_ = np.gradient(texel_heights, units)
slope = np.hypot(gx_, gy_)
cliff = np.clip((slope - slot['slope']['start']) / (slot['slope']['end'] - slot['slope']['start']), 0, 1)[..., None]
colour = colour * (1 - cliff) + layer_colour(slot['layers'][len(LAYERS)]) * cliff
(PROJECT / 'work').mkdir(exist_ok=True)
for placement in model_placements:
    placement['model'] = str(model_file(placement['name']))
    placement['scale'] = model_scale(placement['name'])[0]
(PROJECT / 'work/minimap_models.json').write_text(json.dumps(model_placements, indent=1) + '\n')
Image.fromarray(np.clip(colour ** (1 / 2.2) * 255 + 0.5, 0, 255).astype(np.uint8), 'RGB').save(
    PROJECT / 'work/ground_colour.png')

# Previews for review.
review = PROJECT / 'review'
review.mkdir(exist_ok=True)
low, high = heights.min(), heights.max()
Image.fromarray(((heights - low) / (high - low) * 255).astype(np.uint8), 'L').resize((512, 512)).save(
    review / 'heights.png')
colours = np.array([[122, 113, 124], [150, 138, 142], [40, 36, 48], [206, 200, 186], [134, 66, 46], [96, 90, 100],
                    [70, 30, 74], [0, 0, 0]], dtype=np.float32)
Image.fromarray(np.clip(field[::4, ::4] @ colours, 0, 255).astype(np.uint8), 'RGB').save(review / 'weights.png')
report = {'map': MAP, 'bmodels': len(models), 'faces': sum(len(m.faces) for m in models),
          'entities': len(entities), 'actors': len(actors), 'chests': len(loot), 'events': sorted(EVENTS),
          'height_range': [int(heights.min()), int(heights.max())], 'arrival': [int(arrival[0]), int(arrival[1]),
                                                                                int(arrival_z)],
          'crew_door': [int(crew_door[0]), int(crew_door[1])], 'arrival_direction_degrees': direction,
          'party_start': [int(party_start[0]), int(party_start[1]), int(party_start_z), party_start_facing],
          'wreck': [int(wreck_centre[0]), int(wreck_centre[1]), int(wreck_level)], 'stash': [int(v) for v in stash],
          'landfall': {'wall': LANDFALL['wall']['line'], 'town': LANDFALL['town'],
                       'gates': [list(EAST_GATE), list(NORTH_GATE)],
                       'level': round(town_level)},
          'lift_arrival': [round(v) for v in lift_arrival],
          'terminal_arrival': [round(v) for v in terminal_arrival],
          'archive_arrival': [round(v) for v in archive_arrival],
          'station_arrival': [round(v) for v in station_arrival],
          'log_cores': [list(item['position'].values()) for item in ground_items[:3]],
          'tablets': [list(item['position'].values()) for item in ground_items[3:6]],
          'camp': {'crawler': [round(v) for v in camp_crawler], 'scrapyard_crawler': [round(v) for v in scrap_crawler],
                   'folk': {a['name']: [a['position']['x'], a['position']['y'], a['position']['z'], a['actor_index']]
                            for a in actors if a['group'] == GROUPS['ashrunner_folk']},
                   'edge': [EDGE_RX, EDGE_RY, EDGE_W]},
          'door_poses': door_poses,
          'street_people': {str(a['npc_id']): a['actor_index'] for a in actors if a['npc_id'] in STREET_PEOPLE.values()}}
(PROJECT / 'out1_build.json').write_text(json.dumps(report, indent=1) + '\n')
print(json.dumps(report))
print('dressing', json.dumps(dressing))
print('population', json.dumps(population))
