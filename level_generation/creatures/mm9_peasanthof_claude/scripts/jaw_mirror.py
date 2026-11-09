"""Symmetric lower face (user review r9, 2026-11-04, review/user_20261104/jaw_asymmetry_r9.png: her right lower face runs as a straight
diagonal from the cheek to the chin, narrower and flatter than her left, which is the correct rounded jaw). The fuller side of the
lower face (cheek, jaw, jaw corner, chin) is mirrored onto the narrower side across the face midline (the vertical plane through the
nose tip): every skin-shell vertex (the head component holding the nose) of the narrower side in the region moves toward the mirror
image of the closest point on the fuller side's surface (BVH of the fuller side's faces). Weight 1 in the region, eased to 0 (smooth)
over the region's upper edge (Y1-0.02..Y1, the cheekbone), its lower edge (Y0..Y0+0.016, the neck seam stays welded to the body), near
the midline (T0..T0+15 deg from the front) and toward the back (T1-20..T1 deg); the mouth (a sphere of R_MOUTH round the lips' centre)
is excluded with a 1 cm ease, so the lips, tusks, nose and eyes stay as they are. Positions only.
Args: <in blend> <out blend> [y0 1.636] [y1 1.748] [t0 12] [t1 135] [r_mouth 0.02] [mouth_dy -0.043] [export head y 1.697] [side auto|+|-]"""
import bpy, bmesh, sys, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
f = lambda i, d: float(a[i]) if len(a) > i else d
Y0, Y1, T0, T1, RM, MDY, HEADY = f(2, 1.636), f(3, 1.748), f(4, 12.0), f(5, 135.0), f(6, 0.02), f(7, -0.043), f(8, 1.697)
SIDE = a[9] if len(a) > 9 else 'auto'
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent; mw = ob.matrix_world; mwi = mw.inverted()
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
hb = next(b for b in rig.pose.bones if b.name.endswith('Head')); off = HEADY - (rig.matrix_world @ hb.head).z
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
hv = {v.index for f_ in bm.faces if f_[lh] and not f_[lk] for v in f_.verts}
W = {i: mw @ bm.verts[i].co for i in hv}
fr = [i for i in hv if 1.70 - off < W[i].z < 1.78 - off]
nose = min(fr, key=lambda i: W[i].y)                      # faces -y
comp = {nose}; st = [bm.verts[nose]]
while st:
    v = st.pop()
    for e in v.link_edges:
        o = e.other_vert(v)
        if o.index in hv and o.index not in comp: comp.add(o.index); st.append(o)
cx = W[nose].x
band = [i for i in comp if Y0 - off < W[i].z < Y1 - off]
cy = 0.5 * (min(W[i].y for i in band) + max(W[i].y for i in band))
def ang(p): return math.degrees(math.atan2(abs(p.x - cx), -(p.y - cy)))
def ss(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
reg = [i for i in band if T0 < ang(W[i]) < T1]
def fullness(sgn): 
    r = [math.hypot(W[i].x - cx, W[i].y - cy) for i in reg if (W[i].x - cx) * sgn > 0]
    return sum(r) / max(len(r), 1)
fp, fm = fullness(1), fullness(-1)
full = (1 if fp >= fm else -1) if SIDE == 'auto' else (1 if SIDE == '+' else -1)
# BVH of the fuller side's shell faces (original positions)
faces = [f_ for f_ in bm.faces if f_[lh] and not f_[lk] and all(v.index in comp for v in f_.verts)
         and sum((W[v.index].x - cx) * full for v in f_.verts) > 0]
vmap = {}; verts = []; polys = []
for f_ in faces:
    pl = []
    for v in f_.verts:
        if v.index not in vmap: vmap[v.index] = len(verts); verts.append(W[v.index])
        pl.append(vmap[v.index])
    polys.append(pl)
bvh = BVHTree.FromPolygons(verts, polys)
mouth = Vector((cx, 0, W[nose].z + MDY)); mouth.y = W[nose].y + 0.02
moved = 0; mx = 0.0
for i in reg:
    p = W[i]
    if (p.x - cx) * full >= 0: continue                    # only the narrower side moves
    t = ang(p); z = p.z + off
    w = ss((z - Y0) / 0.016) * ss((Y1 - z) / 0.02) * ss((t - T0) / 15.0) * ss((T1 - t) / 20.0)
    w *= ss(((p - mouth).length - RM) / 0.01)
    if w <= 0: continue
    m = Vector((2 * cx - p.x, p.y, p.z))
    q, _, _, _ = bvh.find_nearest(m)
    if q is None: continue
    tgt = Vector((2 * cx - q.x, q.y, q.z))
    d = (tgt - p) * w
    bm.verts[i].co = mwi @ (p + d); moved += 1; mx = max(mx, d.length)
bm.to_mesh(ob.data); bm.free(); ob.data.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('JAWMIRROR fuller side', '+x' if full > 0 else '-x', 'mean radius +x', round(fp * 1000, 1), '-x', round(fm * 1000, 1),
      'mm; moved', moved, 'max', round(mx * 1000, 1), 'mm')
