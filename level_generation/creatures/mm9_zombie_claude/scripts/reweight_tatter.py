"""Tatter on the trousers (cloth gate): every tatter vertex takes the weights of the nearest point of the trouser/hip skin (barycentric), so the cloth rides the thigh exactly and no thigh passes through it in any clip;
and sits at least CLEAR outside that skin at rest. UVs and triangles unchanged. Args: <in blend> <out blend>"""
import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
CLEAR = 0.012
bpy.ops.wm.open_mainfile(filepath=IN)
b = bpy.data.objects['Body']; me = b.data
n = len(me.vertices)
pa = np.zeros(n, np.int32); me.attributes['part'].data.foreach_get('value', pa)
P = np.array([v.co[:] for v in me.vertices])
G = len(b.vertex_groups)
W = np.zeros((n, G), np.float32)
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
tri = [p.vertices[:] for p in me.polygons if all(pa[i] == 1 for i in p.vertices)]
bvh = BVHTree.FromPolygons([Vector(q) for q in P], tri)
T = np.array(tri)
moved = 0
for i in np.nonzero(pa == 2)[0]:
    loc, nor, fi, d = bvh.find_nearest(Vector(P[i]))
    if loc is None: continue
    a, b_, c = P[T[fi]]
    q = np.array(loc)
    # barycentric
    v0, v1, v2 = b_ - a, c - a, q - a
    d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    u = (d11 * d20 - d01 * d21) / den if abs(den) > 1e-14 else 0.33; w = (d00 * d21 - d01 * d20) / den if abs(den) > 1e-14 else 0.33
    bc = np.clip([1 - u - w, u, w], 0, 1); bc /= bc.sum()
    W[i] = (W[T[fi]] * bc[:, None]).sum(0)
    s = (P[i] - q) @ np.array(nor)
    if s < CLEAR:
        me.vertices[int(i)].co = Vector(P[i] + np.array(nor) * (CLEAR - s)); moved += 1
print('TATTER moved', moved)
for i in np.nonzero(pa == 2)[0]:
    o = np.argsort(-W[i])[:4]; row = np.zeros(G, np.float32); row[o] = W[i, o]; row[row < 0.02] = 0; row /= row.sum()
    for g in range(G):
        vg = b.vertex_groups[g]
        if row[g] > 0: vg.add([int(i)], float(row[g]), 'REPLACE')
        else: vg.remove([int(i)])
# head/neck band: wider (4.4 -> 7 cm), the hair locks rigid on the head; Head_h carries the arc
names = {g.name: g.index for g in b.vertex_groups}
hd, nk, hh = names['Bip01 Head'], names['Bip01 Neck'], names['Bip01 Head_h']
P2 = np.array([v.co[:] for v in me.vertices])
def sstep(x, a, c):
    t = np.clip((x - a) / (c - a), 0, 1); return t * t * (3 - 2 * t)
t_ = sstep(P2[:, 2] - (0.815 + 0.25 * P2[:, 1]), -0.035, 0.035)
for i in np.nonzero(pa >= 10)[0]:
    t = 1.0 if pa[i] >= 11 else float(t_[i])
    row = {nk: max(1 - 2 * t, 0.0), hh: 1 - abs(2 * t - 1), hd: max(2 * t - 1, 0.0)}
    for g in range(G):
        vg = b.vertex_groups[g]
        if row.get(g, 0) > 0.01: vg.add([int(i)], float(row[g]), 'REPLACE')
        else: vg.remove([int(i)])
# neck base narrowed: the head's neck flared to the body ring's width (0.16 m) in a collar of painted hair; the ring comes in to 0.117 m, shoulders and neck following on smooth falloffs (no UV change)
fx = lambda x: np.clip((0.26 - np.abs(x)) / 0.1, 0, 1)
Pn = np.array([v.co[:] for v in me.vertices])
for i in range(n):
    if pa[i] == 0 and Pn[i, 2] > 0.72:
        t = sstep(Pn[i, 2], 0.72, 0.797) * fx(Pn[i, 0])
    elif pa[i] >= 10 and pa[i] != 12 and pa[i] != 13 and Pn[i, 2] < 0.86:
        t = 1 - sstep(Pn[i, 2], 0.797, 0.86)
    else:
        continue
    me.vertices[i].co.x = float(Pn[i, 0] * (1 - 0.28 * t))
# armpit: weights relaxed along the mesh where the arm folds against the chest
W2 = np.zeros((n, G), np.float32)
for v in me.vertices:
    for g in v.groups: W2[v.index, g.group] = g.weight
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, c = e.vertices; nbr[a].append(c); nbr[c].append(a)
rig = b.parent
ja = {s_: np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s_} UpperArm'].head_local) for s_ in 'LR'}
sel = []
for s_ in 'LR':
    d_ = np.linalg.norm((Pn - ja[s_]) * np.array([1, 1, 1]), axis=1)
    sel += np.nonzero((pa == 0) & (d_ < 0.16) & (Pn[:, 2] < ja[s_][2] + 0.0))[0].tolist()
sel = np.array(sel)
print('ARMPIT verts', len(sel))
for _ in range(6):
    W2[sel] = np.array([0.5 * W2[i] + 0.5 * W2[nbr[i]].mean(0) if nbr[i] else W2[i] for i in sel])
for i in sel:
    o = np.argsort(-W2[i])[:4]; row = np.zeros(G, np.float32); row[o] = W2[i, o]; row[row < 0.015] = 0; row /= row.sum()
    for g in range(G):
        vg = b.vertex_groups[g]
        if row[g] > 0: vg.add([int(i)], float(row[g]), 'REPLACE')
        elif W2[i, g] > 0: vg.remove([int(i)])
# repacked body atlas
Rp = np.load(bpy.path.abspath('//repack.npz'))
uvl = me.uv_layers['UVMap'].data
for k, fi in enumerate(Rp['body']):
    p = me.polygons[int(fi)]
    for c, li in enumerate(p.loop_indices): uvl[li].uv = tuple(float(x) for x in Rp['uvn'][k, c])
print('REPACK uv', len(Rp['body']))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
