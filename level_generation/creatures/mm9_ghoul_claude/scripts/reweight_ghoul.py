"""After UVs (the layout stays): flap weights. Each flap's sides ride the skin under them (weights of the nearest skin point), its centre and tip stay on the MM9 flap bone, its top on the pelvis. Args: <uv blend> <out blend>"""
import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
# the split-chart body layout (repack.py): UVs written face by face, in the order of work/faces.npz
_R = np.load(bpy.path.abspath('//repack.npz'))
_uv = me.uv_layers['UVMap'].data
_loops = np.array([list(p.loop_indices) for p in me.polygons])
for fi, q in zip(_R['body'], _R['uvn']):
    for k in range(3): _uv[int(_loops[fi, k])].uv = (float(q[k, 0]), float(q[k, 1]))
n = len(me.vertices)
P = np.array([v.co[:] for v in me.vertices])
pa = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', pa)
names = [g.name for g in body.vertex_groups]; gid = {k: i for i, k in enumerate(names)}
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
sk = np.nonzero(pa == 0)[0]
polys = [p for p in me.polygons if all(pa[x] == 0 for x in p.vertices)]
tree = BVHTree.FromPolygons([tuple(P[i]) for i in range(n)], [tuple(p.vertices) for p in polys])


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


for pid, bn in ((6, 'Bone01'), (7, 'Bone03')):
    vs = np.nonzero(pa == pid)[0]
    if bn not in gid:
        body.vertex_groups.new(name=bn); names.append(bn); gid[bn] = len(names) - 1; W = np.c_[W, np.zeros(n)]
    # the top and sides ride the skin under them, the centre and tip hang on the MM9 flap bone: the sheet drapes over the thighs and into the gap between them
    for i in vs:
        loc, nor, fi, d = tree.find_nearest(Vector(P[i]))
        f = polys[fi]
        pts = P[list(f.vertices)]; bc = 1 / np.maximum(np.linalg.norm(pts - np.array(loc), axis=1), 1e-5); bc /= bc.sum()
        ws = (W[list(f.vertices)].T * bc).sum(1)
        tz = float(1 - sstep(np.array(0.05 - P[i, 2]), 0.0, 0.10))
        cen = float(1 - sstep(np.array(abs(P[i, 0])), 0.01, 0.10))
        low = float(sstep(np.array(-0.05 - P[i, 2]), 0.0, 0.20))
        fb = max(cen * (1 - tz), low) if pid == 6 else float(sstep(np.array(0.06 - P[i, 2]), 0.0, 0.26))
        row = ws * (1 - fb)
        row[gid[bn]] += fb
        W[i] = row
    print('FLAP', pid, len(vs))
# thumbs: the base edges tore (stretch 2.4): weights relaxed over the thumb's root, tips left rigid
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
for s in 'LR':
    ids = [gid[k] for k in (f'Bip01 {s} Finger0', f'Bip01 {s} Finger01', f'Bip01 {s} Finger02') if k in gid]
    hb = gid[f'Bip01 {s} Hand']
    th = W[:, ids].sum(1)
    near = np.nonzero((th > 0.01) & (W[:, ids[-1]] < 0.5))[0]
    band = set(near.tolist())
    for v in list(band): band |= set(nbr[v])
    band = np.array(sorted(i for i in band if pa[i] == 0))
    for _ in range(6):
        W[band] = 0.5 * W[band] + 0.5 * np.array([W[nbr[i]].mean(0) for i in band])
    print('THUMB', s, len(band))
    for i in band:
        o = np.argsort(-W[i])[:4]; row = np.zeros(W.shape[1]); row[o] = W[i, o]; row[row < 0.02] = 0; row /= row.sum()
        for g_ in body.vertex_groups: g_.remove([int(i)])
        for k in np.nonzero(row)[0]: body.vertex_groups[names[k]].add([int(i)], float(row[k]), 'REPLACE')
np.savez(bpy.path.abspath('//flap_verts.npz'), front=P[pa == 6], back=P[pa == 7])
order = np.argsort(-W, axis=1)
for i in np.nonzero(np.isin(pa, (6, 7)))[0]:
    keep = order[i, :4]; row = np.zeros(W.shape[1]); row[keep] = W[i, keep]; row[row < 0.02] = 0; row /= row.sum()
    for g_ in body.vertex_groups: g_.remove([int(i)])
    for k in np.nonzero(row)[0]: body.vertex_groups[names[k]].add([int(i)], float(row[k]), 'REPLACE')
# the flaps' top rows go in under the belt's lower edge, so the flap comes out from under it (their paint repeats the belt's brass)
for v in me.vertices:
    if pa[v.index] in (6, 7) and v.co.z > 0.095:
        t = min(1.0, (v.co.z - 0.095) / 0.03)
        v.co.y += (0.016 if pa[v.index] == 6 else -0.016) * t
# the studs and the plate lump go: the belt's front is painted from the master (finish_tex.py)
import bmesh
bm = bmesh.new(); bm.from_mesh(me); lay = bm.verts.layers.int['part']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] == 3], context='VERTS')
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
