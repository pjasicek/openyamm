#!/usr/bin/env python3
"""A5 (2026-11-21, 17th session, D-58): D-54's checks on D3's entrance:d7_fall in a build (or installed) folder.
   d54_check.py <folder with xeen_d3.odm and xeen_d3.scene.yml>
Heights at the point's node and its eight neighbours, the tiles of the four cells round it (water/lava), every
building face, decoration and spawn/actor within 256, and every ranged hostile (missile or spell) within 5,888."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json, math, os, subprocess, sys, yaml

ROOT = _REPO_ROOT
PX, PY, PZ = -15360, 11776, 1440
CX, CY = 34, 41
folder = sys.argv[1]
exp = os.path.join(ROOT, 'output/studio_cal/d3/scratch/d54_export.json')
subprocess.run([ROOT + '/openyamm-studio/build-xeen/oymap', 'export', os.path.join(folder, 'xeen_d3.odm'),
                '--out', exp], check=True, stdout=subprocess.DEVNULL)
m = json.load(open(exp))['map']
t = m['terrain']
H = lambda x, y: t['height_map'][y * 128 + x] * t['height_scale']
print('heights round node [34, 41] (rows y 40-42, x 33-35):')
for y in (40, 41, 42):
    print('  ', [H(x, y) for x in (33, 34, 35)])
print('  the four cells touching the point: corners', sorted({H(x, y) for x in (33, 34, 35) for y in (40, 41, 42)}))
lookup = m['tile_set_lookup']
tiles = {(x, y): t['tile_map'][y * 128 + x] for x in (33, 34) for y in (40, 41)}
tt = [l.rstrip('\n').split('\t') for l in open(ROOT + '/assets_dev/engine/data_tables/terrain_tile_data_2.txt')]
tt = [r for i, r in enumerate(tt) if len(r) >= 7 and not (i == 0 and r[0].strip().lower() == 'index')]
for k in sorted(set(tiles.values())):   # xeen: ids under 90 direct, else the tileset lookup (game TerrainTileData.cpp)
    di = k if k < 90 else lookup[(k - 90) // 36] + (k - 90) % 36
    fl = int(tt[di][6], 0)
    print('  tile %d -> %s flags 0x%04x: %s' % (k, tt[di][1], fl, 'WATER' if fl & 2 else 'BURN (lava)' if fl & 1
                                                   else 'land, no water or lava'))
print('tile ids of cells [33-34, 40-41]:', tiles, 'tile set lookup', lookup, 'attributes',
      {(x, y): t['attribute_map'][y * 128 + x] for x in (33, 34) for y in (40, 41)})


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    u = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - u * dx, py - ay - u * dy)


def inside(px, py, poly):
    c = False
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[i], poly[i - 1]
        if (ay > py) != (by > py) and px < (bx - ax) * (py - ay) / (by - ay) + ax:
            c = not c
    return c


near_b = []
for b in m['bmodels']:
    v = b['vertices']
    best = 1e9
    for f in b.get('faces', []):
        idx = f.get('vertex_indices') or f.get('vertices') or []
        pts = [v[i][:2] for i in idx]
        if not pts:
            continue
        if inside(PX, PY, pts) and max(v[i][2] for i in idx) > H(CX, CY) + 8:
            best = 0
        for i in range(len(pts)):
            best = min(best, seg_dist(PX, PY, *pts[i], *pts[i - 1]))
    if not b.get('faces'):
        best = min(math.hypot(PX - p[0], PY - p[1]) for p in v)
    near_b.append((best, b['name']))
near_b.sort()
print('nearest buildings (xy distance to a face edge):', [(round(d), n) for d, n in near_b[:5]])
sc = yaml.safe_load(open(os.path.join(folder, 'xeen_d3.scene.yml')))
ents = sorted((math.hypot(e['position']['x'] - PX, e['position']['y'] - PY), e.get('name'),
               e.get('decoration_list_id')) for e in sc['entities'])
print('nearest decorations:', [(round(d), n, i) for d, n, i in ents[:6]])
print('within 256:', [(round(d), n) for d, n, i in ents if d <= 256 and n != 'party start'],
      [(round(d), n) for d, n in near_b if d <= 256])
# ranged: missile (Attack 1/2 Miss) or a spell with Use% > 0
rows = [l.rstrip('\n').split('\t') for l in open(ROOT + '/assets_dev/worlds/xeen/data_tables/monster_data.txt')]
mon = {r[0]: r for r in rows[3:] if r and r[0].isdigit()}
by_pic = {}
for r in mon.values():
    by_pic.setdefault(r[2].rsplit(' ', 1)[0], []).append(r)
ranged = lambda r: r[19] not in ('0', '') or r[23] not in ('0', '') or r[24] not in ('0', '') or r[26] not in ('0', '')
ms = next(l.rstrip('\n').split('\t') for l in open(ROOT + '/assets_dev/worlds/xeen/data_tables/map_stats.txt')
          if '\txeen_d3.odm\t' in l)
slots = {1: ms[16], 2: ms[20], 3: ms[24]}
print('map_stats slots:', slots, {k: [(r[0], r[1], 'ranged' if ranged(r) else 'melee') for r in by_pic[v]]
                                 for k, v in slots.items()})
hostile_near = []
for s in sc['spawns']:
    d = math.hypot(s['position']['x'] - PX, s['position']['y'] - PY)
    if s['type_id'] == 3:
        rs = by_pic.get(slots.get(s['index'], ''), [])
        hostile_near.append((d, 'marker slot %d %s' % (s['index'], slots.get(s['index'])), any(ranged(r) for r in rs)))
for a in sc['initial_state']['actors']:
    d = math.hypot(a['position']['x'] - PX, a['position']['y'] - PY)
    r = mon.get(str(a['monster_info_id']))
    hostile_near.append((d, 'actor %s %s' % (a['monster_info_id'], a.get('name') or (r[1] if r else '?')),
                         bool(r and ranged(r))))
hostile_near.sort()
print('nearest markers/actors:', [(round(d), n, rg) for d, n, rg in hostile_near[:6]])
rn = [(round(d), n) for d, n, rg in hostile_near if rg]
print('ranged within 5,888:', [x for x in rn if x[0] <= 5888], '; nearest ranged anywhere:', rn[:1])
