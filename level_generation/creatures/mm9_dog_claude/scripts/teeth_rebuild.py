"""Clean teeth for the dog: Meshy's tooth rows are jagged clusters that shred in the 2K paint. They are replaced by
simple closed cones along the dental arcades, each rigid on its own jaw, rooted 2 mm in the gum, and none reaching the
opposite lip when the mouth is closed (the slit is 11 mm at bind). UVs: every cone maps into one small ivory patch in
free atlas space (work/teeth.json), so the Meshy paint on the rest of the layout stays valid.
Args: <in blend (uv_v1)> <out blend> <json>"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scipy_free_dt import largest_square

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
f = lambda y: 0.7475 + 0.03 * (y + 0.5)
UP, JAW = 'Xmouth', 'Xjawpiv'
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
me = body.data
uvl = me.uv_layers['UVMap']
# free patch
S = 512
mask = np.zeros((S, S), bool)
me.calc_loop_triangles()
for t in me.loop_triangles:
    p = np.array([tuple(uvl.data[l].uv) for l in t.loops]) * S
    x0, y0 = np.maximum(np.floor(p.min(0)).astype(int) - 1, 0)
    x1, y1 = np.minimum(np.ceil(p.max(0)).astype(int) + 1, S - 1)
    mask[y0:y1 + 1, x0:x1 + 1] = True
cx, cy, half = largest_square(mask)
u0, v0, du = (cx - half * 0.7) / S, (cy - half * 0.7) / S, 1.4 * half / S
rep = {'patch': [u0, v0, du], 'patch_px_2k': du * 2048}
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
pl, cl = bm.verts.layers.int['piece'], bm.verts.layers.int['chain']
dl = bm.verts.layers.deform.active
hl = bm.faces.layers.int['head']
uv = bm.loops.layers.uv['UVMap']
gi = {g.name: g.index for g in body.vertex_groups}
seen, removed = set(), 0
for v in bm.verts:
    if v.index in seen or v[pl] == 0:
        continue
    c, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); c.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    p = np.array([tuple(x.co) for x in c])
    if 0.7 < p[:, 2].mean() < 0.8 and np.ptp(p[:, 1]) <= 0.09:
        bmesh.ops.delete(bm, geom=c, context='VERTS')
        removed += 1
rep['removed_pieces'] = removed
SIDES = 5


def cone(cen, tip_dir, length, r, bone, flat=1.0):
    """Closed cone, root ring at cen (flattened across the arcade by flat), tip along tip_dir."""
    ring = []
    c = Vector(cen)
    d = Vector(tip_dir).normalized()
    a = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0))
    u = (a - d * a.dot(d)).normalized()
    w = d.cross(u)
    for k in range(SIDES):
        t = 2 * math.pi * k / SIDES
        ring.append(bm.verts.new(c + u * (math.cos(t) * r) + w * (math.sin(t) * r * flat)))
    tip = bm.verts.new(c + d * length)
    base = bm.verts.new(c - d * 0.0005)
    vs = ring + [tip, base]
    for v in vs:
        v[pl] = 2; v[cl] = -1
        v[dl][gi[bone]] = 1.0
    for k in range(SIDES):
        n = (k + 1) % SIDES
        f1 = bm.faces.new((ring[k], ring[n], tip)); f2 = bm.faces.new((ring[n], ring[k], base))
        for fc in (f1, f2):
            fc[hl] = 0
            fc.smooth = True
        for l in f1.loops:
            i = ring.index(l.vert) if l.vert in ring else None
            l[uv].uv = (u0 + du * 0.5, v0 + du) if i is None else (u0 + du * (0.1 + 0.8 * i / (SIDES - 1)), v0)
        for l in f2.loops:
            i = ring.index(l.vert) if l.vert in ring else None
            l[uv].uv = (u0 + du * 0.5, v0) if i is None else (u0 + du * (0.1 + 0.8 * i / (SIDES - 1)), v0 + du * 0.15)


def both(x, y, z, d, length, r, bone, flat=1.0):
    cone((x, y, z), (0.08 * np.sign(x) * 0 + d[0], d[1], d[2]), length, r, bone, flat)
    if abs(x) > 1e-6:
        cone((-x, y, z), (-d[0], d[1], d[2]), length, r, bone, flat)


down, up = (0, -0.08, -1), (0, -0.05, 1)
# upper: incisors, canines, premolars along the lip
for x in (0.0045, 0.0135, 0.0225):
    y = -0.5075 + (x / 0.03) ** 2 * 0.009
    both(x, y, f(y) + 0.0075, down, 0.0115, 0.0034, UP)
both(0.031, -0.4965, f(-0.4965) + 0.0075, (0.02, -0.08, -1), 0.0165, 0.0042, UP)
for t in np.linspace(0, 1, 4):
    x, y = 0.0355 + 0.006 * t, -0.484 + 0.066 * t
    both(x, y, f(y) + 0.0075, down, 0.0115 - 0.003 * t, 0.0044, UP, 0.7)
# lower: incisors, canines, premolars
for x in (0.0042, 0.0118, 0.0185):
    y = -0.4965 + (x / 0.025) ** 2 * 0.007
    both(x, y, 0.7345, up, 0.0085, 0.0028, JAW)
both(0.0245, -0.4885, f(-0.4885) - 0.0075 - 0.003, (0, -0.05, 1), 0.0135, 0.0038, JAW)
for t in np.linspace(0, 1, 4):
    x, y = 0.0300 + 0.0055 * t, -0.474 + 0.056 * t
    both(x, y, f(y) - 0.0075, up, 0.0085 - 0.002 * t, 0.004, JAW, 0.7)
rep['tris'] = sum(len(p.verts) - 2 for p in bm.faces)
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'))
print('TEETH ' + json.dumps(rep))
