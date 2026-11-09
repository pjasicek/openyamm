"""Body neck under the narrow jaw (r10, 2026-11-04): jaw_mirror3.py moved the neck seam down by up to 14.5 mm on her right side and
carried the shift into the body neck below (3 cm falloff) plus a radial projection; the neck's few large triangles there caught
the light as a dark angular facet under the jaw in the front view. The displacement of the body-only vertices near the seam
(against the reference blend, same vertex indices: the subdivision only appended vertices) is relaxed by Laplacian smoothing
(ITER passes, half toward the neighbour mean; head-shell and seam vertices, and everything the jaw pass did not move, stay
fixed), so the neck follows the moved seam smoothly. Head geometry (and so the head paint) is unchanged.
MODE follow (used): the body-only vertices take only the seam's displacement, faded over 3 cm below it (no projection, no fold).
Args: <reference blend (before jaw_mirror3)> <in blend> <out blend> [iter 12] [rings 1] [mode relax|follow]"""
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
ITER = int(a[3]) if len(a) > 3 else 12
RINGS = int(a[4]) if len(a) > 4 else 1
MODE = a[5] if len(a) > 5 else 'relax'
FALL = 0.03
bpy.ops.wm.open_mainfile(filepath=a[0])
ref = [v.co.copy() for v in bpy.data.objects['Body'].data.vertices]
bpy.ops.wm.open_mainfile(filepath=a[1])
ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
lh = bm.faces.layers.int['head']
n0 = len(ref)
D = {i: bm.verts[i].co - ref[i] for i in range(n0)}
# vertices the subdivision added (head faces; some sit on the seam and are shared with body faces): their displacement is the
# mean of their original-index neighbours' (they lie on edges between those)
for v in bm.verts[n0:]:
    nb = [D[e.other_vert(v).index] for e in v.link_edges if e.other_vert(v).index < n0]
    D[v.index] = sum(nb, Vector()) / max(len(nb), 1)
headv = {v.index for f in bm.faces if f[lh] for v in f.verts}
moved = {i for i in range(n0) if D[i].length > 1e-6}
free = [i for i in moved if i not in headv]               # body-only vertices the jaw pass moved
# also let their body neighbours (unmoved, RINGS rings) relax, so the transition spreads further
for _ in range(RINGS):
    ring = {e.other_vert(bm.verts[i]).index for i in free for e in bm.verts[i].link_edges}
    free = sorted(set(free) | {i for i in ring if i < n0 and i not in headv})
fs = set(free)
mx0 = max((D[i].length for i in free), default=0.0)
if MODE == 'follow':
    # the body neck only follows the moved seam: inverse-distance mean (3 nearest) of the seam vertices' displacement, faded to 0
    # over FALL below the seam; the radial projection of the body neck (the fold) is dropped
    from mathutils.kdtree import KDTree
    seam = [v.index for v in bm.verts if any(f[lh] for f in v.link_faces) and any(not f[lh] for f in v.link_faces)
            and D[v.index].length > 1e-6]
    kd = KDTree(len(seam))
    for k, i in enumerate(seam): kd.insert(bm.verts[i].co, k)
    kd.balance()
    body = [i for i in range(n0) if i not in headv and D[i].length > 1e-6]
    for i in body:
        p = ref[i]; nb = kd.find_n(p, 3)
        if not nb: D[i] = Vector(); continue
        tw = 0.0; acc = Vector()
        for _co, k, d in nb:
            w = 1.0 / max(d, 1e-4); tw += w; acc += w * D[seam[k]]
        d0 = nb[0][2]; t = max(0.0, min(1.0, 1.0 - d0 / FALL)); fall = t * t * (3 - 2 * t)
        D[i] = acc / tw * fall
    free = body; ITER = 0
for _ in range(ITER):
    E = {}
    for i in free:
        nb = [D[e.other_vert(bm.verts[i]).index] for e in bm.verts[i].link_edges]
        E[i] = 0.5 * D[i] + 0.5 * (sum(nb, Vector()) / max(len(nb), 1))
    for i in free: D[i] = E[i]
for i in free: bm.verts[i].co = ref[i] + D[i]
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=a[2])
print('NECKRELAX body vertices relaxed', len(free), 'max shift before', round(mx0 * 1000, 1), 'mm, after',
      round(max((D[i].length for i in free), default=0.0) * 1000, 1), 'mm')
