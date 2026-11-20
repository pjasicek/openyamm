"""Backstop tube inside the waist (second pass, see-through gate: the slit at the belt line of the bent trunk; the
vest's and skirt's rims under the belt are already joined to their linings, so the view through the opening gap met
the back faces of the vest above). A closed tube of outward-facing faces sits inside every torso layer from rest z
Z0 to Z1: per ring (every DZ) and per angle (NA around the spine axis at that height) the innermost body surface's
radius x SHRINK. Each tube vertex copies the weights of the nearest body vertex at its angle, so it bends with the
trunk; all faces sample one dark vest texel (region R) of the body paint and carry `lined` = 1 (left out of the shadow
meshes). Hidden at rest; through any gap that opens at the belt the eye meets the dark tube, not the background.
Args (Blender): <in blend> <out blend> <region mask png> <body base colour png> [z0 0.12] [z1 0.40] [shrink 0.86]"""
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, MASK, BASE = a[:4]
Z0 = float(a[4]) if len(a) > 4 else 0.12
Z1 = float(a[5]) if len(a) > 5 else 0.40
SHRINK = float(a[6]) if len(a) > 6 else 0.86
DZ, NA = 0.012, 32
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data; rig = body.parent
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
# dark vest texel
mk = bpy.data.images.load(MASK); bc = bpy.data.images.load(BASE)
mw, mh = mk.size; bw, bh = bc.size
m = np.array(mk.pixels[:], np.float32).reshape(mh, mw, 4)
b = np.array(bc.pixels[:], np.float32).reshape(bh, bw, 4)
bs = b[(np.arange(mh) * bh // mh)][:, (np.arange(mw) * bw // mw)]
lum = bs[..., :3] @ np.array([0.2126, 0.7152, 0.0722])
cand = (m[..., 0] > 0.95)
lumc = np.where(cand, lum, 9)
# a dark texel deep inside the region (5 px from its edge)
from_edge = cand.copy()
for _ in range(5):
    from_edge[1:-1, 1:-1] &= from_edge[:-2, 1:-1] & from_edge[2:, 1:-1] & from_edge[1:-1, :-2] & from_edge[1:-1, 2:]
lumc = np.where(from_edge, lum, 9)
iy, ix = np.unravel_index(np.argsort(lumc, axis=None)[int(from_edge.sum() * 0.05)], lumc.shape)
UV = ((ix + 0.5) / mw, (iy + 0.5) / mh)          # Blender image rows are bottom-up, as UVs
co = np.array([v.co for v in me.vertices])
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
bodyv = np.zeros(len(co), bool)
for p in me.polygons:
    if not hd[p.index] and not hn[p.index]:
        bodyv[list(p.vertices)] = True
# dense surface samples of the body faces (the reduced torso's vertices are several cm apart)
samp = []
bary = np.array([[1/3, 1/3, 1/3], [0.6, 0.2, 0.2], [0.2, 0.6, 0.2], [0.2, 0.2, 0.6], [0.45, 0.45, 0.1], [0.1, 0.45, 0.45],
                 [0.45, 0.1, 0.45], [1, 0, 0]])
for p in me.polygons:
    if hd[p.index] or hn[p.index] or len(p.vertices) != 3:
        continue
    t = co[list(p.vertices)]
    samp.append(bary @ t)
samp = np.concatenate(samp)
torso = np.abs(samp[:, 0]) < 0.2
rings = []
zs = np.arange(Z0, Z1 + 1e-6, DZ)
for z in zs:
    sel = torso & (np.abs(samp[:, 2] - z) < DZ * 0.6)
    P = samp[sel]
    c = np.array([0.5 * (P[:, 0].min() + P[:, 0].max()), 0.5 * (P[:, 1].min() + P[:, 1].max())])
    ang = np.arctan2(P[:, 1] - c[1], P[:, 0] - c[0]); rad = np.linalg.norm(P[:, :2] - c, axis=1)
    ring = []
    for k in range(NA):
        th = 2 * math.pi * k / NA
        d = np.abs((ang - th + math.pi) % (2 * math.pi) - math.pi)
        msk = d < 2 * math.pi / NA
        r = rad[msk].min() if msk.any() else rad.min()
        ring.append(Vector((c[0] + math.cos(th) * r * SHRINK, c[1] + math.sin(th) * r * SHRINK, z)))
    rings.append(ring)
kd = KDTree(int(bodyv.sum()))
idx = np.nonzero(bodyv)[0]
for k, i in enumerate(idx):
    kd.insert(Vector(co[i]), k)
kd.balance()
bm = bmesh.new(); bm.from_mesh(me)
dl = bm.verts.layers.deform.active
uvl = bm.loops.layers.uv['UVMap']
huv = bm.loops.layers.uv.get('HeadUV')
lined = bm.faces.layers.int.get('lined') or bm.faces.layers.int.new('lined')
bm.verts.ensure_lookup_table()
old = list(bm.verts)
VV = []
for ring in rings:
    row = []
    for p in ring:
        v = bm.verts.new(p)
        # weights of the nearest body vertex outward along the ray
        _, k, _ = kd.find(p)
        sv = old[int(idx[k])]
        for g, w in sv[dl].items():
            v[dl][g] = w
        row.append(v)
    VV.append(row)
nf = 0
for i in range(len(VV) - 1):
    for k in range(NA):
        q = [VV[i][k], VV[i][(k + 1) % NA], VV[i + 1][(k + 1) % NA], VV[i + 1][k]]
        f = bm.faces.new(q)        # counter-clockwise seen from outside: normal outward
        for l in f.loops:
            l[uvl].uv = UV
            if huv:
                l[huv].uv = UV
        f[lined] = 1
        f.smooth = True
        nf += 1
bm.normal_update()
bm.to_mesh(me); bm.free(); me.update()
# orientation check after writing
out_ok = 0
for p in me.polygons[-nf:]:
    c = p.center
    if Vector((c.x - 0.0, c.y - 0.03, 0)).dot(Vector((p.normal.x, p.normal.y, 0))) > 0:
        out_ok += 1
if out_ok < nf / 2:
    bpy.context.view_layer.objects.active = body
    for pol in me.polygons[-nf:]:
        pol.flip()
print('BACKSTOP', {'rings': len(VV), 'faces': nf, 'uv': [round(UV[0], 4), round(UV[1], 4)], 'outward_before_flip': out_ok})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
