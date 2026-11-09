"""Build the Brood Spires (hes_out3.odm, map 9120) from its design: terrain, ground materials, the acid, plants,
buildings, decorations, chests, ground items, monsters, people, events, then the ODM through the editor's writer, into
runtime/worlds/hesper for the shared Hesper stage.

    python3 level_generation/projects/hesper_out3/build_out3.py
    flock output/hesper_stage/locks/stage.lock python3 level_generation/projects/hesper_stage/stage.py

The design is the authority (design/kreegan_world/zone3/BROOD_SPIRES.md, BUILD-READY): the terrain fields of
brood_terrain.py, every road, place, spire, decoration group and spawn point of brood_detail.json (make_brood_detail.py)
and the Acid Garden of acid_garden_plan.json. Modelled on level_generation/projects/hesper_out1/build_out1.py, whose
BModel kit (bmodels.py, houses.py) it imports; kit_out3.py adds the greenhouse, the farm wall, the ruins, the gantry and
the dungeon portals. The editor needs the stage as its asset root, so run the stage once before the first build.
Nothing is written to assets_dev.
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
DESIGN = ROOT / 'design/kreegan_world/zone3'
STAGE = ROOT / 'output/hesper_stage/assets_editor_dev'
SOURCE = PROJECT / 'source'
TREE = PROJECT / 'runtime/worlds/hesper'
OUT1 = ROOT / 'level_generation/projects/hesper_out1'
MAP = 'hes_out3.odm'
sys.path.insert(0, str(DESIGN))
sys.path.insert(0, str(OUT1))
sys.path.insert(0, str(PROJECT))
import brood_terrain as bt  # noqa: E402
from bmodels import Model, normal, write_obj  # noqa: E402
import houses  # noqa: E402
import kit_out3 as kit  # noqa: E402

DETAIL = json.loads((DESIGN / 'brood_detail.json').read_text())
GARDEN = json.loads((DESIGN / 'acid_garden_plan.json').read_text())
GRID = 128
STEP = 512
TEXELS = 16                                   # weight texels per terrain cell
BOUND = 4 * bt.CELL_UNITS                     # the playable square: +-23 040
EDGE_BAND = 1500.0                            # heights matched to the neighbour within this band of an edge
rng = np.random.default_rng(20261023)


# --- Coordinates ----------------------------------------------------------------------------------------------------
def to_px(x, y):
    return (np.asarray(x) / bt.CELL_UNITS + 4) * bt.CELL, (4 - np.asarray(y) / bt.CELL_UNITS) * bt.CELL


def place(cell, fx=0.5, fy=0.5):
    x, y = bt.world(cell, fx, fy)
    return float(x), float(y)


PLACES = DETAIL['places']


def places(kind):
    return [p for p in PLACES if p['kind'] == kind]


def game_height(h):
    """The design's relative height in world units: 800 + 1500 h; the outer walls above 6000 compressed."""
    z = bt.BASE_Z + bt.Z_SCALE * h
    return np.minimum(np.where(z > 6000.0, 6000.0 + (z - 6000.0) * 0.3, z), 8000.0)


# --- Terrain heights ------------------------------------------------------------------------------------------------
gx = np.arange(GRID)
sample_x, sample_y = np.meshgrid((gx - 64) * STEP, (64 - gx) * STEP)        # [gy, gx]
heights = np.zeros((GRID, GRID))
for dx in (-170, 0, 170):
    for dy in (-170, 0, 170):
        h, _ = bt.build_terrain(*to_px(sample_x + dx, sample_y + dy))
        heights += game_height(h) / 9.0
# The edge bands the neighbours' contracts fix: unaveraged, so their rows are exactly the contract's.
edge_heights = game_height(bt.build_terrain(*to_px(sample_x, sample_y))[0])
# The vertex rows within 1 500 of an edge and the first one past it (1 536 in), so the ground is level for the
# whole band and rises only beyond it.
SOUTH_BAND = sample_y <= -BOUND + EDGE_BAND + STEP / 2
CROWN_Y, CROWN_Z = bt.CROWN_Y, 1200.0
EAST_GAP = (sample_x >= BOUND - EDGE_BAND - STEP / 2) & (np.abs(sample_y - CROWN_Y) <= 1000)


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


def run_on(line, distance=11000.0):
    """A road that leaves the playable square at an end runs on past the map's edge, so it reads as going somewhere."""
    for end, inner in ((0, 1), (-1, -2)):
        (x, y), (ix, iy) = line[end], line[inner]
        if max(abs(x), abs(y)) > BOUND - 600:
            dx, dy = x - ix, y - iy
            length = math.hypot(dx, dy)
            point = (x + dx / length * distance, y + dy / length * distance)
            line = [point] + line if end == 0 else line + [point]
    return line


ROADS = DETAIL['roads']
colony = [run_on([tuple(map(float, p)) for p in ROADS['colony'][0]])]
lane = [[tuple(map(float, p)) for p in line] for line in ROADS['track']]
resin = [[tuple(map(float, p)) for p in line] for line in ROADS['resin']]
resin[2] = run_on(resin[2])                                           # the Crown road runs on past the east edge
causeway = [[tuple(map(float, p)) for p in line] for line in ROADS['causeway']]
# Road widths (BROOD_SPIRES.md, Roads): the colony road 640, the lane 500; the resin roads 500 (relay), 600 (the
# Kreegan Way), 640 (the Crown road), 500 (the hatchery track); the causeway 400.
RESIN_WIDTHS = [500.0, 600.0, 640.0, 500.0]

# Sites (buildings and the big models): centre, half sizes, yaw; what roads go round and the scatter keeps clear of.
G_BOX = GARDEN['box']
SHIP = DETAIL['seedship']
SITES = {
    'garden': (((G_BOX[0] + G_BOX[2]) / 2, (G_BOX[1] + G_BOX[3]) / 2), (G_BOX[2] - G_BOX[0]) / 2,
               (G_BOX[3] - G_BOX[1]) / 2, 0.0),
    'hatchery': (place('A2', 0.68, 0.22), 700, 700, 0.0),
    'relay_spire': (place('B7', 0.55, 0.15), 2200, 2200, 0.0),
    'weather_station': ((9350.0, -8720.0), 420, 380, 0.0),
    'survey_mast': (place('A4', 0.55, 0.45), 300, 300, 0.0),
}

# --- Pads ------------------------------------------------------------------------------------------------------------
# The Acid Garden's levels are the terrain function's; each building sits on its own level (acid_garden_plan.json).
for house in GARDEN['houses']:
    (hx, hy), across = house['position'], house['door'] in ('north', 'south')
    half_x, half_y = (house['width'] / 2, house['depth'] / 2) if across else (house['depth'] / 2, house['width'] / 2)
    flatten((hx, hy), half_x + 60, half_y + 60, falloff=200, level=house['level_z'])
hatchery_level = flatten(SITES['hatchery'][0], 700, 700, falloff=400)
(wx_, wy_), _, _, _ = SITES['weather_station']
station_level = flatten((wx_, wy_), 420, 380, falloff=500)
flatten((wx_ + 550, wy_ + 300), 200, 200, falloff=300, level=station_level)        # the mast's foot
mast_level = flatten(SITES['survey_mast'][0], 300, 300, falloff=400)
# D5's door: a pad at the root mound's east face, the door facing east (BROOD_SPIRES.md section 13).
D5_DOOR = (-11480.0, -12384.0)
d5_level = flatten((D5_DOOR[0] + 200, D5_DOOR[1]), 450, 520, falloff=500)
# The former turret shelves remain unchanged; their four pairs are now kite roosts.
ROOST_PAIRS = []                              # (group, monster, centre, facing degrees)
for p in places('m_sentinel'):
    group = {'D8': 1, 'E8': 2, 'H2': 4, 'H4': 5}[p['cell']]
    monster = 10310 if group in (1, 2) else 10311
    facing = {1: 270.0, 2: 270.0, 4: 225.0, 5: 135.0}[group]
    ROOST_PAIRS.append((group, monster, tuple(map(float, p['position'])), facing))
roost_spots = []                              # (group, monster, x, y, facing)
for group, monster, (cx, cy), facing in ROOST_PAIRS:
    a = math.radians(facing + 90)
    for side in (-1, 1):
        x, y = cx + side * 300 * math.cos(a), cy + side * 300 * math.sin(a)
        flatten((x, y), 260, 260, falloff=260)
        roost_spots.append((group, monster, x, y, facing))

# --- Roads -----------------------------------------------------------------------------------------------------------
for line in colony:
    grade(line, 700, 600, 0.18)
for line in lane:
    grade(line, 560, 500, 0.25)
for line, width in zip(resin, RESIN_WIDTHS):
    grade(line, width + 60, 500, 0.3)
for line in causeway:
    grade(line, 460, 400, 0.3)
# The gantry's foot and the hull breach, the sinkhole's floor at D9's mouth.
BREACH = tuple(map(float, SHIP['breach']))
GANTRY_FOOT = tuple(map(float, SHIP['gantry_foot']))
foot_level = flatten(GANTRY_FOOT, 300, 300, falloff=400)
D9_DOOR = (-8986.0, 6970.0)
# The edge bands again, exactly the contract's: the south band Starport Reach's built north row, the Crown gap at 1 200.
heights[SOUTH_BAND] = edge_heights[SOUTH_BAND]
heights[EAST_GAP] = CROWN_Z

height_bytes = np.clip(np.round(heights / 32.0), 0, 255).astype(np.uint8)
heights = height_bytes.astype(np.float64) * 32.0          # the quantised heights everything else stands on

# --- Materials: tiles (one per cell) and weights (16 texels per cell) ----------------------------------------------
# Tile ids through the lookups [volcanic 198, swamp 270, rock 342, tar 666]: raw 90 + 36 x set + offset. The tile
# names key the plant rules (the plants below); the ground itself is drawn by the material
# weights. The fourth set is MM8's tar tiles: the stage's liquids.yml makes them the Brood Spires' acid
# (hesper_acid, a shallow liquid: waded, never drowned in; the rust brine of Starport Reach keeps the water tiles, so
# the two never match each other), and acid_tiles() picks their shore tiles (tr*), whose coverage masks the stage
# copies from MM8. The acid cells carry the Burn attribute (0x01): the engine's burning damage while wading.
LOOKUPS = [198, 270, 342, 666]
# The plant rules need whole tiles: a transition tile (volne and the other corners and edges) carries a coverage mask
# that keeps plants to part of its cell. So the egg fields' membrane takes the volcanic set's voltylx (raw 91) and the
# wet creep the rock set's rktylx (raw 164), each unused otherwise; the walls share the slopes' rktyl.
TILES = {'creep': 90, 'wet': 164, 'marsh': 126, 'crust': 127, 'membrane': 91, 'bone': 163, 'plating': 1,
         'rock': 162, 'wall': 162, 'acid': 198}
ACID_EDGE = {'S': 216, 'N': 217, 'W': 214, 'E': 215}          # trS trN trW trE (raw 90 + 108 + offset)
ACID_INNER = {'SW': 218, 'NW': 219, 'SE': 220, 'NE': 221}
ACID_OUTER = {'SW': 210, 'NW': 211, 'SE': 212, 'NE': 213}
BURN = 0x01
LAYERS = ['creep', 'creep_wet', 'marsh', 'crust', 'membrane', 'bone', 'plating']   # weighted; 'rock' is the slope layer
MIX = {'creep': {'creep': 1.0}, 'wet': {'creep_wet': 1.0}, 'marsh': {'marsh': 1.0}, 'crust': {'crust': 1.0},
       'membrane': {'membrane': 1.0}, 'bone': {'bone': 1.0}, 'plating': {'plating': 1.0},
       'rock': {'creep': 0.7, 'creep_wet': 0.3}, 'wall': {'creep': 1.0}, 'acid': {'crust': 0.6, 'marsh': 0.4}}


def segment_distance(xs, ys, lines):
    best = np.full(np.shape(xs), 1e9)
    for line in lines:
        for (ax, ay), (bx, by) in zip(line, line[1:]):
            dx, dy = bx - ax, by - ay
            t = np.clip(((xs - ax) * dx + (ys - ay) * dy) / (dx * dx + dy * dy), 0, 1)
            best = np.minimum(best, np.hypot(xs - (ax + t * dx), ys - (ay + t * dy)))
    return best


def road_masks(xs, ys):
    """The paved roads (the colony road and the lane), the resin roads and the bone causeway at world points."""
    paved = (segment_distance(xs, ys, colony) < 320) | (segment_distance(xs, ys, lane) < 250)
    resin_mask = np.zeros(np.shape(xs), bool)
    for line, width in zip(resin, RESIN_WIDTHS):
        resin_mask |= segment_distance(xs, ys, [line]) < width / 2
    return paved, resin_mask, segment_distance(xs, ys, causeway) < 200


cell_x, cell_y = np.meshgrid((gx - 64) * STEP + STEP / 2, (64 - gx) * STEP - STEP / 2)
_, cell_material = bt.build_terrain(*to_px(cell_x, cell_y))
paved_c, resin_c, bone_c = road_masks(cell_x, cell_y)
land = cell_material != 'acid'
cell_material[paved_c & land] = 'plating'
cell_material[resin_c & land] = 'wet'
cell_material[bone_c & land] = 'bone'


def acid_tiles(acid):
    """Shore tiles round the acid cells (rows run north to south): land cells beside acid take the shore tile of the
    side or corner the acid lies on. A land cell with acid on opposite sides, three sides or two diagonals alone has
    no tile and becomes acid; repeated until every shore cell has one. Returns the acid mask and the shore cells'
    tile ids (0 elsewhere). (Starport Reach's brine_tiles, for the tar tile set.)"""
    acid = acid.copy()
    while True:
        padded = np.pad(acid, 1)
        n, s_, w, e = padded[:-2, 1:-1], padded[2:, 1:-1], padded[1:-1, :-2], padded[1:-1, 2:]
        nw, ne, sw, se = padded[:-2, :-2], padded[:-2, 2:], padded[2:, :-2], padded[2:, 2:]
        sides = n.astype(int) + s_ + w + e
        fill = ~acid & ((n & s_) | (w & e) | (sides >= 3) | ((sides == 0) & ((nw.astype(int) + ne + sw + se) >= 2)))
        if not fill.any():
            break
        acid |= fill
    shore = np.zeros(acid.shape, np.uint8)
    land_ = ~acid
    for name, mask in (('S', s_), ('N', n), ('W', w), ('E', e)):
        shore[land_ & (sides == 1) & mask] = ACID_EDGE[name]
    for name, (a, b) in {'SW': (s_, w), 'NW': (n, w), 'SE': (s_, e), 'NE': (n, e)}.items():
        shore[land_ & (sides == 2) & a & b] = ACID_INNER[name]
    for name, mask in (('SW', sw), ('NW', nw), ('SE', se), ('NE', ne)):
        shore[land_ & (sides == 0) & mask] = ACID_OUTER[name]
    return acid, shore


acid_mask, acid_shore = acid_tiles(cell_material == 'acid')
cell_material[acid_mask] = 'acid'
tile_bytes = np.vectorize(TILES.get)(cell_material).astype(np.uint8)
tile_bytes[acid_shore > 0] = acid_shore[acid_shore > 0]
attribute_bytes = np.where(acid_mask, BURN, 0).astype(np.uint8)


def cell_corners(cells):
    corners = np.zeros(heights.shape, bool)
    for dy in (0, 1):
        for dx in (0, 1):
            corners[dy:GRID, dx:GRID] |= cells[:GRID - dy, :GRID - dx]
    return corners


# The acid lies level in its bed: every corner of an acid or shore cell sinks to the lowest acid corner within a cell
# of it (the liquid's planes are drawn at their cells' corners); a pool lies wholly level at its lowest acid corner.
acid_corners = cell_corners(acid_mask)
wet_corners = cell_corners(acid_mask | (acid_shore > 0))
padded = np.pad(np.where(acid_corners, heights, np.inf), 1, constant_values=np.inf)
lowest = np.min([padded[1 + dy:GRID + 1 + dy, 1 + dx:GRID + 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)],
                axis=0)
heights[wet_corners] = np.minimum(heights, lowest)[wet_corners]
pool_labels, pool_count = ndimage.label(acid_mask | (acid_shore > 0), structure=np.ones((3, 3)))
for label in range(1, pool_count + 1):
    pool_wet = cell_corners(pool_labels == label)
    pool_acid = pool_wet & acid_corners
    if pool_acid.any() and np.ptp(heights[pool_acid]) <= 160:
        heights[pool_wet] = heights[pool_acid].min()
height_bytes = np.clip(np.round(heights / 32.0), 0, 255).astype(np.uint8)
heights = height_bytes.astype(np.float64) * 32.0

size = GRID * TEXELS
units = 65536.0 / size
tx, ty = np.meshgrid(-32768.0 + (np.arange(size) + 0.5) * units, 32768.0 - (np.arange(size) + 0.5) * units)
_, texel_material = bt.build_terrain(*to_px(tx, ty))
field = np.zeros((size, size, len(LAYERS)), dtype=np.float32)
for material, mix in MIX.items():
    where = texel_material == material
    for layer, weight in mix.items():
        field[..., LAYERS.index(layer)] += where * weight
softness = 110.0 / units
field = np.stack([ndimage.gaussian_filter(field[..., c], softness, mode='nearest') for c in range(len(LAYERS))], -1)
paved_t, resin_t, bone_t = road_masks(tx, ty)
# The sinkhole's ramp is wet creep over roots (the terrain's own 'wet' on its arc): it stays as the terrain draws it.
for mask, layer, crisp in [(resin_t, 'creep_wet', 1.0), (bone_t, 'bone', 1.0), (paved_t, 'plating', 0.75)]:
    weight = np.clip(ndimage.gaussian_filter(mask.astype(np.float32), crisp, mode='nearest'), 0, 1)
    field *= (1 - weight)[..., None]
    field[..., LAYERS.index(layer)] += weight
# The integrator's review of build01: the creep's orange veins everywhere were busy at a distance, so between the
# spires it thins out into the marsh's dark mud in broad low-frequency patches (not on the roads, the membrane or the
# crust); and the colony road and the lane, Starport Reach's clean pavers, glared white: marsh mud blown over them,
# fading out over the last 3 000 before the pass's edge so the crossing still meets Starport Reach's clean paving.
thin = bt.value_noise(*to_px(tx, ty), 7, 401) * 0.6 + bt.value_noise(*to_px(tx, ty), 19, 402) * 0.4
thin = np.clip((thin - 0.42) / 0.25, 0.0, 1.0) * 0.45 * (1.0 - np.clip(resin_t + bone_t + paved_t, 0, 1))
moved_creep = field[..., LAYERS.index('creep')] * thin
field[..., LAYERS.index('creep')] -= moved_creep
field[..., LAYERS.index('marsh')] += moved_creep
road_fade = np.clip((ty - (-BOUND + 1500)) / 3000.0, 0.0, 1.0)
dust = np.clip(ndimage.gaussian_filter(paved_t.astype(np.float32), 0.75, mode='nearest'), 0, 1) * 0.5 * road_fade
dust *= 0.75 + 0.5 * bt.value_noise(*to_px(tx, ty), 60, 403)
field[..., LAYERS.index('marsh')] += dust * field[..., LAYERS.index('plating')]
field[..., LAYERS.index('plating')] *= 1.0 - dust
field /= np.maximum(field.sum(-1, keepdims=True), 1e-6)
field = np.concatenate([field, np.zeros((size, size, 8 - len(LAYERS)), dtype=np.float32)], -1)
quantized = np.clip(field * 255 + 0.5, 0, 255).astype(np.uint8)
del texel_material, tx, ty

# --- Buildings --------------------------------------------------------------------------------------------------------
ART = ROOT / 'design/kreegan_world/art'
SIZES = {}                          # texture -> native size (master / 4)
for folder in ['textures_out1/masters', 'textures_k5_grafted/masters', 'textures_k7_hive/masters',
               'textures_k8_ship/masters', 'textures_k11_greenhouse/masters']:
    for png in (ART / folder).glob('*.png'):
        with Image.open(png) as image:
            SIZES[png.stem] = (image.width / 4, image.height / 4)
# As Starport Reach's TEXTURE_SCALE: the textures whose detail reads too small at one native texel per world unit.
TEXTURE_SCALE = {'hoplate': 1.5, 'hopylon': 1.25, 'hhmodule': 2.5, 'hhprefab': 1.75, 'hhprefdk': 1.75,
                 'hhwallpf': 1.75, 'hhwalldk': 1.75, 'hodome': 1.5, 'hsfloor': 1.5, 'hscradle': 1.5,
                 'hobhive': 1.5, 'hokwall': 1.5}
for texture, scale in TEXTURE_SCALE.items():
    SIZES[texture] = (SIZES[texture][0] * scale, SIZES[texture][1] * scale)
models = []
EVENTS = {}                         # event id -> (title, Lua body)
DOOR_ANGLE = {'north': math.pi / 2, 'south': -math.pi / 2, 'east': 0.0, 'west': math.pi}

# The Acid Garden (acid_garden_plan.json): Hesk's farmhouse (tall, dark), Wren's post (a lean-to with a lookout deck),
# the three greenhouses (K11), the wall round the yard and terraces with its gate (east) and wicket (north).
GARDEN_EVENTS = {}
door_ways = []                      # (x, y, out_x, out_y) of every door, for the clear-in-front rule
for house in GARDEN['houses']:
    (hx, hy), front = house['position'], DOOR_ANGLE[house['door']]
    fx, fy = hx + math.cos(front) * house['depth'] / 2, hy + math.sin(front) * house['depth'] / 2
    z = house['level_z']
    event = house['event']
    name = f"garden_{house['number']}"
    if house['style'] == 'tall':
        models.append(houses.tall_house(name, fx, fy, z, front, event, house['width'], house['depth'],
                                        skin='prefab_dark'))
        door_x = -house['width'] / 2 * 0.3
    elif house['style'] == 'lean':
        m = houses.salvage_house(name, fx, fy, z, front, event, house['width'], house['depth'], 'lean', windows=2,
                                 pipe=False, skin='prefab')
        w = house['width'] / 2
        kit.lookout_deck(m, houses.Frame(fx, fy, z, front), -w + 60, house['depth'] * 0.35, -w + 380,
                         house['depth'] - 40, 400.0 + 150 + 120)
        models.append(m)
        door_x = -w * 0.25
    else:
        end_wall = 'hhprefab' if house['finish'] == 'light' else 'hhprefdk'
        models.append(kit.greenhouse(name, fx, fy, z, front, event, house['width'], house['depth'], end_wall))
        door_x = 0.0
    ex, ey = -math.sin(front), math.cos(front)
    door_ways.append((fx + ex * door_x, fy + ey * door_x, math.cos(front), math.sin(front)))
models.append(kit.farm_wall('garden_wall', G_BOX, GARDEN['wall']['height'], GARDEN['wall']['thickness'],
                            GARDEN['wall']['gate'], GARDEN['wall']['wicket'], height_at))

# The drowned agri-domes (C5): three colony domes sunk to their shoulders in the marsh; the big one torn open on its
# east side (toward the causeway), its locker and tablet inside.
DOMES_CENTRE = place('C5', 0.42, 0.55)
DOMES = [(DOMES_CENTRE, 700.0, 0.0), ((DOMES_CENTRE[0] - 1350, DOMES_CENTRE[1] + 950), 550.0, None),
         ((DOMES_CENTRE[0] - 300, DOMES_CENTRE[1] - 1450), 450.0, None)]
for k, ((dx, dy), radius, torn) in enumerate(DOMES):
    z = min(height_at(dx + radius * math.cos(a), dy + radius * math.sin(a)) for a in np.linspace(0, 6.28, 12))
    models.append(kit.sunk_dome(f'agri_dome_{k}', (dx, dy), z, radius, radius * 0.95, radius * 0.35, torn))
# The old survey mast (A4): its plinth and the mast fallen east-north-east, the dish ring at its far end.
models.append(kit.survey_mast('survey_mast', SITES['survey_mast'][0], mast_level, math.radians(20), height_at))
# The weather station (F6): an Ancient hab hut, its door sealed (event 18), and a standing mast beside it.
WEATHER_DOOR_EVENT = 18
models.append(houses.hab_house('weather_station', wx_, wy_ - 280, station_level, -math.pi / 2, WEATHER_DOOR_EVENT,
                               700, 560))
models.append(kit.lattice_mast('weather_mast', wx_ + 550, wy_ + 300, station_level))
door_ways.append((wx_, wy_ - 280, 0.0, -1.0))
# The gantry from the cradle's west slope up to the hull breach (event 52 on the breach face).
D11_EVENT, D9_EVENT, D5_EVENT = 52, 51, 50
BREACH_SILL = 2000.0
breach_dir = np.array(BREACH) - np.array(GANTRY_FOOT)
breach_dir /= np.linalg.norm(breach_dir)
gantry_top = tuple(np.array(BREACH) - breach_dir * 60)
models.append(kit.gantry('gantry', GANTRY_FOOT, gantry_top, foot_level + 6, BREACH_SILL - 10, height_at,
                         breach_event=D11_EVENT))
# D9's mouth in the sinkhole floor's north wall, facing south-east into the pit; D5's grafted door facing east.
d9_front = math.atan2(-1.0, 1.0)
# Set 250 back into the pit's wall from the design's door point, so the rock closes round its sides.
d9_set = (D9_DOOR[0] - math.cos(d9_front) * 250, D9_DOOR[1] - math.sin(d9_front) * 250)
models.append(kit.hive_portal('d09_mouth', *d9_set, height_at(*D9_DOOR), d9_front, D9_EVENT))
door_ways.append((*D9_DOOR, math.cos(d9_front), math.sin(d9_front)))
# D5's door is the Relay Spire model's own doorway (the integrator's answer: one door): the model stands so its
# doorway lies on the design's door point, and the clickable face is the grafted blast door (hkblast) fitted flush in
# that doorway, a step of plating before it. The doorway, measured on the model (its front view and vertices): its
# plane 0.30 of the model's size in front of its centre, 0.063 wide, from its base to 0.21 high.
RELAY_DOOR_DEPTH, RELAY_DOOR_W, RELAY_DOOR_H = 0.30, 0.063, 0.21
door_ways.append((*D5_DOOR, 1.0, 0.0))

# --- Decorations ----------------------------------------------------------------------------------------------------
ids = json.loads((ROOT / 'output/hesper_stage/decoration_ids.json').read_text())
STAND_INS = PROJECT / 'standins'
DECORATIONS = ROOT / 'level_generation/props/hesper_decorations'
designs = json.loads((DECORATIONS / 'designs.json').read_text())
STAGED = {d['name']: d for d in yaml.safe_load((ROOT / 'level_generation/projects/hesper_stage/decorations.yml')
                                               .read_text())['decorations']}
entities = []
model_placements = []                   # the big models the minimap draws (build_minimap_blender.py)
MINIMAP_MODELS = {'hes_seedship', 'hes_cradle_arch', 'hes_relay_spire', 'hes_hatchery_tower', 'hes_spire_great',
                  'hes_spire_roost', 'hes_spire_mid', 'hes_spire_fallen', 'hes_hive_mound'}


def model_file(name):
    """The model a decoration draws: its baked Meshy model, a hard-surface piece, or this project's stand-in."""
    name = STAGED.get(name, {}).get('model', name)
    for path in [DECORATIONS / 'work/codex_tex' / f'{name}_export.glb', DECORATIONS / 'work/hard_surface' / f'{name}.glb',
                 STAND_INS / f'{name}.glb']:
        if path.exists():
            return path
    raise FileNotFoundError(name)


def model_scale(name):
    """World units per glTF unit, and the model's glTF bounds (x, y up, z). A Meshy model is scaled to its design's
    length (the stage does the same), the others are in metres."""
    path = model_file(name)
    data = path.read_bytes()
    gltf = json.loads(data[20:20 + int.from_bytes(data[12:16], 'little')])
    accessors = [gltf['accessors'][primitive['attributes']['POSITION']] for mesh in gltf['meshes']
                 for primitive in mesh['primitives']]
    low = np.min([a['min'] for a in accessors], 0)
    high = np.max([a['max'] for a in accessors], 0)
    # The stage's rule (hesper_stage/stage.py): a decoration named in designs.json is sized to its design's length,
    # every other one is in metres.
    return (designs[name]['length'] / max(high - low) if name in designs else 100.0), low, high


def model_bounds(name):
    scale, low, high = model_scale(name)
    return low * scale, high * scale


def decoration(name, x, y, facing=None, event=0, sink=0.0, cog=0, z=None):
    """A decoration entity. A click runs `event` (the engine reads the secondary slot); `cog` (the primary) keys
    evt.SetSprite's swaps."""
    facing = int(rng.integers(0, 360)) if facing is None else int(round(facing)) % 360
    position = {'x': int(round(x)), 'y': int(round(y)), 'z': int(round((height_at(x, y) if z is None else z) - sink))}
    if name in MINIMAP_MODELS:
        model_placements.append({'name': name, **position, 'facing': facing})
    entities.append({'entity_index': 0, 'name': name, 'decoration_list_id': ids[name] - 1, 'ai_attributes': 0,
                     'position': position, 'facing': facing, 'event_id_primary': cog,
                     'event_id_secondary': event, 'variable_primary': 0, 'variable_secondary': 0, 'special_trigger': 0,
                     'initial_decoration_flag': 0})


colliders = Model('colliders')
# A model's front: the stand-ins and the hard-surface pieces face glTF -z (Blender +y is their back); a Meshy model's
# front is its glTF +z side (Starport Reach's FRONT_YAW 270, from codex_texture.py's guides).
def front_yaw(name):
    return 270 if 'codex_tex' in str(model_file(name)) else 90


def building(name, x, y, front, event=0, parts=None, collide=0.85, z=None):
    """Place a model building with its front facing `front` (degrees), collision as invisible boxes: `parts`
    (along, across, length, depth fractions of the footprint in the model's own axes) or its footprint shrunk by
    `collide`."""
    facing = (front + front_yaw(name)) % 360
    decoration(name, x, y, facing=facing, event=event, z=z)
    low, high = model_bounds(name)
    yaw = math.radians(facing)
    centre = np.array([(low[0] + high[0]) / 2, -(low[2] + high[2]) / 2])
    extent = np.array([high[0] - low[0], high[2] - low[2]])
    ground = height_at(x, y) if z is None else z
    boxes = parts if parts is not None else ([(0.0, 0.0, collide, collide)] if collide else [])
    for along, across, length, depth in boxes:
        c, s = math.cos(yaw), math.sin(yaw)
        local = centre + extent * (along, across)
        ox, oy = local[0] * c - local[1] * s, local[0] * s + local[1] * c
        colliders.collider((x + ox, y + oy, ground - 60), (extent[0] * length, extent[1] * depth,
                                                            high[1] - low[1] + 60), yaw=yaw)
    return facing


# Places the scatter and the actors keep clear of: building sites, doors' ways in, the dungeon portals.
def door_clear(x, y, reach=900.0, half=350.0, margin=0.0):
    return not any(-50 - margin < (x - dx) * ox + (y - dy) * oy < reach + margin and
                   abs(-(x - dx) * oy + (y - dy) * ox) < half + margin for dx, dy, ox, oy in door_ways)


def on_road(x, y, margin=0.0):
    p, r, b = road_masks(np.array([x]), np.array([y]))
    if margin:
        d = min(segment_distance(np.array([x]), np.array([y]), colony)[0] - 320,
                segment_distance(np.array([x]), np.array([y]), lane)[0] - 250,
                segment_distance(np.array([x]), np.array([y]), causeway)[0] - 200,
                *[segment_distance(np.array([x]), np.array([y]), [line])[0] - w / 2
                  for line, w in zip(resin, RESIN_WIDTHS)])
        return d < margin
    return bool(p[0] or r[0] or b[0])


def on_acid(x, y, pad=0):
    col, row = int((x + 32768) // STEP), int((32768 - y) // STEP)
    wet = acid_mask | (acid_shore > 0)
    return bool(wet[max(row - pad, 0):row + pad + 1, max(col - pad, 0):col + pad + 1].any())


def in_garden(x, y, margin=0.0):
    return G_BOX[0] - margin < x < G_BOX[2] + margin and G_BOX[1] - margin < y < G_BOX[3] + margin


# The spires: the design's seeded scatter (brood_detail.json), placed on the built ground. A spire the build's roads
# or pads now reach is dropped (counted in the report); the fallen ones lie at the design's yaw (map degrees, y south).
dropped = []
for spire in DETAIL['spires']:
    x, y = spire['position']
    kind = spire['kind']
    if kind == 'hes_spire_fallen':
        continue
    if kind != 'hes_spire_roost' and (on_road(x, y, margin=200) or on_acid(x, y) or in_garden(x, y, 600)
                                      or not door_clear(x, y, margin=300)):
        dropped.append(kind)
        continue
    decoration(kind, x, y, facing=-spire['yaw_deg'])
fallen = [s for s in DETAIL['spires'] if s['kind'] == 'hes_spire_fallen']
for spire in fallen:
    x, y = spire['position']
    yaw = -spire['yaw_deg']
    # Three boxes along it (its three segments): cover on the pass, and its collision.
    building('hes_spire_fallen', x, y, yaw - front_yaw('hes_spire_fallen') + 90,
             parts=[(-0.33, 0.0, 0.3, 0.75), (0.0, 0.0, 0.3, 0.75), (0.33, 0.0, 0.3, 0.75)])

# The landmarks: the Seedship in its cradle (five keel boxes), the ten cradle arches (a box at each foot), the Relay
# Spire on its root mound (a box 4 400 square to +5 120), the hatchery tower (a box 1 400 square).
ship_c = np.array(SHIP['centre'], float)
heading = math.radians(SHIP['heading_deg'])
ship_axis = np.array([math.sin(heading), math.cos(heading)])         # the bow's direction (world)
ship_west = np.array([-math.cos(heading), math.sin(heading)])        # the port side
SHIP_FLOOR = 890.0
ship_facing = math.degrees(math.atan2(ship_axis[1], ship_axis[0]))
# The hull is a model along its own x (the stand-in's and, once made, the Meshy model's long axis): its facing turns
# that axis to the bow.
# The hull lies along its model's longer horizontal axis: along glTF x the facing turns it to the bow, along glTF z (the
# game's local -y) a quarter turn more.
ship_low, ship_high = model_bounds('hes_seedship')
ship_along_z = (ship_high[2] - ship_low[2]) > (ship_high[0] - ship_low[0])
decoration('hes_seedship', *ship_c, facing=ship_facing + (90 if ship_along_z else 0), z=SHIP_FLOOR + 600)
for k in range(5):                                                   # the keel boxes
    along = -0.4 + 0.2 * k
    p = ship_c + ship_axis * along * SHIP['length']
    colliders.collider((p[0], p[1], SHIP_FLOOR - 40), (SHIP['length'] * 0.19, SHIP['beam'] * 0.8, 4600.0),
                       yaw=math.radians(ship_facing))
# Five pairs, rising either side and curving over; spaced round the gantry (the breach is at -0.24 of the length).
ARCH_PAIRS = [-0.44, -0.08, 0.1, 0.27, 0.44]


def glb_foot(name):
    """Where a model touches the ground, in its own glTF x and z (world units at its game size): the mean of its
    vertices in the lowest twentieth of its height."""
    data = model_file(name).read_bytes()
    length = int.from_bytes(data[12:16], 'little')
    gltf = json.loads(data[20:20 + length])
    binary = data[20 + length + 8:]
    points = []
    for mesh in gltf['meshes']:
        for primitive in mesh['primitives']:
            accessor = gltf['accessors'][primitive['attributes']['POSITION']]
            view = gltf['bufferViews'][accessor['bufferView']]
            start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
            points.append(np.frombuffer(binary, np.float32, accessor['count'] * 3, start).reshape(-1, 3))
    points = np.concatenate(points)
    low = points[points[:, 1] < points[:, 1].min() + 0.05 * np.ptp(points[:, 1])]
    return low[:, 0].mean() * model_scale(name)[0], low[:, 2].mean() * model_scale(name)[0]


arch_foot = glb_foot('hes_cradle_arch')
for along in ARCH_PAIRS:
    for side in (-1, 1):
        p = ship_c + ship_axis * along * SHIP['length'] + ship_west * side * (SHIP['beam'] / 2 + 900)
        facing = math.degrees(math.atan2(-ship_west[1] * side, -ship_west[0] * side))
        decoration('hes_cradle_arch', *p, facing=facing)
        yaw = math.radians(facing)                                   # its foot: glTF x is local x, glTF z local -y
        fx_, fy_ = arch_foot[0], -arch_foot[1]
        q = (p[0] + fx_ * math.cos(yaw) - fy_ * math.sin(yaw), p[1] + fx_ * math.sin(yaw) + fy_ * math.cos(yaw))
        colliders.collider((q[0], q[1], height_at(*q) - 60), (520, 520, 1600), yaw=yaw)
relay_size = designs['hes_relay_spire']['length']                  # the model's longest side in world units
relay_meshy = front_yaw('hes_relay_spire') == 270
# The Meshy model's doorway on D5's door point (its centre RELAY_DOOR_DEPTH west of it); the stand-in has no doorway and
# stands at the design's centre with the old grafted portal.
relay_centre = ((D5_DOOR[0] - RELAY_DOOR_DEPTH * relay_size, D5_DOOR[1]) if relay_meshy
                else SITES['relay_spire'][0])
relay_base = d5_level - 0.024 * relay_size if relay_meshy else height_at(*relay_centre)   # its door sill on the pad
decoration('hes_relay_spire', *relay_centre, facing=(0 + front_yaw('hes_relay_spire')) % 360, z=relay_base)
if relay_meshy:
    door_model = Model('d05_door')
    half, top, x = RELAY_DOOR_W * relay_size / 2, RELAY_DOOR_H * relay_size, D5_DOOR[0] + 8
    door_model.facing([(x, D5_DOOR[1] - half, d5_level), (x, D5_DOOR[1] + half, d5_level),
                       (x, D5_DOOR[1] + half, d5_level + top), (x, D5_DOOR[1] - half, d5_level + top)], 'hkblast',
                      (1, 0, 0), event=D5_EVENT, fit=True)
    door_model.box((D5_DOOR[0] + 160, D5_DOOR[1], d5_level - 40), (300, 2 * half + 160, 48), 'hoplate', top='hoplate')
    models.append(door_model)
else:
    models.append(kit.grafted_portal('d05_door', *D5_DOOR, d5_level, 0.0, D5_EVENT))
# Its cyan coils: a light at the dish crown (6 000 over the root), not at the model's foot.
decoration('hes_relay_crown_light', *relay_centre, facing=0, z=height_at(*relay_centre) + 6000)
# Its tower, behind the door's plane (the design's 4 400 square would reach past the doorway on the model).
colliders.collider((relay_centre[0], relay_centre[1], relay_base - 60), (3200, 3200, 5180))
hatchery_centre = SITES['hatchery'][0]
decoration('hes_hatchery_tower', *hatchery_centre, facing=0, z=hatchery_level)
colliders.collider((hatchery_centre[0], hatchery_centre[1], hatchery_level - 60), (1400, 1400, 2660))
# The ag-flyer wreck (G7; build_brood_props.py, nose at the model's +x, its torn right wing lying beside it): its
# three boxes, the cabin, the tail with its creep and the fallen wing (fractions of the model's footprint, measured
# from it), the nose sunk 60 into the marsh; event 20.
WRECK = place('G7', 0.5, 0.45)
building('hes_agflyer_wreck', *WRECK, 160, event=20, z=height_at(*WRECK) - 60,
         parts=[(0.14, 0.07, 0.71, 0.15), (-0.36, 0.07, 0.28, 0.11), (0.09, -0.31, 0.19, 0.37)])

# The decoration groups (brood_detail.json `decor`, in make_brood_detail.DECOR's order): pods, bone litter, the
# mounds (the hatchery's and the Relay Spire's hive mounds, then two egg mounds at each egg field), crust shelves,
# the domes' places (the BModels above) and the two signs (events 16, 17).
mound_names = ['hes_hive_mound'] * 8 + ['hes_egg_mound'] * 8
GLOW_SACS = []
mounds = 0
signs = 0
for item in DETAIL['decor']:
    symbol, (x, y) = item['symbol'], item['position']
    if symbol == 'dome':
        continue
    if symbol == 'sign':
        decoration('hes_signpost', x, y, event=16 + signs)
        signs += 1
        continue
    if symbol == 'mound':
        name = mound_names[mounds]
        mounds += 1
    else:
        name = {'pod': 'hes_creep_pod', 'bones': 'hes_bones_litter', 'crust': 'hes_acid_shelf'}[symbol]
    if name != 'hes_acid_shelf' and (on_acid(x, y) or on_road(x, y, margin=100) or not door_clear(x, y)):
        continue
    if name == 'hes_acid_shelf' and (on_acid(x, y) or on_road(x, y, margin=100)):
        # A crust shelf sits at a pool's rim: moved to the nearest shore cell's land edge.
        continue
    decoration(name, x, y, sink=20 if name in ('hes_bones_litter', 'hes_egg_mound') else 0)
    if name == 'hes_hive_mound':
        GLOW_SACS.append((x, y))
# Crust shelves on the pools' and the lake's rims: each design shelf moved to the nearest acid-shore cell.
shore_cells = np.argwhere(acid_shore > 0)
shore_points = np.stack([(shore_cells[:, 1] - 64) * STEP + STEP / 2, (64 - shore_cells[:, 0]) * STEP - STEP / 2], 1)
for item in DETAIL['decor']:
    if item['symbol'] != 'crust':
        continue
    x, y = item['position']
    d = np.hypot(shore_points[:, 0] - x, shore_points[:, 1] - y)
    k = int(np.argmin(d))
    if d[k] < 2500:
        sx, sy = shore_points[k]
        decoration('hes_acid_shelf', sx + rng.uniform(-120, 120), sy + rng.uniform(-120, 120))
# The glow sacs: one on each hive mound, six on the hatchery tower (outdoor variant, a light of radius 320).
for x, y in GLOW_SACS:
    decoration('hes_glow_sac_out', x + 180, y - 120, z=height_at(x, y) + 380)
for k in range(6):
    a = k * math.pi / 3 + 0.3
    hx_, hy_ = hatchery_centre
    decoration('hes_glow_sac_out', hx_ + 760 * math.cos(a), hy_ + 760 * math.sin(a), z=hatchery_level + 300 + 120 * k)
# Line decorations: dead landing-light pylons every 1 800 along the colony road (alternating sides), trail cairns every
# 1 400 along the lane and the causeway, a giant rib every 700 along the causeway (alternating sides, along it).
for x, y, a in DETAIL['line_decor']['pylon']:
    if not (on_acid(x, y) or in_garden(x, y, 200)):
        decoration('hes_pylon', x, y)
for x, y, a in DETAIL['line_decor']['cairn']:
    decoration('hes_trail_cairn', x, y)
for k, (x, y, a) in enumerate(DETAIL['line_decor']['rib']):
    world_a = math.radians(-a)
    side = 1 if k % 2 else -1
    rx, ry = x - math.sin(world_a) * side * 380, y + math.cos(world_a) * side * 380
    if not on_acid(rx, ry) and not in_garden(rx, ry, 100):
        decoration('hes_giant_rib', rx, ry, facing=math.degrees(world_a) + (0 if side > 0 else 180), sink=30)

# Aster's relay posts (events 10-12) and the tablet plinths (13-15), the dead scout (19).
RELAYS = places('relay')                     # D5, D9, D11 in the design's order
for k, p in enumerate(RELAYS):
    decoration('hes_relay_post', *p['position'], event=10 + k)
TABLETS = places('tablet')                   # A4 the survey mast, F6 the weather station, C5 the agri-domes
TABLET_ITEMS = {'A4': 11366, 'F6': 11367, 'C5': 11368}
for k, p in enumerate(TABLETS):
    decoration('hes_tablet_plinth', *p['position'], event=13 + k, facing=90)
SCOUT = tuple(map(float, GARDEN['scout']['position']))
decoration('hes_corpse_colonist', *SCOUT, event=19, facing=225)

# The Acid Garden's props (acid_garden_plan.json yard_props), its lit wall posts (outside the wall at the corners and
# flanking the gate and the wicket) and the stat barrel (event 21, +2 Endurance once, map variable 10).
STAT_BARREL_EVENT = 21
for prop in GARDEN['yard_props']:
    x, y = prop['position']
    if prop['name'] == 'water condenser':
        decoration('hes_water_condenser', x, y)
    elif prop['name'] == 'ration crates':
        for k, (ox, oy) in enumerate(((0, 0), (110, 0), (55, 95), (-40, 120))):
            decoration('hes_crate_clean', x + ox, y + oy, facing=15 * k)
    elif prop['name'] == 'hand cart':
        decoration('hes_hand_cart', x, y, facing=200)
    elif prop['name'] == 'brazier':
        decoration('hes_brazier_out', x, y)
    elif prop['name'] == 'stat barrel':
        decoration('hes_stat_barrel_green', x, y, facing=90, event=STAT_BARREL_EVENT, cog=STAT_BARREL_EVENT)
gx0, gy0, gx1, gy1 = G_BOX
for (px, py) in GARDEN['wall']['posts']:
    ox = -170 if px <= gx0 else 170 if px >= gx1 else 0
    oy = -170 if py <= gy0 else 170 if py >= gy1 else 0
    if px in (gx0, gx1) and py in (gy0, gy1):
        ox, oy = ox * 0.8, oy * 0.8
    decoration('hes_light_post_out', px + ox, py + oy)

# The S10 nest (C5-C6): four resin nest mounds round the nest's centre, swapped dark by event 150 (cog 150); the
# scouts' lost supplies (a colonial locker, chest 41) among them.
NEST = GARDEN['nest']
NEST_COG = 150
for k in range(4):
    a = k * math.pi / 2 + 0.4
    decoration('hes_nest_mound', NEST['centre'][0] + 520 * math.cos(a), NEST['centre'][1] + 520 * math.sin(a),
               cog=NEST_COG)

# Abandoned Kreegan plinths now serve as kite roosts (geometry and bake unchanged).
mount_top = model_bounds('hes_turret_mount_k')[1][1]
for group, monster, x, y, facing in roost_spots:
    decoration('hes_turret_mount_k', x, y, facing=facing + front_yaw('hes_turret_mount_k') - 90)

# --- Chests (events 30-41) ---------------------------------------------------------------------------------------------
CHESTS = {'chest_c': 'hes_colonial_locker', 'chest_k': 'hes_kreegan_pod_chest'}
loot = []
CHEST_EVENT0 = 30
for p in PLACES:
    if p['kind'] not in CHESTS:
        continue
    x, y = p['position']
    if (x, y) == (-8179, 6566):
        # The sinkhole floor's pod (chest 34) lay in the 700 x 900 before D9's mouth: 1 000 out from it instead.
        x, y = D9_DOOR[0] + math.cos(d9_front) * 1000, D9_DOOR[1] + math.sin(d9_front) * 1000
    index = len(loot)
    decoration(CHESTS[p['kind']], x, y, event=CHEST_EVENT0 + index, facing=rng.integers(0, 360))
    label = p['label'].split(', ', 1)[-1]
    # H3 by LOOT_RULES: until Hesper's loot pool exists, the native treasure level 6 and 9 000 gold (as D9 and D11).
    loot.append({'source_id': f'hesper:out3:chest_{index}', 'source_object_index': index, 'source_name': label,
                 'position': {'x': int(x), 'y': int(y), 'z': int(height_at(x, y))}, 'container_id': index,
                 'kind': 'chest', 'presentation': CHESTS[p['kind']].replace('hes_', ''), 'random_treasure_level': 6,
                 'treasure_type': 0, 'gold': 9000, 'gold_only': False, 'random': True, 'ai_drop': False,
                 'trap_level': 0, 'should_repopulate': False, 'fixed_items': [], 'remove_when_empty': False})
    EVENTS[CHEST_EVENT0 + index] = (label.capitalize(), f'evt.OpenChest({index})')
assert len(loot) == 12, len(loot)

# --- Actors: the placed groups (BROOD_SPIRES.md section 7) and the Acid Garden's people ---------------------------
MONSTER_ROWS = {int(row[0]): row for row in (line.split('\t') for line in
                (ROOT / 'design/kreegan_world/data/monster_data.txt').read_text().splitlines()) if row[0].isdigit()}
STAGE_MONSTERS = {m['id']: m for m in yaml.safe_load(
    (ROOT / 'level_generation/projects/hesper_stage/monsters.yml').read_text())['monsters']}
actors = []
behaviours = []                                  # (actor index, behaviour id): set by the load event
moved = []


def obstacles():
    radii = {d['name']: d.get('radius', 0) for d in STAGED.values()}
    radii.update({'hes_spire_great': 300, 'hes_spire_mid': 200, 'hes_spire_cluster': 180, 'hes_spire_roost': 320,
                  'hes_hive_mound': 400, 'hes_nest_mound': 300, 'hes_turret_mount_k': 300})
    return [(e['position']['x'], e['position']['y'], radii.get(e['name'], 0)) for e in entities]


OBSTACLES = None


def ground_free(x, y, radius, flier=False, gap=60.0, garden=False):
    """Free ground for an actor: off the acid, the decorations' collision, the doors' ways in and the other actors, on
    level ground; out of the Acid Garden unless it is one of its people (garden)."""
    if abs(x) > BOUND - 800 or abs(y) > BOUND - 800:
        return False
    if not flier and (on_acid(x, y) or in_garden(x, y, 100) != garden):
        return False
    if any(math.hypot(x - ox, y - oy) < radius + r + 30 for ox, oy, r in OBSTACLES if r):
        return False
    if not door_clear(x, y, reach=700, half=450):
        return False
    if not flier:
        z = height_at(x, y)
        d = radius + 100
        if any(abs(height_at(x + dx, y + dy) - z) > 0.7 * d for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d))):
            return False
    return all(math.hypot(x - a['position']['x'], y - a['position']['y']) >= radius + a['radius'] + gap
               for a in actors)


def find_spot(name, x, y, radius, flier=False, rings=30, step=80.0, garden=False):
    if ground_free(x, y, radius, flier, garden=garden):
        return x, y
    for ring in range(1, rings + 1):
        for a in np.linspace(0, 2 * math.pi, 8 + 4 * ring, endpoint=False):
            px, py = x + ring * step * math.cos(a), y + ring * step * math.sin(a)
            if ground_free(px, py, radius, flier, garden=garden):
                moved.append((name, ring * step))
                return px, py
    raise SystemExit(f'build_out3: no room for {name} near {x:.0f}, {y:.0f}')


def actor(monster, x, y, facing, group, z=None, posted=False, name='', search=True, npc=0, garden=False):
    """Place a monster actor at (x, y) facing `facing` (degrees), on the ground or at z; a ground actor whose spot is
    taken moves to the nearest free one."""
    radius, height = STAGE_MONSTERS[monster]['radius'], STAGE_MONSTERS[monster]['height']
    row = MONSTER_ROWS[monster]
    flier = row[9] == 'Y'
    if search and z is None:
        x, y = find_spot(name or str(monster), x, y, radius, flier, garden=garden)
    actors.append({'actor_index': len(actors), 'name': name, 'npc_id': npc, 'attributes': 0, 'hp': int(row[4]),
                   'hostility_type': int(row[12]) if row[12].isdigit() else 0, 'monster_info_id': monster,
                   'monster_id': monster, 'radius': radius, 'height': height,
                   'move_speed': 0 if posted else int(row[13]),
                   'position': {'x': int(round(x)), 'y': int(round(y)),
                                'z': int(round(height_at(x, y) if z is None else z))},
                   'initial_yaw_units': int(round((facing % 360) / 360 * 2048)) % 2048, 'immobile': posted,
                   'sprite_ids': [0, 0, 0, 0], 'sector_id': 0, 'current_action_animation': 0, 'carried_item_id': 0,
                   'group': group, 'ally': 0, 'unique_name_index': 0})
    return actors[-1]


OBSTACLES = obstacles()
HATCHLING, PRIME, EGG, CRAWLER, MATRON = 10003, 10031, 10045, 10091, 10092
FARMER = 10265
# Groups 1, 2, 4, 5: kite roosts on the abandoned plinths; preserve the first eight actor indices.
for group, monster, x, y, facing in roost_spots:
    actor(monster, x, y, facing, group, z=height_at(x, y) + mount_top, posted=False, name='kite spur roost', search=False)


def cluster(monster, count, centre, group, spread, name, facing=None, behaviour=None):
    cx, cy = centre
    for k in range(count):
        a = 2.4 * k
        r = 0 if k == 0 else spread * (0.45 + 0.55 * k / max(1, count - 1))
        a_ = actor(monster, cx + r * math.cos(a), cy + r * math.sin(a),
                   (137.5 * k) % 360 if facing is None else facing, group, name=name)
        if behaviour:
            behaviours.append((a_['actor_index'], behaviour))


# Group 3 and 6-9: the egg fields (the clusters hatch by the world's hes_egg_cluster behaviour, D9's, bound to 10045).
FIELDS = {3: ('E8', 5), 6: ('C1', 5), 7: ('E2', 6), 8: ('B5', 5), 9: ('G4', 6)}
brood_places = {p['cell']: p for p in places('m_brood')}
for group, (cell, count) in FIELDS.items():
    cluster(EGG, count, brood_places[cell]['position'], group, 650, f'egg field {cell}')
# Group 10: the hatchery: seven clusters (the hatchery's parameters: hes_egg_cluster_hatchery), four Hatchlings, an
# Overseer Prime wandering round the tower (hes_overseer_prime).
hatch = brood_places['A2']['position']
cluster(EGG, 7, hatch, 10, 750, 'hatchery egg cluster', behaviour='hes_egg_cluster_hatchery')
cluster(HATCHLING, 4, (hatch[0] + 500, hatch[1] - 600), 10, 300, 'hatchery hatchling')
prime = actor(PRIME, hatchery_centre[0] + 1200, hatchery_centre[1], 90, 10, name='hatchery Overseer Prime',
              z=hatchery_level + 900)
behaviours.append((prime['actor_index'], 'hes_overseer_prime'))
# Group 11: the S10 nest: a Crawler Matron and seven Brood Crawlers round the mounds.
nest_centre = tuple(NEST['centre'])
cluster(MATRON, 1, nest_centre, 11, 0, 'nest matron')
cluster(CRAWLER, 7, nest_centre, 11, 600, 'nest brood crawler')
# Group 12: the gantry's foot: two Overseer Primes over the gantry, four Hatchlings at its foot.
gantry_guard = places('m_overseer')[0]['position']
cluster(HATCHLING, 4, gantry_guard, 12, 350, 'gantry hatchling')
for k in range(2):
    a_ = actor(PRIME, GANTRY_FOOT[0] + 700 * k + 300, GANTRY_FOOT[1] - 200 * k, 180, 12, name='gantry Overseer Prime',
               z=foot_level + 1000 + 200 * k)
    behaviours.append((a_['actor_index'], 'hes_overseer_prime'))
# Groups 13-20: an Overseer Prime perched at each roost (z + 2 700).
roosts = [s for s in DETAIL['spires'] if s.get('roost')]
for k, spire in enumerate(roosts):
    x, y = spire['position']
    a_ = actor(PRIME, x + 120, y, 270, 13 + k, z=height_at(x, y) + 2700, name='roost Overseer Prime', search=False)
    behaviours.append((a_['actor_index'], 'hes_overseer_prime'))
hostile_placed = len(actors)
# The Acid Garden's people (P4's roster): Hesk (9510) on terrace 1 (the design's spot is inside greenhouse 1: moved
# to the yard by the stair's head), and the farmers Bram, Sedge and Lio (9601-9603) on the terrace stair, all on the
# Garden farmer row (10265, staged with a villager body), wandering as MM's street people do (group 22).
PEOPLE_GROUP = 22
actor(FARMER, -2250, -5350, 270, PEOPLE_GROUP, name='Hesk', npc=9510, garden=True)
for k, (npc, name) in enumerate(((9601, 'Bram'), (9602, 'Sedge'), (9603, 'Lio'))):
    actor(FARMER, -1500 + (k - 1) * 120, -3974 + (k - 1) * 380, 180, PEOPLE_GROUP, name=name, npc=npc, garden=True)
people = {a['name']: a['actor_index'] for a in actors if a['group'] == PEOPLE_GROUP}

# --- Spawn points (brood_detail.json `spawns`: slot 1 the brood, 2 the Overseers, 3 the crawlers) ---------------------
# Slot 1 at a random tier (the slot's difficulty 0: Hatchlings), slot 2 every point fixed at tier B (the Overseer
# Prime), slot 3 fixed at B (Brood Crawlers) except the G7 and B3 points at C (the Matron).
def encounter_index(slot, tier):
    return slot if not tier else 4 + 3 * 'ABC'.index(tier) + slot - 1


QUIET_RING = 3150.0
spawns = []
SLOT_TIERS = {1: None, 2: 'B', 3: 'B'}
for k, point in enumerate(DETAIL['spawns']):
    slot = point['slot']
    tier = 'C' if slot == 3 and point['cell'] in ('G7', 'B3') else SLOT_TIERS[slot]
    x, y = point['position']
    radius = 200
    for ring in range(0, 30):
        candidates = [(x, y)] if ring == 0 else [(x + ring * 90 * math.cos(a), y + ring * 90 * math.sin(a))
                                                 for a in np.linspace(0, 2 * math.pi, 8 + 4 * ring, endpoint=False)]
        ok = [(px, py) for px, py in candidates
              if not on_acid(px, py, 1) and not on_road(px, py, margin=400) and
              not (G_BOX[0] - QUIET_RING < px < G_BOX[2] + QUIET_RING and G_BOX[1] - QUIET_RING < py < G_BOX[3] + QUIET_RING)
              and ground_free(px, py, radius, flier=(slot == 2))]
        if ok:
            x, y = ok[0]
            if ring:
                moved.append((f'spawn {k} {point["cell"]}', ring * 90))
            break
    else:
        raise SystemExit(f'build_out3: no room for spawn point {k} at {point["cell"]}')
    spawns.append({'spawn_index': len(spawns), 'position': {'x': round(x), 'y': round(y), 'z': round(height_at(x, y))},
                   'radius': 128, 'type_id': 3, 'index': encounter_index(slot, tier), 'attributes': 0,
                   'group': 40 + slot})

# --- Ground items: Hale's helm and note, the Engram Shard on the pass, the gold piles, the caches -------------------
staged_item_rows = {int(row[0]): row for row in (line.split('\t') for line in
                    (STAGE / 'worlds/hesper/data_tables/items.txt').read_text().splitlines()) if row[0].isdigit()}
object_ids = [int(line.split('\t')[2]) for line in (ROOT / 'assets_dev/engine/data_tables/object_list.txt')
              .read_text(encoding='latin-1').splitlines()[1:] if line.strip()]
ground_items = []
missing_items = []


def ground_item(item_id, x, y, z=None, gold=0):
    """A ground item (a sprite object carrying the item), or a gold pile (item 189 with its amount, as D9's)."""
    if gold:
        sprite = 85
    elif item_id in staged_item_rows:
        sprite = int(staged_item_rows[item_id][11])
    else:
        missing_items.append(item_id)
        return
    raw = bytearray(36)
    raw[0:4] = item_id.to_bytes(4, 'little')
    raw[12:16] = gold.to_bytes(4, 'little')
    ground_items.append({
        'sprite_object_index': len(ground_items), 'sprite_id': sprite, 'object_description_id': object_ids.index(sprite),
        'position': {'x': int(round(x)), 'y': int(round(y)), 'z': int(round(height_at(x, y) if z is None else z))},
        'velocity': {'x': 0, 'y': 0, 'z': 0}, 'yaw_angle': int(rng.integers(0, 2048)), 'sound_id': 0,
        'attributes': 0, 'sector_id': 0, 'time_since_created': 0, 'temporary_lifetime': 0,
        'glow_radius_multiplier': 0, 'spell_id': 0, 'spell_level': 0, 'spell_skill': 0, 'field54': 0,
        'spell_caster_pid': 0, 'spell_target_pid': 0, 'lod_distance': 0, 'spell_caster_ability': 0,
        'initial_position': {'x': 0, 'y': 0, 'z': 0}, 'raw_containing_item_hex': raw.hex().upper()})


ground_item(11106, SCOUT[0] + 110, SCOUT[1] + 40)                    # the Rebreather Helm at Hale's side
ground_item(11376, SCOUT[0] + 70, SCOUT[1] - 90)                     # Hale's Last Note
ground_item(11330, 922, -21542)                                      # an Engram Shard under the fallen spire
for (x, y), gold in (((1150, -18000), 1000), ((-18800, 15800), 3000), ((-14000, -2300), 1500), ((6500, 12000), 2500),
                     ((18800, 7900), 2000)):
    ground_item(189, x, y, gold=gold)
# The two caches before the hard fights: a scout's pack by the first fallen spire, a farmer's crate on the way to the
# nest (outside the west wall: the design's point is on the wall's line).
for (x, y) in ((1200, -21250), (-5500, -5400)):
    decoration('hes_crate_clean', x + 90, y + 60, facing=30)
    for k, item in enumerate((11300, 11300, 11302, 11304)):
        ground_item(item, x + 40 * (k % 2) - 20, y + 40 * (k // 2) - 20)

# R5 Ashkite flocks: complete each spur flock, then add two flocks on the egg-field spires.
# Appended after existing placements so people's and boss actor indices remain stable.
for group, monster, (cx, cy), facing in ROOST_PAIRS:
    for side in (-1, 1):
        actor(monster, cx + side * 500, cy + 450, facing, group, name='kite spur flock')
for flock, spire in enumerate(sorted(roosts, key=lambda p: min(
        math.dist(p['position'], brood_places[cell]['position']) for cell in ('C1', 'E2', 'B5', 'G4')))[:2]):
    cx, cy = spire['position']
    for k in range(4):
        a = k * math.pi / 2
        actor(10310 if k < 2 else 10311, cx + 470 * math.cos(a), cy + 470 * math.sin(a),
              math.degrees(a), 150 + flock, z=height_at(cx, cy) + 2700,
              name=f'egg-field spire kite flock {flock + 1}', search=False)
hostile_placed += 16

# --- The party start and the arrivals ----------------------------------------------------------------------------------
SOUTH_ARRIVAL = (288.0, -22540.0)
EAST_ARRIVAL = (21800.0, 8640.0)
D5_ARRIVAL = (-11080.0, -12384.0)
D9_ARRIVAL = (-8830.0, 6600.0)
d11_arrival_xy = np.array(BREACH) - breach_dir * 300
deck_length = float(np.linalg.norm(np.array(gantry_top) - np.array(GANTRY_FOOT)))
d11_t = float(np.dot(d11_arrival_xy - np.array(GANTRY_FOOT), breach_dir))
d11_z = (foot_level + 6) + (BREACH_SILL - 10 - foot_level - 6) * d11_t / deck_length
ARRIVALS = {
    'south_edge': {'position': [*SOUTH_ARRIVAL, height_at(*SOUTH_ARRIVAL)], 'direction_degrees': 90},
    'east_edge': {'position': [*EAST_ARRIVAL, height_at(*EAST_ARRIVAL)], 'direction_degrees': 180},
    'd05_root_door': {'position': [*D5_ARRIVAL, height_at(*D5_ARRIVAL)], 'direction_degrees': 0},
    'd09_mouth': {'position': [*D9_ARRIVAL, height_at(*D9_ARRIVAL)], 'direction_degrees': 315},
    'd11_breach': {'position': [float(d11_arrival_xy[0]), float(d11_arrival_xy[1]), d11_z],
                   'direction_degrees': round(math.degrees(math.atan2(-breach_dir[1], -breach_dir[0]))) % 360},
}
ARRIVALS = {k: {'position': [int(round(v)) for v in a['position']], 'direction_degrees': a['direction_degrees']}
            for k, a in ARRIVALS.items()}
for index, entity in enumerate(entities):
    entity['entity_index'] = index + 1
start = ARRIVALS['south_edge']
entities.insert(0, {'entity_index': 0, 'name': 'Party Start', 'decoration_list_id': 14, 'ai_attributes': 2,
                    'position': dict(zip('xyz', start['position'])), 'facing': start['direction_degrees'],
                    'event_id_primary': 0, 'event_id_secondary': 0, 'variable_primary': 0, 'variable_secondary': 0,
                    'special_trigger': 0, 'initial_decoration_flag': 2})

# --- Events (BROOD_SPIRES.md section 17; texts section 18; P4's lines) -------------------------------------------------
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


def lua_string(text):
    return json.dumps(text)


def relay(done_bit, before, after):
    return (f'if IsQBitSet(QBit(100034)) then evt.StatusText("A dead relay post; something hums inside.") '
            f'elseif not IsQBitSet(QBit(100003)) then evt.StatusText("A relay post of the Ancients, dark. Something '
            f'hums inside.") elseif IsQBitSet(QBit({done_bit})) then evt.SimpleMessage({lua_string("Aster, through the relay: " + chr(34) + after + chr(34))}) '
            f'else evt.SimpleMessage({lua_string("Aster, through the relay: " + chr(34) + before + chr(34))}) end')


EVENTS[10] = ('Aster relay post', relay(100007, "The Relay Spire rises ring upon ring around an open shaft, and the Overseers "
              "fly it. Their lancers carry the heavier shields. Bring energy weapons. At the crown something old "
              "and proud is waiting. It speaks; do not let it keep you talking.",
              "The gate at the root is mended. Go home if you need to; come back."))
EVENTS[11] = ('Aster relay post', relay(100011, "The Brood Pits. Below this point the null field begins. The other "
              "Guardian's song is at its loudest, so loud no spell can be spoken. Take blades and guns. Burst the egg sacs "
              "that feed the Mother's shield, then strike her.", "She is dead. Her children will starve slowly."))
EVENTS[12] = ('Aster relay post', relay(100013, "The Seedship. It is alive, and it is growing toward your world. Its "
              "brain hangs in the ribs at its heart; four ganglia, each with its own shield. Cut them and it is blind. "
              "Vhorrax is inside too, travelers. He will offer you terms. Whether you take them is yours to choose; he "
              "keeps his word, which is more than the rest of them do.",
              "Blind. It will never find your home now."))
TABLET_TAKEN = 'A colony log tablet lies on the plinth, the colony\'s seal on its face. You take it.'
for k, p in enumerate(TABLETS):
    var = 5 + k
    item = TABLET_ITEMS[p['cell']]
    EVENTS[13 + k] = ('Colony log tablet', f'if IsAtLeast(MapVar({var}), 1) then evt.StatusText("The plinth is empty.") '
                      f'return end SetValue(MapVar({var}), 1) AddValue(InventoryItem({item}), {item}) '
                      f'evt.StatusText({lua_string(TABLET_TAKEN)})')
EVENTS[16] = ('Signpost', 'evt.SimpleMessage("West: the Acid Garden, Hesk\'s farm. Food and a dry roof. North-east, '
              'along the lake lies the devils\' ship in its bones. Keep off.")')
EVENTS[17] = ('Sign', 'evt.SimpleMessage("Scratched into the post: \'The pit goes down to the black ones\' nest. Magic '
              'dies below. Take cells and guns. - Marek\'s party.\'")')
EVENTS[18] = ('The weather station', 'evt.StatusText("Instruments, long dead. Creep has grown through the vents.")')
EVENTS[19] = ('Hale', 'evt.SimpleMessage("Hale, a Landfall scout, three days dead by the look of him. The acid rain ate '
              'his cloak but not his rebreather: it is still on his belt.")')
EVENTS[20] = ('The ag-flyer wreck', 'evt.SimpleMessage("A colony crop flyer, nose down in the marsh. Painted on its '
              'side: \'Agri-Service 3. Spray runs at dawn only.\'")')
EVENTS[STAT_BARREL_EVENT] = ('Green barrel', 'if IsAtLeast(MapVar(10), 1) then evt.StatusText("Empty.") return end '
                             'AddValue(BaseEndurance, 2) SetValue(MapVar(10), 1) '
                             f'evt.SetSprite({STAT_BARREL_EVENT}, 1, "hes_stat_barrel_empty") '
                             'evt.StatusText("+2 Endurance (Permanent)")')
EVENTS[D5_EVENT] = ('The Relay Spire', dungeon_entry('hesper_d05', 'hes_d05.blv', 'from_hes_out3',
                                                     'A grafted blast door. The way is not yet open.'))
EVENTS[D9_EVENT] = ('The Brood Pits', dungeon_entry('hesper_d09', 'hes_d09.blv', 'from_hes_out3',
                                                    'A membrane door, sealed. The way is not yet open.'))
EVENTS[D11_EVENT] = ('The Seedship', dungeon_entry('hesper_d11', 'hes_d11.blv', 'from_hes_out3',
                                                   'The hull breach is sealed with resin. The way is not yet open.'))
EVENTS[301] = ("Hesk's farmhouse", 'evt.StatusText("Hesk\'s farmhouse. The door is sealed against the rain; Hesk works '
               'the yard.")')
EVENTS[302] = ("Wren's post", 'evt.EnterHouse(9351)')
EVENTS[303] = ('The farm store', 'evt.EnterHouse(9352)')
for event in (304, 305):
    EVENTS[event] = ('Greenhouse', 'evt.StatusText("Sealed. Through the amber glass, rows of pale fungus glow under the '
                     'drip lines.")')
# The S10 nest cleared (150), the pass roosts cleared (151), the Crown road's (152): from the group check (5).
NEST_DARK = f'evt.SetSprite({NEST_COG}, 1, "hes_nest_mound_dead")'
EVENTS[150] = ('The nest is quiet', f'if IsQBitSet(QBit(100510)) then return end SetQBit(QBit(100510)) {NEST_DARK} '
               'evt.StatusText("The nest is quiet.")')
EVENTS[151] = ('The pass roosts cleared', 'if IsQBitSet(QBit(100501)) then return end SetQBit(QBit(100501)) '
               'evt.StatusText("The pass roosts are quiet.")')
EVENTS[152] = ("The Crown road's roosts cleared", 'if IsQBitSet(QBit(100502)) then return end '
               'SetQBit(QBit(100502))')
# 5: the group checks every 2 s (MM's CheckMonstersKilled: every actor of the group dead).
# The load event runs them too (a map reloaded after the last kill, and headless runs).
GROUP_CHECKS_LUA = ('local function brood_group_checks() local function dead(g) return '
                    'evt.CheckMonstersKilled(ActorKillCheck.Group, g, 0, false) end '
                    'if not IsQBitSet(QBit(100501)) and dead(1) and dead(2) then RunEvent151() end '
                    'if not IsQBitSet(QBit(100502)) and dead(4) and dead(5) then RunEvent152() end '
                    'if not IsQBitSet(QBit(100510)) and dead(11) then RunEvent150() end end\n')
EVENTS[5] = ('Group checks', 'brood_group_checks()')
# The acid rain (engine needs E2-E4 met by the map's Lua): a day rolls a 40 % chance of a rain spell from a hash of
# the day (the same on every save and every machine, as the engine's own weather rolls), its start hour (0-15) and
# length (2-9 hours). Event 4 every game hour and on load starts or stops the rain (map variable 1 while it rains;
# 2 the day, 3 and 4 today's start hour and length, 0 on a dry day, 9 the hour of the last check);
# event 3 every 5 s while it rains burns each character with neither sealed helm (11106, 11107) equipped for 3D6
# Body, "The acid rain burns!", and the first time sets 100503 and autonote 10201.
RAIN_LUA = '''local function brood_rain_day(day)
    local h = (day * 2654435761 + 977) % 4294967296
    h = (h ~ (h >> 13)) * 1274126177 % 4294967296
    h = h ~ (h >> 16)
    local rains = (h % 1000) < 400
    local start = (h >> 10) % 16
    local length = 2 + (h >> 14) % 8
    return rains, start, length
end
local function brood_rain_update()
    local minutes = evt.CurrentGameMinutes()
    local day = minutes // 1440
    local hour = (minutes % 1440) // 60
    local rains, start, length = brood_rain_day(day)
    local raining = rains and hour >= start and hour < start + length
    if not raining and day > 0 then
        local yesterday, ystart, ylength = brood_rain_day(day - 1)
        raining = yesterday and hour + 24 < ystart + ylength
    end
    evt.SetRain(0, raining)
    SetValue(MapVar(1), raining and 1 or 0)
    SetValue(MapVar(2), day % 30000)
    SetValue(MapVar(3), rains and start or 0)
    SetValue(MapVar(4), rains and length or 0)
    SetValue(MapVar(9), hour)
end
local function brood_rain_burn()
    if not IsAtLeast(MapVar(1), 1) then return end
    local hurt = false
    for player = 0, evt.GetPartyMemberCount() - 1 do
        if not evt.PartyMemberHasEquippedItem(player, 11106) and not evt.PartyMemberHasEquippedItem(player, 11107) then
            evt.DamagePlayer(player, Damage.Body, math.random(1, 6) + math.random(1, 6) + math.random(1, 6))
            hurt = true
        end
    end
    if hurt then
        evt.StatusText("The acid rain burns!")
        evt.PlaySoundName("acid_burn")
        if not IsQBitSet(QBit(100503)) then SetQBit(QBit(100503)) SetAutonote(10201) end
    end
end
'''
EVENTS[3] = ('The acid rain burns', 'brood_rain_burn()')
EVENTS[4] = ('The acid rain', 'brood_rain_update()')
behaviour_lua = ' '.join(f'evt.SetActorBehavior({index}, "{name}")' for index, name in behaviours)
EVENTS[1] = ('The Brood Spires on load',
             behaviour_lua
             + ' if IsQBitSet(QBit(100501)) then evt.SetMonGroupBit(1, MonsterBits.Invisible, 1) '
               'evt.SetMonGroupBit(2, MonsterBits.Invisible, 1) end'
             + ' if IsQBitSet(QBit(100502)) then evt.SetMonGroupBit(4, MonsterBits.Invisible, 1) '
               'evt.SetMonGroupBit(5, MonsterBits.Invisible, 1) end'
             + f' if IsQBitSet(QBit(100510)) then {NEST_DARK} end'
             + f' if IsAtLeast(MapVar(10), 1) then evt.SetSprite({STAT_BARREL_EVENT}, 1, "hes_stat_barrel_empty") end'
             + ' brood_group_checks() brood_rain_update() brood_rain_burn()')
EVENTS[2] = ('The Brood Spires, first visit', 'SetAutonote(10202)')

# --- The guide's outdoor checks ---------------------------------------------------------------------------------------
# No road under a building's footprint except its last 500 at either end (where it arrives at a door or a gate), and
# no decoration in the 700 x 900 before a door (its lights and the yard's props are outside the doorways' boxes).
problems = []
footprints = [(name, centre, hx, hy) for name, (centre, hx, hy, _) in SITES.items()]
footprints += [(f"house {h['number']}", tuple(h['position']), *((h['depth'] / 2, h['width'] / 2)
               if h['door'] in ('east', 'west') else (h['width'] / 2, h['depth'] / 2))) for h in GARDEN['houses']]
for kind, lines in (('colony', colony), ('lane', lane), ('resin', resin), ('causeway', causeway)):
    for line in lines:
        points = resample(line, 128.0)
        for x, y in points[4:-4]:
            for name, (cx, cy), hx, hy in footprints:
                if name == 'garden' and kind in ('lane', 'causeway'):
                    continue                            # they end at its gate and wicket
                if abs(x - cx) < hx and abs(y - cy) < hy:
                    problems.append(f'{kind} road under {name} at ({x:.0f}, {y:.0f})')
                    break
for entity in entities:
    if entity['name'] == 'Party Start':
        continue
    x, y = entity['position']['x'], entity['position']['y']
    if not door_clear(x, y, reach=900, half=350):
        problems.append(f"{entity['name']} in front of a door at ({x}, {y})")
if problems:
    raise SystemExit('build_out3: ' + '; '.join(sorted(set(problems))[:20]))

# --- Write the sources, build with the editor, verify -----------------------------------------------------------------
if SOURCE.exists():
    shutil.rmtree(SOURCE)
(SOURCE / 'models').mkdir(parents=True)
if colliders.faces:
    models.append(colliders)
bmodel_records = []
interactive = []
for index, model in enumerate(models):
    write_obj(model, SOURCE / 'models' / f'{model.name}.obj', SIZES)
    textures = sorted({texture for _, texture, _ in model.faces})
    bmodel_records.append({'geometry_id': f'hes_out3:{model.name}', 'runtime_bmodel_index': index,
                           'source': {'asset_path': str(SOURCE / 'models' / f'{model.name}.obj'), 'scale': 128,
                                      'merge_coplanar_faces': False, 'preserve_source_winding': True},
                           'materials': {'default_texture': textures[0], 'remaps': {t: t for t in textures}}})
    for event, faces in model.events.items():
        for face in faces:
            interactive.append({'bmodel_index': index, 'face_index': face, 'legacy_attributes': 0x2000000,
                                'cog_number': 0, 'cog_triggered_number': event, 'cog_trigger': 0})
    for face in model.invisible:                        # FaceAttribute::Invisible: blocks, not drawn
        interactive.append({'bmodel_index': index, 'face_index': face, 'legacy_attributes': 0x2000,
                            'cog_number': 0, 'cog_triggered_number': 0, 'cog_trigger': 0})
(SOURCE / 'hes_out3.geometry.yml').write_text(json.dumps({'version': 1, 'map_file': MAP, 'bmodels': bmodel_records},
                                                         indent=1) + '\n')
(SOURCE / 'hes_out3.terrain.yml').write_text(json.dumps({
    'version': 1, 'map_file': MAP, 'height_map_hex': height_bytes.tobytes().hex().upper(),
    'tile_map_hex': tile_bytes.tobytes().hex().upper(),
    'attribute_map_hex': attribute_bytes.tobytes().hex().upper()}) + '\n')
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
(SOURCE / 'hes_out3.scene.yml').write_text(json.dumps(scene, indent=1) + '\n')
package = {'format_version': 1, 'kind': 'outdoor_map_package', 'package_id': 'hesper:brood_spires',
           'display_name': 'The Brood Spires', 'map_file': MAP, 'scene_file': 'hes_out3.scene.yml',
           'geometry_metadata_file': 'hes_out3.geometry.yml', 'terrain_metadata_file': 'hes_out3.terrain.yml',
           'script_module': 'maps/hes_out3.lua', 'map_stats_id': 9120, 'redbook_track': 0,
           'environment_name': 'grassland', 'is_top_level_area': True,
           'outdoor_bounds': {'enabled': True, 'min_x': -BOUND, 'max_x': BOUND, 'min_y': -BOUND, 'max_y': BOUND}}
(SOURCE / 'hes_out3.map.yml').write_text(json.dumps(package, indent=1) + '\n')

if TREE.exists():
    shutil.rmtree(TREE)
for folder in ['maps', 'events/maps', 'terrain_materials', 'terrain_decorations', 'behaviors']:
    (TREE / folder).mkdir(parents=True, exist_ok=True)
if (PROJECT / 'work/hes_out3.bmp').exists():                  # the last minimap (finish_minimap.py)
    (TREE / 'icons_x2').mkdir(exist_ok=True)
    shutil.copy2(PROJECT / 'work/hes_out3.bmp', TREE / 'icons_x2/hes_out3.bmp')
with tempfile.TemporaryDirectory(prefix='hes-out3-') as directory:
    temp = Path(directory)
    for name in ['hes_out3.map.yml', 'hes_out3.scene.yml', 'hes_out3.geometry.yml', 'hes_out3.terrain.yml']:
        shutil.copy2(SOURCE / name, temp / name)
    with (PROJECT / 'build.log').open('w') as stream:
        subprocess.run([str(ROOT / 'build/editor/openyamm-editor'), '--asset-root', str(STAGE), '--headless-build-map',
                        str(temp / 'hes_out3.map.yml')], check=True, stdout=stream, stderr=subprocess.STDOUT)
    shutil.copy2(temp / MAP, TREE / 'maps' / MAP)
shutil.copy2(SOURCE / 'hes_out3.scene.yml', TREE / 'maps/hes_out3.scene.yml')

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

# The edge contracts: the south edge row within 32 of Starport Reach's built north row (and the pass road at 1 120
# for 1 500 in), the Crown gap level at 1 200 for 1 500 in.
edges = json.loads((ROOT / 'design/kreegan_world/WORK_PACKAGES/edges/hes_out1_built_edges.json').read_text())
north = edges['north_edge_y_23040']
worst = 0.0
for x, z in zip(north['x'], north['in_0']):
    if abs(x) <= BOUND:
        worst = max(worst, abs(height_at(x, -BOUND) - z))
assert worst <= 32, f'south edge differs from Starport Reach by {worst}'
pass_road = [height_at(288, -BOUND + d) for d in range(0, 1501, 250)]
assert max(abs(z - 1120) for z in pass_road) <= 32, pass_road
gap = [height_at(BOUND - d, CROWN_Y + o) for d in range(0, 1501, 250) for o in (-900, 0, 900)]
assert max(abs(z - CROWN_Z) for z in gap) <= 32, gap

# Lua.
text = '-- Generated by level_generation/projects/hesper_out3/build_out3.py.\n'
text += ('SetMapMetadata({onLoad = {1, 2}, onLeave = {}, openedChestIds = {'
         + ', '.join(f'[{CHEST_EVENT0 + index}] = {{{index}}}' for index in range(len(loot))) + '}})\n')
text += RAIN_LUA
for event in (150, 151, 152):
    text += f'local function RunEvent{event}() {EVENTS[event][1]} end\n'
text += GROUP_CHECKS_LUA
for event in sorted(EVENTS):
    title, body = EVENTS[event]
    if event in (150, 151, 152):
        body = f'RunEvent{event}()'
    text += f'RegisterEvent({event}, {json.dumps(title)}, function() {body} end, {json.dumps(title)})\n'
# Timers in game seconds (one game minute is two real seconds): the rain's burn every 5 s, its schedule every game
# hour, the group checks every 2 s.
text += "RegisterMapTimerEvent(3, 150, function() brood_rain_burn() end, 'The acid rain burns', '', 150)\n"
text += "RegisterMapTimerEvent(4, 3600, function() brood_rain_update() end, 'The acid rain', '', 3600)\n"
text += f"RegisterMapTimerEvent(5, 60, function() {EVENTS[5][1]} end, 'Group checks', '', 60)\n"
(TREE / 'events/maps/hes_out3.lua').write_text(text)
for behaviour in ('hes_egg_cluster_hatchery', 'hes_overseer_prime'):
    shutil.copy2(PROJECT / 'behaviors' / f'{behaviour}.lua', TREE / 'behaviors' / f'{behaviour}.lua')

# Ground materials: the slot file (the design's draft, the new materials' tints from their measured means) and weights.
slot = yaml.safe_load((DESIGN / 'terrain_materials.yml').read_text())
library_means = {k: v['mean_color'] for k, v in yaml.safe_load(
    (ROOT / 'assets_dev/engine/terrain_materials/library.yml').read_text())['materials'].items()}
stage_library = yaml.safe_load((ROOT / 'level_generation/projects/hesper_stage/terrain_library.yml').read_text())
TARGETS = {'creep_wet': (86, 40, 92), 'membrane': (128, 58, 96)}
for layer in slot['layers']:
    if layer['name'] in TARGETS:
        mean = stage_library['materials'][layer['library']]['mean_color']
        layer['tint'] = [round(t / 255.0 / m, 4) for t, m in zip(TARGETS[layer['name']], mean)]
# The integrator's review of build01: the swamp moss's standing-water pools smeared into blue-black blotches, so the
# marsh is ambientCG's wet soil (Ground048, CC0); tinted to the design's olive (84, 82, 58) it read as an Earth meadow on
# the slopes the thinned creep reaches, so it is a violet-brown mud (72, 62, 62); the pavers dulled from Starport
# Reach's clean tint.
marsh = next(layer for layer in slot['layers'] if layer['name'] == 'marsh')
marsh['library'] = 'soil'
marsh['tint'] = [round(c / 255.0 / m, 4) for c, m in zip((72, 62, 62), library_means['soil'])]
marsh['repeat'] = 440
next(layer for layer in slot['layers'] if layer['name'] == 'plating')['tint'] = [0.62, 0.64, 0.74]
slot['weights'] = ['hes_out3_weights0.png', 'hes_out3_weights1.png']
slot['weighted_layers'] = len(LAYERS)
slot['slope'] = {'layer': len(LAYERS), 'start': slot['slope']['start'], 'end': slot['slope']['end']}
assert [layer['name'] for layer in slot['layers']] == ['creep', 'creep_wet', 'marsh', 'crust', 'membrane', 'bone',
                                                       'plating', 'rock']
(TREE / 'terrain_materials/hes_out3.yml').write_text(
    '# Generated by level_generation/projects/hesper_out3/build_out3.py from design/kreegan_world/zone3/'
    'terrain_materials.yml.\n# weights: RGBA images covering the 128x128 cell map, channels in layer order (north '
    'row first).\n' + yaml.safe_dump(slot, sort_keys=False))
for index in range(2):
    Image.fromarray(quantized[..., index * 4:index * 4 + 4], 'RGBA').save(
        TREE / f'terrain_materials/hes_out3_weights{index}.png', optimize=True)

# Plants (section 8): no grass. The design's existing families, Starport Reach's dead stalks and ember moss, and the
# three of CR-P2-13 (creep tendrils, resin nodules, shell shards; cells in art/ground_plants, plants_brood.json). The
# engine's atlas holds at most 4 x 4 cells and Hesper's is full, so the map has its own 4 x 3 atlas of the cells it
# uses. Creep (voltyl): tendrils and a few dead stalks; wet creep (rktylx): ember moss and nodules; the egg fields'
# membrane (voltylx): shell shards and nodules; nothing on the marsh.
PLANT_CELLS = ['dead_stalk_1', 'dead_stalk_2', 'wire_scrub_1', 'ember_moss_1', 'ember_moss_2', 'creep_tendril_1',
               'creep_tendril_2', 'resin_nodule_1', 'resin_nodule_2', 'shell_shard_1', 'shell_shard_2']
plant_atlas = Image.new('RGBA', (4 * 256, 3 * 192), (0, 0, 0, 0))
for index, cell in enumerate(PLANT_CELLS):
    with Image.open(ROOT / 'design/kreegan_world/art/ground_plants/cells' / f'{cell}.png') as image:
        assert image.size == (256, 192) and image.mode == 'RGBA', cell
        plant_atlas.paste(image, (index % 4 * 256, index // 4 * 192))
plant_atlas.save(TREE / 'terrain_decorations/hes_out3_plants.png', optimize=True)
families = yaml.safe_load((OUT1 / 'families.yml').read_text())
families['tuft_texture'], families['tuft_atlas_grid'] = 'hes_out3_plants.png', [4, 3]
families['families'] = {k: v for k, v in families['families'].items() if k in ('dead_stalks', 'ember_moss')}
OUT1_LAYERS = yaml.safe_load((ROOT / 'design/kreegan_world/art/ground_plants/atlas_layers.json').read_text())['layers']
for family in families['families'].values():                   # Starport Reach's atlas layers to this atlas's
    for variant in family['variants']:
        variant['layer'] = PLANT_CELLS.index(next(k for k, v in OUT1_LAYERS.items() if v == variant['layer']))


def plant_family(cells, width, height, candidates, wind):
    return {'kind': 'grass', 'candidates': candidates, 'width': width, 'height': height, 'tint': [1, 1, 1],
            'variants': [{'layer': PLANT_CELLS.index(cell), 'weight': 1, 'width_scale': 1, 'height_scale': scale}
                         for cell, scale in cells], 'full_footprint': False, 'wind_strength': wind}


families['families'].update({
    'creep_tendrils': plant_family([('creep_tendril_1', 1.0), ('creep_tendril_2', 0.85)], 80, 90, 14, 0.4),
    'resin_nodules': plant_family([('resin_nodule_1', 1.0), ('resin_nodule_2', 0.9)], 70, 34, 14, 0.0),
    'shell_shards': plant_family([('shell_shard_1', 1.0), ('shell_shard_2', 0.9)], 70, 34, 18, 0.0)})
(TREE / 'terrain_decorations/hes_out3_families.yml').write_text(
    '# The Brood Spires\' plant families (build_out3.py): Starport Reach\'s dead stalks and ember moss and the three of '
    'CR-P2-13, on the map\'s own atlas.\n' + yaml.safe_dump(families, sort_keys=False))
# Densities after the first capture (build03_plants): at Starport Reach's thin 6 candidates x 0.35 the dark tendrils
# vanished into the dark creep, so the new families are denser and larger (about Starport Reach's ash tufts), and the
# dark tendrils' and nodules' tints are lifted toward violet so they read against the creep (the integrator, 2026-10-23).
PLANT_TINTS = {'creep_tendrils': [1.5, 1.35, 1.5], 'resin_nodules': [1.45, 1.3, 1.5]}
RULES = [('voltyl', 'creep_tendrils', 0.9), ('voltyl', 'dead_stalks', 0.2), ('rktylx', 'ember_moss', 0.6),
         ('rktylx', 'resin_nodules', 0.7), ('voltylx', 'shell_shards', 0.9), ('voltylx', 'resin_nodules', 0.25)]
(TREE / 'terrain_decorations/hes_out3.yml').write_text(yaml.safe_dump({
    'version': 2, 'families_file': 'hes_out3_families.yml', 'seed': 1023, 'near_distance': 3072,
    'minimum_normal_z': 0.7, 'density_variation': 0.9, 'patch_size': 1024, 'tall_grass_chance': 0.0,
    'tall_grass_scale': 1.0,
    'rules': [{'texture': texture, 'family': family, 'density': density,
               'tint': PLANT_TINTS.get(family, [1.0, 1.0, 1.0])}
              for texture, family, density in RULES]}, sort_keys=False))

# The minimap's ground colour and its models (build_minimap_blender.py).
library = yaml.safe_load((ROOT / 'assets_dev/engine/terrain_materials/library.yml').read_text())['materials']
library.update(stage_library['materials'])
DESIGN_COLOURS = {name: colour for name, (colour, _) in bt.MATERIALS.items()}
LAYER_COLOURS = {'creep': DESIGN_COLOURS['creep'], 'creep_wet': DESIGN_COLOURS['wet'],
                 'marsh': DESIGN_COLOURS['marsh'], 'crust': DESIGN_COLOURS['crust'],
                 'membrane': DESIGN_COLOURS['membrane'], 'bone': DESIGN_COLOURS['bone'],
                 'plating': DESIGN_COLOURS['plating'], 'rock': DESIGN_COLOURS['rock']}


def layer_colour(layer):
    with Image.open(ROOT / 'assets_source/engine/terrain_materials' / layer['library'] / 'albedo_height.png') as image:
        tile_size = max(2, int(round(layer['repeat'] / units)))
        tile = np.asarray(image.convert('L').resize((tile_size, tile_size), Image.BOX), dtype=np.float32)
    detail = (tile / max(tile.mean(), 1.0)) ** 0.6
    tile = (np.array(LAYER_COLOURS[layer['name']], dtype=np.float32) / 255) ** 2.2 * detail[..., None]
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
acid_texels = np.kron(acid_mask, np.ones((TEXELS, TEXELS), bool))
colour[acid_texels] = (np.array(DESIGN_COLOURS['acid'], dtype=np.float32) / 255) ** 2.2
(PROJECT / 'work').mkdir(exist_ok=True)
for placement in model_placements:
    placement['model'] = str(model_file(placement['name']))
    placement['scale'] = model_scale(placement['name'])[0]
(PROJECT / 'work/minimap_models.json').write_text(json.dumps(model_placements, indent=1) + '\n')
Image.fromarray(np.clip(colour ** (1 / 2.2) * 255 + 0.5, 0, 255).astype(np.uint8), 'RGB').save(
    PROJECT / 'work/ground_colour.png')

# Previews and the build record.
review = PROJECT / 'review'
review.mkdir(exist_ok=True)
low, high = heights.min(), heights.max()
Image.fromarray(((heights - low) / (high - low) * 255).astype(np.uint8), 'L').resize((512, 512)).save(
    review / 'heights.png')
Image.fromarray(np.clip(colour[::4, ::4] ** (1 / 2.2) * 255, 0, 255).astype(np.uint8), 'RGB').save(
    review / 'ground.png')
counts = {}
for entity in entities:
    counts[entity['name']] = counts.get(entity['name'], 0) + 1
report = {'map': MAP, 'map_id': 9120, 'bmodels': len(models), 'faces': sum(len(m.faces) for m in models),
          'entities': len(entities), 'decorations': counts, 'actors': len(actors), 'hostile_placed': hostile_placed,
          'spawn_points': len(spawns), 'chests': len(loot), 'ground_items': len(ground_items),
          'missing_ground_items': missing_items, 'events': sorted(EVENTS),
          'height_range': [int(heights.min()), int(heights.max())], 'south_edge_worst': worst,
          'arrivals': ARRIVALS, 'd09_mouth': ARRIVALS['d09_mouth'],
          'garden': {'gate': GARDEN['wall']['gate']['position'], 'wicket': GARDEN['wall']['wicket']['position']},
          'people': people, 'actor_groups': {str(g): [a['actor_index'] for a in actors if a['group'] == g]
                                             for g in sorted({a['group'] for a in actors})},
          'behaviours': behaviours, 'levels': {'d5_door': round(d5_level), 'gantry_foot': round(foot_level),
                                               'hatchery': round(hatchery_level), 'station': round(station_level)},
          'chest_positions': [list(c['position'].values()) for c in loot],
          'tablets': {p['cell']: p['position'] for p in TABLETS}, 'relays': [p['position'] for p in RELAYS],
          'kite_roosts': [[g, m, round(x), round(y)] for g, m, x, y, _ in roost_spots],
          'spires_dropped': len(dropped), 'moved': moved}
(PROJECT / 'out3_build.json').write_text(json.dumps(report, indent=1) + '\n')
print(json.dumps({k: report[k] for k in ('map', 'bmodels', 'faces', 'entities', 'actors', 'spawn_points', 'chests',
                                         'ground_items', 'height_range', 'south_edge_worst', 'spires_dropped')}))
print('arrivals', json.dumps(ARRIVALS))
print('missing ground items', missing_items, 'moved', len(moved))
