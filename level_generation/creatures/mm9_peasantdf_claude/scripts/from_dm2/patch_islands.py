"""Own UV islands for the collapsed-UV patch faces, plus backing plates behind the cheek gaps (face pass 2026-11-02).
1. Every head face with ~zero HeadUV area (cheek_patch.py / bridge_hole.py) gets a planar front projection (x, z) of its own
   at the head set's density (UV_PER_M), placed in a free cell (CELL) of the head set (cells not touched by any head face's UV
   bounding box), so project_face.py and the other paint steps colour it like any texel.
2. Backing plates: head faces of the face shell (real UV area, front y < -0.08) within R (x-z distance) of each point are
   duplicated and moved DEPTH along their inward normal; they keep UVs, attributes and weights, and close any crack seen
   from the front with the skin behind it instead of the background. Args: <in blend> <out blend> <x,z;x,z...> [R 0.02] [DEPTH 0.002]"""
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
PTS = [tuple(float(v) for v in s.split(',')) for s in a[2].split(';')]
R = float(a[3]) if len(a) > 3 else 0.02; DEPTH = float(a[4]) if len(a) > 4 else 0.002
UV_PER_M, CELL, G = 1.12, 1 / 32, 32
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
L = bm.loops.layers.uv['HeadUV']; hd = bm.faces.layers.int.get('head'); hn = bm.faces.layers.int.get('hand')
def isheadish(f):
    return (hd and f[hd]) or (hn and f[hn])
def area(f):
    u = [l[L].uv for l in f.loops]
    return abs((u[1] - u[0]).cross(u[2] - u[0])) / 2 if len(u) == 3 else 1.0
used = [[False] * G for _ in range(G)]
for f in bm.faces:
    if not isheadish(f) or area(f) < 1e-9:
        continue
    us = [l[L].uv for l in f.loops]
    x0, x1 = int(max(min(u.x for u in us), 0) * G), int(min(max(u.x for u in us), 0.9999) * G)
    y0, y1 = int(max(min(u.y for u in us), 0) * G), int(min(max(u.y for u in us), 0.9999) * G)
    for i in range(x0, x1 + 1):
        for j in range(y0, y1 + 1):
            used[i][j] = True
free = [(i, j) for i in range(G) for j in range(G) if not used[i][j] and not (i and used[i - 1][j]) and not (j and used[i][j - 1])
        and not (i < G - 1 and used[i + 1][j]) and not (j < G - 1 and used[i][j + 1])]
n_island = 0
cells = []
for f in bm.faces:
    if not (hd and f[hd]) or area(f) >= 1e-9:
        continue
    if not free:
        break
    i, j = free.pop(0)
    co = [Vector((l.vert.co.x, l.vert.co.z)) for l in f.loops]
    lo = Vector((min(c.x for c in co), min(c.y for c in co)))
    span = max(max(c.x for c in co) - lo.x, max(c.y for c in co) - lo.y, 1e-6)
    s = min(UV_PER_M, CELL * 0.8 / span)
    for l, c in zip(f.loops, co):
        l[L].uv = Vector((i * CELL + CELL * 0.1 + (c.x - lo.x) * s, j * CELL + CELL * 0.1 + (c.y - lo.y) * s))
    n_island += 1
    cells.append([i * CELL, 1 - (j + 1) * CELL, (i + 1) * CELL, 1 - j * CELL])   # glTF v (down)
plate = []
for f in list(bm.faces):
    if not (hd and f[hd]) or area(f) < 1e-9:
        continue
    c = f.calc_center_median()
    if c.y < -0.08 and f.normal.y < 0 and any(((c.x - px) ** 2 + (c.z - pz) ** 2) ** 0.5 < R for px, pz in PTS):
        plate.append(f)
res = bmesh.ops.duplicate(bm, geom=plate)
nv = [g for g in res['geom'] if isinstance(g, bmesh.types.BMVert)]
bm.normal_update()
for v in nv:
    v.co -= v.normal * DEPTH
bm.to_mesh(me); me.update()
print('PATCH_ISLANDS islands', n_island, 'free cells left', len(free), 'plate faces', len(plate))
import json, os
json.dump({'cells': cells}, open(os.path.join(os.path.dirname(a[1]), 'patch_islands.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
