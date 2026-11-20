"""Do the larger late-game packs (BALANCE_PLAN.md section 3.6) fit the rebuilt rooms? Run from the repository root.

For each rebuilt MM9 BLV in chapters 4-5 (output/mm9_rework/), hostile placed actors are grouped into packs (single
linkage at 1,200 units, as density.py), each pack's target size is the chapter's target pack (4 in chapter 4, 7 in
chapter 5) or its size today when larger, and
the target pack's footprint (each monster a square of its diameter plus 128 units) is compared with the free space
where the pack stands: 16 rays from each member, at its height, to the nearest wall face (capped at 1,536 units), the
roomiest member's place counting. A pack
"fits" when its footprint takes at most a third of that space and the narrowest width across the pack (opposite rays
summed) holds two of its monsters side by side. Sectors are too coarse for this (the Tomb of 1000 Terrors has 20).
The Temple of Honk's Honks are placed non-hostile (they turn on the party in the story) and are counted; passive scripted
actors (the Tomb's flying critters on fixed paths) and unique bosses of level 150 and above are not packs.
"""
import math, sys
import numpy as np
from collections import defaultdict
from pathlib import Path
import yaml

sys.path.insert(0, 'util')
from map_export import parse_blv_file

R = Path('output/mm9_rework/assets_dev/worlds/mm9/maps')
CHAPTER = {4: 'lichlab wizardslab connectingtunnels yanmirsfort darkpassageway bathhouse klusoshouse traininghall '
              'verhoffinruins dungeonofsecrets',
           5: 'templeofhonk 1000terrors arslegardcity dragonstadium hallofthegods'}
FACTOR = {4: 2.0, 5: 3.6}
TARGET = {4: 4, 5: 7}
LEVEL = {}
for line in open('assets_dev/worlds/mm9/data_tables/monster_data.txt', encoding='latin-1').read().splitlines()[3:]:
    c = line.split('\t')
    if len(c) > 3 and c[0].strip().isdigit() and c[3].strip().isdigit():
        LEVEL[int(c[0])] = int(c[3])
CELL, LINK, SHARE = 128, 1200, 1 / 3

def inside(px, py, poly):
    hit, j = False, len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi:
            hit = not hit
        j = i
    return hit

def sector_floors(q):
    """sector -> (area, longest side) of its floor."""
    V = q['vertices']
    cells, boxes = defaultdict(set), {}
    for f in q['faces']:
        if f['facet_type'] not in (3, 4) or f['is_portal']:
            continue
        poly = [(V[i]['x'], V[i]['y']) for i in f['vertex_indices']]
        s = f['room_number']
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        b = boxes.get(s, [1e9, 1e9, -1e9, -1e9])
        boxes[s] = [min(b[0], min(xs)), min(b[1], min(ys)), max(b[2], max(xs)), max(b[3], max(ys))]
        for cx in range(int(min(xs) // CELL), int(max(xs) // CELL) + 1):
            for cy in range(int(min(ys) // CELL), int(max(ys) // CELL) + 1):
                if inside((cx + 0.5) * CELL, (cy + 0.5) * CELL, poly):
                    cells[s].add((cx, cy))
    return {s: (len(c) * CELL * CELL, max(boxes[s][2] - boxes[s][0], boxes[s][3] - boxes[s][1])) for s, c in cells.items()}

RAYS, CAP = 16, 1536.0

def wall_segments(q):
    """Wall edges in plan with their height range: arrays x1, y1, x2, y2, zmin, zmax."""
    V = q['vertices']
    rows = []
    for f in q['faces']:
        if f['facet_type'] != 1 or f['is_portal']:
            continue
        pts = [(V[i]['x'], V[i]['y'], V[i]['z']) for i in f['vertex_indices']]
        zs = [p[2] for p in pts]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            if (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 > 4:
                rows.append((a[0], a[1], b[0], b[1], min(zs), max(zs)))
    return np.array(rows, dtype=float).T if rows else np.zeros((6, 0))

def free_space(walls, x, y, z):
    """Area of the 16-ray polygon around (x, y) at height z, and the narrowest width across it."""
    x1, y1, x2, y2, zmin, zmax = walls
    keep = (zmin <= z + 64) & (zmax >= z + 64) & (np.minimum(x1, x2) < x + CAP) & (np.maximum(x1, x2) > x - CAP) \
        & (np.minimum(y1, y2) < y + CAP) & (np.maximum(y1, y2) > y - CAP)
    ax, ay, bx, by = x1[keep], y1[keep], x2[keep], y2[keep]
    dists = []
    for k in range(RAYS):
        th = 2 * math.pi * k / RAYS
        dx, dy = math.cos(th), math.sin(th)
        ex, ey = bx - ax, by - ay
        den = dx * ey - dy * ex
        with np.errstate(divide='ignore', invalid='ignore'):
            tt = ((ax - x) * ey - (ay - y) * ex) / den
            uu = ((ax - x) * dy - (ay - y) * dx) / den
        hit = (np.abs(den) > 1e-9) & (tt > 1) & (uu >= 0) & (uu <= 1)
        dists.append(float(min(CAP, tt[hit].min())) if hit.any() else CAP)
    area = 0.0
    for k in range(RAYS):
        a, b = 2 * math.pi * k / RAYS, 2 * math.pi * (k + 1) / RAYS
        area += 0.5 * dists[k] * dists[(k + 1) % RAYS] * math.sin(b - a)
    width = min(dists[k] + dists[k + RAYS // 2] for k in range(RAYS // 2))
    return area, width

def packs(actors):
    n = len(actors); parent = list(range(n))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            a, b = actors[i]['p'], actors[j]['p']
            if (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (2 * (a[2] - b[2])) ** 2 <= LINK * LINK:
                parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(actors[i])
    return list(groups.values())

total = defaultdict(lambda: [0, 0, 0])
for chapter, maps in CHAPTER.items():
    for stem in maps.split():
        blv, scene = R / f'{stem}.blv', R / f'{stem}.scene.yml'
        if not blv.exists() or not scene.exists():
            print(f'ch{chapter} {stem}: not rebuilt as BLV'); continue
        q = parse_blv_file(blv)['payload']
        walls = wall_segments(q)
        s = yaml.load(open(scene), Loader=yaml.CSafeLoader)
        actors = []
        for a in (s.get('initial_state') or {}).get('actors') or []:
            if a.get('mm9_civilian') or a.get('npc_id') or (a.get('hostility_type', 4) == 0 and stem != 'templeofhonk'):
                continue
            if ((a.get('mm9_ai') or {}).get('profile') or {}).get('passive') or LEVEL.get(a.get('monster_info_id'), 0) >= 150:
                continue
            p = a['position']
            actors.append(dict(p=(p['x'], p['y'], p['z']), r=int(a.get('radius', 40)), sector=a.get('sector_id'),
                               name=a.get('name', '')))
        if not actors:
            print(f'ch{chapter} {stem}: no hostile placed monsters'); continue
        fits, tight, worst = 0, [], []
        capacity = 0
        for pack in packs(actors):
            target = max(len(pack), TARGET[chapter])
            radius = max(m['r'] for m in pack)
            footprint = target * (2 * radius + 128) ** 2
            area, width = max(free_space(walls, *m['p']) for m in pack)
            ok = footprint <= SHARE * area and width >= 2 * (2 * radius)
            # How many of these monsters the place holds at a third of its space, at most 10 a pack.
            capacity += min(10, max(len(pack), int(SHARE * area / (2 * radius + 128) ** 2)))
            fits += ok
            if not ok:
                tight.append((footprint / max(area, 1), len(pack), target, radius, round(area / 1e6, 2), int(width),
                              pack[0]['name']))
        n = len(packs(actors))
        need = round(len(actors) * FACTOR[chapter])
        total[chapter][0] += n; total[chapter][1] += fits; total[chapter][2] += capacity
        total.setdefault(('need', chapter), [0])[0] += need
        print(f'ch{chapter} {stem:18} holds {capacity:4} at a third of each place, needs {need:4} ({FACTOR[chapter]}x)')
        print(f'ch{chapter} {stem:18} monsters {len(actors):3}  packs {n:3}  fit {fits:3}/{n:<3}', end='')
        if tight:
            tight.sort(reverse=True)
            print('  tightest: ' + '; '.join(f'{nm} {now}->{tg} r{r}: {100*share:.0f}% of {a}M u2, width {w}'
                                            for share, now, tg, r, a, w, nm in tight[:3]))
        else:
            print()
for chapter in sorted(c for c in total if isinstance(c, int)):
    n, fits, capacity = total[chapter]
    print(f'chapter {chapter}: {fits}/{n} packs fit at {TARGET[chapter]} or more; the maps hold {capacity} monsters at '
          f'a third of each place, the plan needs {total[("need", chapter)][0]}')
