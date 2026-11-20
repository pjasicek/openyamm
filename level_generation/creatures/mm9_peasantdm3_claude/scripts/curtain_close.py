"""Close the gap between the lengthened hair curtain and the cheek / jaw / neck (clay review/clay/sheet_wall_cmp.png:
background between head and curtain from the front). MM9's PeasantDM3 hair hugs the sides of the face. Per side, on a
grid over y (front .. behind the ear) and z (curtain bottom .. temple), a ray from the head axis outward finds the head
or body surface (lat_s) and then the hair curtain's inner surface (lat_h); the curtain is moved inward by
delta = max(0, lat_h - lat_s - CLEAR), smoothed over the grid (sigma SIG cells) and feathered out over 10 cm toward the back and 6 cm toward the crown. Every hair
vertex moves by the delta at its (y, z) (inner and outer layer together: thickness kept). Positions only.
Then every hair vertex within PUSH of the tunic (torso part) is pushed out along the nearest normal.
Args: -- <in blend> <out blend> [CLEAR 0.003] [PUSH 0.006] [SIG 2.5]"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def gaussian_filter(a, sigma):
    # separable Gaussian, nearest padding (Blender's Python has no scipy)
    r = int(3 * sigma + 0.5); k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    out = a.astype(float)
    for ax in (0, 1):
        pad = [(0, 0), (0, 0)]; pad[ax] = (r, r)
        b = np.pad(out, pad, mode='edge')
        out = sum(k[i] * np.take(b, range(i, i + a.shape[ax]), axis=ax) for i in range(2 * r + 1))
    return out
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts_lib as L
argv = sys.argv[sys.argv.index('--') + 1:]
CLEAR = float(argv[2]) if len(argv) > 2 else 0.003
PUSH = float(argv[3]) if len(argv) > 3 else 0.006
# smoothing (grid cells of 1 cm) and wide feathers: a sharp feather (3 cm toward the back, 2 cm at the crown) folded the
# curtain into a deep vertical crease at the side of the head (review/clay/sheet_wedge.png)
SIG = float(argv[4]) if len(argv) > 4 else 2.5
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
co = L.rest_coords(body); lab = L.loose_parts(me)
hair = lab[np.argmax(co[:, 2])]
cand = np.where((co[:, 2] > 0.40) & (co[:, 2] < 0.47))[0]
shell = lab[cand[np.argmin(co[cand, 1])]]
torso = int(np.bincount(lab).argmax())
S = np.where(lab == shell)[0]; HV = np.where(lab == hair)[0]
xc = (co[S, 0].min() + co[S, 0].max()) / 2
vs = co.tolist()
def tree(parts):
    return BVHTree.FromPolygons(vs, [list(f.vertices) for f in me.polygons if lab[f.vertices[0]] in parts])
tb, th = tree({shell, torso}), tree({hair})
YS = np.arange(-0.07, 0.10, 0.01); ZS = np.arange(0.32, 0.52, 0.01)
rep = {}
new = co.copy()
for side in (-1, 1):
    D = np.zeros((len(YS), len(ZS))); M = np.zeros_like(D)
    for i, y in enumerate(YS):
        for j, z in enumerate(ZS):
            o = Vector((xc, y, z)); d = Vector((side, 0, 0))
            hb, _, _, db = tb.ray_cast(o, d)
            if hb is None: continue
            hh, _, _, dh = th.ray_cast(o + d * db, d)
            if hh is None or dh > 0.08: continue
            D[i, j] = max(0.0, dh - CLEAR); M[i, j] = 1
    # feather: no move behind y 0.07 (the back hair already lies on the neck) or above z 0.50
    fy = np.clip((0.13 - YS) / 0.10, 0, 1)[:, None]; fz = np.clip((0.53 - ZS) / 0.06, 0, 1)[None, :]
    Ds = gaussian_filter(D * M, SIG) / np.maximum(gaussian_filter(M, SIG), 1e-6) * (gaussian_filter(M, SIG) > 0.15)
    Ds = Ds * fy * fz
    rep[side] = {'cells': int(M.sum()), 'max_cm': round(float(Ds.max()) * 100, 2), 'p90_cm': round(float(np.percentile(Ds[Ds > 0], 90)) * 100, 2) if (Ds > 0).any() else 0}
    sel = HV[np.sign(co[HV, 0] - xc) == side]
    yi = np.clip((co[sel, 1] - YS[0]) / 0.01, 0, len(YS) - 1.001); zi = np.clip((co[sel, 2] - ZS[0]) / 0.01, 0, len(ZS) - 1.001)
    i0, j0 = yi.astype(int), zi.astype(int); fi, fj = yi - i0, zi - j0
    val = (Ds[i0, j0] * (1 - fi) * (1 - fj) + Ds[i0 + 1, j0] * fi * (1 - fj) + Ds[i0, j0 + 1] * (1 - fi) * fj + Ds[i0 + 1, j0 + 1] * fi * fj)
    inside = (co[sel, 1] >= YS[0]) & (co[sel, 1] <= YS[-1]) & (co[sel, 2] >= ZS[0]) & (co[sel, 2] <= ZS[-1])
    val = val * inside
    new[sel, 0] -= side * val
    rep[side]['moved'] = int((val > 1e-4).sum())
# the curtain moved inward must stay outside the tunic (the back collar rises to 0.40 m and poked through the hair at the
# nape, review/shots/sheet_f1_b.png): any hair vertex within PUSH of the torso part is pushed out along its normal
tt = BVHTree.FromPolygons(vs, [list(f.vertices) for f in me.polygons if lab[f.vertices[0]] == torso])
pushed = 0
for vi in HV:
    loc, nor, _, dist = tt.find_nearest(Vector(new[vi]))
    if loc is None: continue
    d = (Vector(new[vi]) - loc).dot(nor)
    if d < PUSH:
        new[vi] = np.array(loc + nor * PUSH); pushed += 1
rep['pushed_out_of_torso'] = pushed
me.vertices.foreach_set('co', new.reshape(-1)); me.update()
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
print('CURTAIN', json.dumps(rep))
