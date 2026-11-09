"""HOF1: the head shell's neck strip behind the jaw corners juts out past the jaw on one side only (r6 "pale wedge beside the jaw";
r7's nape_strip_in.py pulled both sides in by a fixed factor and the user saw a pinched, cut-off jaw: "deformed right part of the
face/chin? not symmetrical?"). Mirror match instead: every skin-shell vertex (the head component holding the nose) below YTOP (export
height) and behind the jaw front (export z < ZB) is compared with the nearest shell vertex to its mirror image (plane through the nose
tip); if it stands more than TOL further from the centre plane, its x moves in to the mirrored neighbour's distance (weight 1 below
YTOP - 0.013, easing to 0 at YTOP). Inward only, x only, the narrower side and everything above YTOP (the jaw line) untouched.
Args: <in blend> <out blend> [ytop 1.668] [zb -0.02] [tol 0.004] [export head y 1.697]"""
import bpy, bmesh, sys
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
YTOP = float(a[2]) if len(a) > 2 else 1.668; ZB = float(a[3]) if len(a) > 3 else -0.02
TOL = float(a[4]) if len(a) > 4 else 0.004; HEADY = float(a[5]) if len(a) > 5 else 1.697
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent; mw = ob.matrix_world; mwi = mw.inverted()
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
hb = next(b for b in rig.pose.bones if b.name.endswith('Head')); off = HEADY - (rig.matrix_world @ hb.head).z
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
hv = {v.index for f in bm.faces if f[lh] and not f[lk] for v in f.verts}
W = {i: mw @ bm.verts[i].co for i in hv}
fr = [i for i in hv if 1.70 - off < W[i].z < 1.78 - off]
nose = min(fr, key=lambda i: W[i].y)
comp = {nose}; st = [bm.verts[nose]]
while st:
    v = st.pop()
    for e in v.link_edges:
        o = e.other_vert(v)
        if o.index in hv and o.index not in comp: comp.add(o.index); st.append(o)
cx = W[nose].x
ids = sorted(comp); kd = KDTree(len(ids))
for k, i in enumerate(ids): kd.insert(W[i], k)
kd.balance()
zt = YTOP - off; moved = []
for i in ids:
    p = W[i]
    if p.z >= zt or -p.y > ZB: continue                    # export z = -master y
    e = min(1.0, (zt - p.z) / 0.013); e = e * e * (3 - 2 * e)
    m = Vector((2 * cx - p.x, p.y, p.z))
    near = [ids[k] for (_, k, _) in kd.find_n(m, 6) if (W[ids[k]].x - cx) * (p.x - cx) < 0]
    if not near: continue
    j = min(near, key=lambda q: (W[q] - m).length)
    d_self, d_other = abs(p.x - cx), abs(W[j].x - cx)
    if d_self <= d_other + TOL: continue
    nx = cx + (1 if p.x > cx else -1) * (d_self + (d_other - d_self) * e)
    bm.verts[i].co = mwi @ Vector((nx, p.y, p.z)); moved.append(round((d_self - abs(nx - cx)) * 1000, 1))
bm.to_mesh(ob.data); bm.free(); ob.data.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('STRIPMIRROR moved', len(moved), 'mm', moved)
