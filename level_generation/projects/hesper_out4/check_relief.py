"""Read-only walkability check of the Crown's terrain (the relief of 2026-10-24; the stage's check_walkability.py reads
BLVs only).

The engine's rules (game/outdoor): a monster slides off a terrain tile whose four corners span more than 512
(OutdoorGeometryUtils `outdoorTerrainSlopeTooHigh`), the party off a triangle that spans more than 512
(OutdoorMovementController `terrainSlopeTooHigh`). A tile is walkable here when its four corners span at most 512 (the
monsters' stricter rule). The check:

- every place the map or another map puts the party or a monster on the ground (the arrivals, the door poses, the
  grounded placed actors, the spawn points, the chests and items on the ground) stands on a walkable tile of the open
  floor: the tiles connected to the Kreegan Road's arrival;
- no walkable pocket of the floor (below 2 500: not the rim's crest) of at least four tiles is cut off from it (a pit
  or a shelf nobody can reach);
- the roads' grades over each 512: resin paving at most 15 % (build_out4's grading; 19 % allowed for the heights'
  32-unit steps), the tracks at most 30 % (34 %).

    python3 level_generation/projects/hesper_out4/check_relief.py [map.odm]     (exit 1 on a finding)
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file  # noqa: E402

odm = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT / 'runtime/worlds/hesper/maps/hes_out4.odm'
H = np.array(parse_odm_file(odm)['payload']['height_map'], np.float64).reshape(128, 128) * 32.0
scene = json.loads(odm.with_suffix('.scene.yml').read_text())
build = json.loads((PROJECT / 'out4_build.json').read_text())
detail = json.loads((ROOT / 'design/kreegan_world/zone4/crown_detail.json').read_text())
SPAN = 512.0
BOUND = 23040.0


def ground(x, y):
    fx, fy = (x + 32768.0) / 512, (32768.0 - y) / 512
    ix, iy = int(np.clip(math.floor(fx), 0, 126)), int(np.clip(math.floor(fy), 0, 126))
    tx, ty = fx - ix, fy - iy
    if tx + ty <= 1:
        return H[iy, ix] + (H[iy, ix + 1] - H[iy, ix]) * tx + (H[iy + 1, ix] - H[iy, ix]) * ty
    return H[iy + 1, ix + 1] + (H[iy + 1, ix] - H[iy + 1, ix + 1]) * (1 - tx) + (H[iy, ix + 1] - H[iy + 1, ix + 1]) * (1 - ty)


def tile(x, y):
    return int(np.clip(math.floor((32768.0 - y) / 512), 0, 126)), int(np.clip(math.floor((x + 32768.0) / 512), 0, 126))


corners = np.stack([H[:-1, :-1], H[:-1, 1:], H[1:, :-1], H[1:, 1:]])
walkable = (corners.max(0) - corners.min(0)) <= SPAN
labels, count = ndimage.label(walkable)
start = build['arrivals']['kreegan_road']['position']
main = labels[tile(start[0], start[1])]
findings = []

points = [(f'arrival {k}', *v['position']) for k, v in build['arrivals'].items()]
points += [(f'door pose {k}', *v[:3]) for k, v in build['door_poses'].items()]
for a in scene['initial_state']['actors']:
    p = a['position']
    if abs(p['z'] - ground(p['x'], p['y'])) <= 40:
        points.append((f"actor {a['actor_index']} {a['name']}", p['x'], p['y'], p['z']))
points += [(f"spawn {s['spawn_index']}", s['position']['x'], s['position']['y'], s['position']['z'])
           for s in scene['spawns']]
for k, (x, y, z) in enumerate(build['chests_at']):
    if abs(z - ground(x, y)) <= 40:
        points.append((f'chest {k}', x, y, z))
for item in scene['initial_state']['sprite_objects']:
    p = item['position']
    if abs(p['z'] - ground(p['x'], p['y'])) <= 40:
        points.append((f"ground item {item['sprite_object_index']}", p['x'], p['y'], p['z']))
for name, x, y, z in points:
    iy, ix = tile(x, y)
    if not walkable[iy, ix]:
        findings.append(f'{name} at ({x:.0f}, {y:.0f}): its tile is too steep '
                        f'(span {corners[:, iy, ix].max() - corners[:, iy, ix].min():.0f})')
    elif labels[iy, ix] != main:
        findings.append(f'{name} at ({x:.0f}, {y:.0f}): its walkable ground is cut off from the open floor')

# Cut-off pockets of the floor inside the playable square: a pit (lower than the steep ground round it: the party
# slides in and cannot climb out) is a finding; a shelf on a ridge's or an outcrop's top (higher than its sides: out of
# reach on foot, as the rim's crest) is listed.
centres_x = -32768.0 + (np.arange(127) + 0.5) * 512
inside = (np.abs(centres_x)[None, :] < BOUND - 512) & (np.abs(centres_x)[:, None] < BOUND - 512)
mean = corners.mean(0)
pockets, shelves = [], []
for label in range(1, count + 1):
    if label == main:
        continue
    cells = (labels == label) & inside
    if cells.sum() < 4 or mean[cells].mean() >= 2500:
        continue
    iy, ix = np.argwhere(cells)[0]
    entry = (int(cells.sum()), round(float(mean[cells].mean())), round(centres_x[ix]), round(-centres_x[iy]))
    # A pit when the open floor beside it stands higher (the party walks onto the slope and slides in).
    beside = ndimage.binary_dilation(cells, iterations=2) & (labels == main)
    (pockets if beside.any() and mean[beside].max() > mean[cells].mean() + 64 else shelves).append(entry)
for size, z, x, y in pockets:
    findings.append(f'a pit of {size} walkable tiles at about ({x}, {y}, {z}) is cut off from the open floor')

# Road grades.
grades = {}
for kind, limit in (('paving', 0.19), ('track', 0.34)):
    worst = 0.0
    lines = [line for line in detail['roads'][kind]]
    if kind == 'track':
        ring = build['ring']
        lines.append([(14720.0, ring['centre'][1]), (ring['plate'][0] - 200.0, ring['centre'][1])])
    for line in lines:
        for (ax, ay), (bx, by) in zip(line, line[1:]):
            n = max(1, int(math.hypot(bx - ax, by - ay) / 512))
            zs = []
            for k in range(n + 1):
                x, y = ax + (bx - ax) * k / n, ay + (by - ay) * k / n
                if abs(x) < BOUND and abs(y) < BOUND:
                    zs.append((x, y, ground(x, y)))
            for (x0, y0, z0), (x1, y1, z1) in zip(zs, zs[1:]):
                g = abs(z1 - z0) / max(math.hypot(x1 - x0, y1 - y0), 1)
                if g > worst:
                    worst = g
                if g > limit:
                    findings.append(f'{kind} grade {g:.2f} at ({x0:.0f}, {y0:.0f})')
    grades[kind] = round(worst, 3)

floor = inside & (mean < 2500)
print(json.dumps({'height_range': [int(H.min()), int(H.max())],
                  'floor_tiles': int(floor.sum()), 'floor_steep_tiles': int((floor & ~walkable).sum()),
                  'points_checked': len(points), 'pits': len(pockets), 'shelves_out_of_reach': len(shelves), 'road_grades': grades,
                  'findings': len(findings)}))
for f in findings:
    print('  ' + f)
sys.exit(1 if findings else 0)
