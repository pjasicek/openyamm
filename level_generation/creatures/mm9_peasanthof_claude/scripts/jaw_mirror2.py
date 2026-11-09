"""Symmetric lower face, second pass (user review r10, 2026-11-04: the r9 nearest-point mirror (jaw_mirror.py) moved the narrow
side by at most 4.7 mm and left her right jaw a straight diagonal: the narrow side's few large triangles span straight from the cheek
to the chin where the fuller side has a jaw-corner vertex). Here the narrow side's lower-face faces (any vertex with weight > 0) are
first subdivided once (bmesh subdivide_edges, cuts 1, grid fill; UVs, weights and face layers interpolate), then every narrow-side
skin-shell vertex in the region is projected radially onto the mirror image of the fuller side's surface: a ray from the face centre
C = (nose-tip x, mid depth, export height ZC) in the mirrored direction is cast against the fuller side's faces (the crossing nearest
the vertex's own radius; none within 25 mm = left as is), and the
vertex moves along its own direction from C to that radius. Same smooth weights as jaw_mirror.py (upper edge Y1-0.02..Y1 at the
cheekbone, the shell's open edge (neck seam) welded with a 12 mm ease and nothing below Y0, midline T0..T0+15 deg untouched, back T1-20..T1, mouth sphere R_MOUTH excluded with a 1 cm
ease), so the nose, mouth, tusks and eyes stay. Positions and the new vertices only.
Args: <in blend> <out blend> [y0 1.636] [y1 1.748] [t0 12] [t1 135] [r_mouth 0.02] [mouth_dy -0.043] [export head y 1.697]
      [side -|+ : the fuller side, master x sign] [zc 1.715] [cuts 1]"""
import bpy, bmesh, sys, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
f = lambda i, d: float(a[i]) if len(a) > i else d
Y0, Y1, T0, T1, RM, MDY, HEADY = f(2, 1.636), f(3, 1.748), f(4, 12.0), f(5, 135.0), f(6, 0.02), f(7, -0.043), f(8, 1.697)
full = -1 if (a[9] if len(a) > 9 else '-') == '-' else 1
ZC, CUTS = f(10, 1.715), int(f(11, 1))
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
# the shell's open edge (neck seam to the body, the shell boundary) stays welded: weight eased over SEAM_EASE from it
from mathutils.kdtree import KDTree
seam = [i for i in comp if any(not (f_[lh] and not f_[lk]) for f_ in bm.verts[i].link_faces)
        or any(e.is_boundary for e in bm.verts[i].link_edges)]
kd = KDTree(len(seam))
for k, i in enumerate(seam): kd.insert(W[i], k)
kd.balance()
SEAM_EASE = 0.012
def weight(p):
    t = ang(p); z = p.z + off
    w = ss((z - Y0) / 0.004) * ss(kd.find(p)[2] / SEAM_EASE) * ss((Y1 - z) / 0.02) * ss((t - T0) / 15.0) * ss((T1 - t) / 20.0)
    return w * ss(((p - mouth).length - RM) / 0.01)
mouth = Vector((cx, 0, W[nose].z + MDY)); mouth.y = W[nose].y + 0.02
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
# subdivide the narrow side's region faces
nf0 = len(bm.faces)
sub = [f_ for f_ in bm.faces if f_[lh] and not f_[lk] and all(v.index in comp for v in f_.verts)
       and all((W[v.index].x - cx) * full < 0.002 for v in f_.verts) and any((W[v.index].x - cx) * full < 0 and weight(W[v.index]) > 0 for v in f_.verts)]
edges = list({e for f_ in sub for e in f_.edges})
if CUTS > 0:
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=CUTS, use_grid_fill=True, smooth=0.0)
    bmesh.ops.triangulate(bm, faces=[f_ for f_ in bm.faces if len(f_.verts) > 4])
bm.verts.ensure_lookup_table(); bm.verts.index_update()
C = Vector((cx, cy, ZC - off))
moved = 0; mx = 0.0; miss = 0
for v in bm.verts:
    p = mw @ v.co
    if (p.x - cx) * full >= 0: continue                    # only the narrower side moves
    if not any(f_[lh] and not f_[lk] for f_ in v.link_faces): continue
    if not (Y0 - off < p.z < Y1 - off) or not (T0 < ang(p) < T1): continue
    w = weight(p)
    if w <= 0: continue
    u = (p - C).normalized(); um = Vector((-u.x, u.y, u.z))
    o = C.copy(); hits = []
    for _ in range(8):
        h, _n, _i, d = bvh.ray_cast(o, um)
        if h is None: break
        hits.append((h - C).length); o = h + um * 1e-4
    r0 = (p - C).length
    if not hits: miss += 1; continue
    r = min(hits, key=lambda x: abs(x - r0))               # the crossing nearest the vertex's own radius
    if abs(r - r0) > 0.025: miss += 1; continue
    tgt = C + u * r
    d = (tgt - p) * w
    v.co = mwi @ (p + d); moved += 1; mx = max(mx, d.length)
bm.to_mesh(ob.data); bm.free(); ob.data.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('JAWMIRROR2 fuller side', '+x' if full > 0 else '-x', 'subdivided', len(sub), 'faces (', nf0, '->', len(ob.data.polygons), '); moved', moved,
      'max', round(mx * 1000, 1), 'mm; rays missed', miss)
