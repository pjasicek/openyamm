"""A disc across the inside of the dress at the hips, facing down (see-through gate: the view up the skirt of the fallen
woman met the culled back faces of the torso shell). At height Z (MM9 frame) rays from the body axis go out in N
directions to the outermost body shell (cast from outside in; body faces only); the cap ring sits at 0.96 x each
hit radius, a fan to the centre, facing down. Weights: every ring vertex takes the weights of the nearest body vertex,
the centre the mean of the ring's. UVMap: each ring vertex the UV of its hit point on the shell (the dress paint at that
height), the centre their mean texel (a dark dress texel: the darkest ring UV); HeadUV copied. Faces only added.
Args: <in blend> <out blend> <body base colour png (unused, kept for the chain's signature)> [z -0.06] [n 40]"""
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
Z = float(a[3]) if len(a) > 3 else -0.06
N = int(a[4]) if len(a) > 4 else 40
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']; me = ob.data; rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mw = ob.matrix_world; mwi = mw.inverted()
bm = bmesh.new(); bm.from_mesh(me)
lh = bm.faces.layers.int.get('head'); lhand = bm.faces.layers.int.get('hand')
uvm = bm.loops.layers.uv['UVMap']; uvh = bm.loops.layers.uv.get('HeadUV')
dl = bm.verts.layers.deform.verify()
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
body = [f for f in bm.faces if not (lh and f[lh]) and not (lhand and f[lhand])]
vs = sorted({v for f in body for v in f.verts}, key=lambda v: v.index)
vidx = {v.index: i for i, v in enumerate(vs)}
P = [mw @ v.co for v in vs]
tris = []; tri_face = []
for f in body:
    ids = [vidx[v.index] for v in f.verts]
    for k in range(1, len(ids) - 1):
        tris.append([ids[0], ids[k], ids[k + 1]]); tri_face.append((f, 0, k, k + 1))
bvh = BVHTree.FromPolygons(P, tris)
# axis: centre of the body vertices in a 4 cm band at Z, between the thighs' outer limits
band = np.array([tuple(p) for p in P if abs(p.z - Z) < 0.02 and abs(p.x) < 0.35])
cx, cy = float(np.median(band[:, 0])), float(0.5 * (band[:, 1].min() + band[:, 1].max()))
C = Vector((cx, cy, Z))
ring = []; uvs = []
for k in range(N):
    t = 2 * math.pi * k / N
    d = Vector((math.cos(t), math.sin(t), 0))
    hit = bvh.ray_cast(C + d * 0.6, -d, 0.6)       # from outside in: the outermost shell (the skirt), not the legs
    if hit[0] is None:
        continue
    f, i0, i1, i2 = tri_face[hit[2]]
    lp = f.loops
    tri_v = [mw @ lp[i0].vert.co, mw @ lp[i1].vert.co, mw @ lp[i2].vert.co]
    tri_uv = [Vector((lp[i][uvm].uv.x, lp[i][uvm].uv.y, 0)) for i in (i0, i1, i2)]
    uv = barycentric_transform(hit[0], *tri_v, *tri_uv)
    p = C + (hit[0] - C) * 0.96
    ring.append(p); uvs.append((uv.x, uv.y))
if len(ring) < 8:
    raise SystemExit('waist cap: too few hits')
kd_pts = np.array([tuple(mw @ v.co) for v in vs])
def nearest_weights(p):
    i = int(np.argmin(((kd_pts - np.array(p[:])) ** 2).sum(1)))
    return {g: w for g, w in vs[i][dl].items()}
new = [bm.verts.new(mwi @ p) for p in ring]
cen = bm.verts.new(mwi @ C)
acc = {}
for v, p in zip(new, ring):
    for g, w in nearest_weights(p).items():
        v[dl][g] = w; acc[g] = acc.get(g, 0.0) + w / len(ring)
for g, w in acc.items():
    cen[dl][g] = w
mu = (sum(u[0] for u in uvs) / len(uvs), sum(u[1] for u in uvs) / len(uvs))
faces = []
for k in range(len(new)):
    a_, b_ = new[k], new[(k + 1) % len(new)]
    f = bm.faces.new([cen, b_, a_])           # wound to face down (-z)
    f.smooth = True
    if lh: f[lh] = 0
    if lhand: f[lhand] = 0
    f.material_index = body[0].material_index
    for lp in f.loops:
        if lp.vert is cen:
            lp[uvm].uv = uvs[k]
        elif lp.vert is a_:
            lp[uvm].uv = uvs[k]
        else:
            lp[uvm].uv = uvs[(k + 1) % len(new)]
        if uvh:
            lp[uvh].uv = (0.999, 0.999)
    faces.append(f)
for f in faces:
    f.normal_update()
    if f.normal.z > 0:
        f.normal_flip()
bm.to_mesh(me); me.update()
print('WAIST_CAP z', Z, 'centre', [round(x, 3) for x in C], 'ring', len(ring), 'faces', len(faces))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
