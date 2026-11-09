"""Make the Meshy Smart Topology return mirror-symmetric (MM9's hen/rooster are exactly symmetric).

Args: <meshy glb> <out glb> <keep side: neg|pos> [report json]
1. The symmetry plane is found by ICP of the mesh against its own mirror image (yaw about Z, roll about Y and an x
   offset; Meshy faces -Y with +Z up after the glTF import), and the mesh is turned so that plane is x = 0.
2. The kept half (x <= 0 for 'neg': the bird's right) is cut at x = 0 (bisect), mirrored and welded on the seam.
   Separate pieces (eyes, a loose wing) on the kept side are mirrored with it; pieces on the dropped side are removed.
"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

a = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, KEEP = a[0], a[1], a[2]
REP = a[3] if len(a) > 3 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
src = next(o for o in bpy.data.objects if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
P = np.array([tuple(v.co) for v in bm.verts])


def kdt(X):
    k = KDTree(len(X))
    for i, p in enumerate(X):
        k.insert(Vector(p), i)
    k.balance()
    return k


rng = np.random.default_rng(1)
S = P[rng.choice(len(P), min(4000, len(P)), replace=False)]
# iterate: R, t such that M(x) = R x + t is symmetric about x=0, i.e. mirror(M(x)) ~ M(surface)
R = np.eye(3); t = np.array([-(P[:, 0].min() + P[:, 0].max()) / 2, 0, 0])
F = np.diag([-1.0, 1, 1])
for it in range(30):
    X = S @ R.T + t
    k = kdt(X)
    Y = X @ F
    Q = np.array([X[k.find(Vector(y))[1]] for y in Y]) @ F   # mirror of the matched point
    # best rigid motion of X onto midpoints between X and the mirrored matches (Kabsch), restricted by re-solving
    T = (X + Q) / 2
    mx, mt = X.mean(0), T.mean(0)
    U, _, Vt = np.linalg.svd((T - mt).T @ (X - mx))
    D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
    dR = U @ D @ Vt
    R = dR @ R; t = dR @ t + mt - dR @ mx
    t[1] = t[2] = 0.0
X = P @ R.T + t
k = kdt(X)
err = np.array([k.find(Vector(x))[2] for x in (X @ F)[::7]])
ang = math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2))))
for v, x in zip(bm.verts, X):
    v.co = Vector(x)
# drop separate pieces that lie wholly on the dropped side; bisect the rest
sgn = -1 if KEEP == 'neg' else 1
bm.verts.ensure_lookup_table()
seen = set(); drop = []
for v in bm.verts:
    if v.index in seen:
        continue
    comp, st = [], [v]; seen.add(v.index)
    while st:
        u = st.pop(); comp.append(u)
        for e in u.link_edges:
            w = e.other_vert(u)
            if w.index not in seen:
                seen.add(w.index); st.append(w)
    xs = [u.co.x * sgn for u in comp]
    if max(xs) < 0:
        drop += comp
bmesh.ops.delete(bm, geom=drop, context='VERTS')
geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=(0, 0, 0), plane_no=(sgn, 0, 0),
                             clear_inner=True, clear_outer=False)
for v in bm.verts:
    if abs(v.co.x) < 2e-4:
        v.co.x = 0.0
# faces lying in the mirror plane would be doubled by the mirror (non-manifold): drop them
inplane = [f for f in bm.faces if all(abs(v.co.x) < 1e-6 for v in f.verts)]
bmesh.ops.delete(bm, geom=inplane, context='FACES_ONLY')
me = bpy.data.meshes.new('Sym'); bm.to_mesh(me)
ob = bpy.data.objects.new('Sym', me); bpy.context.scene.collection.objects.link(ob)
for o in list(bpy.data.objects):
    if o is not ob:
        bpy.data.objects.remove(o)
mod = ob.modifiers.new('mirror', 'MIRROR'); mod.use_axis[0] = True; mod.use_mirror_merge = True
mod.merge_threshold = 2e-4; mod.use_clip = True
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.modifier_apply(modifier='mirror')
# seam clean-up: weld near-coincident seam vertices, fill slits left on the plane, drop duplicate faces
cb = bmesh.new(); cb.from_mesh(ob.data)
seam = [v for v in cb.verts if abs(v.co.x) < 1e-4]
bmesh.ops.remove_doubles(cb, verts=seam, dist=6e-4)
for v in cb.verts:
    if abs(v.co.x) < 1e-4:
        v.co.x = 0.0
seen_f = {}
dups = []
for f in cb.faces:
    k = tuple(sorted(v.index for v in f.verts))
    if k in seen_f:
        dups.append(f)
    else:
        seen_f[k] = f
bmesh.ops.delete(cb, geom=dups, context='FACES_ONLY')
slit = [e for e in cb.edges if e.is_boundary and all(abs(v.co.x) < 1e-4 for v in e.verts)]
filled = bmesh.ops.holes_fill(cb, edges=slit, sides=0)['faces'] if slit else []
bmesh.ops.triangulate(cb, faces=filled)
# non-manifold edges on the seam: remove the extra faces lying across the seam
nm = [e for e in cb.edges if len(e.link_faces) > 2]
extra = []
for e in nm:
    fs = sorted(e.link_faces, key=lambda f: f.calc_area())
    extra += fs[:len(fs) - 2]
bmesh.ops.delete(cb, geom=list(set(extra)), context='FACES_ONLY')
bmesh.ops.delete(cb, geom=[v for v in cb.verts if not v.link_faces], context='VERTS')
bmesh.ops.recalc_face_normals(cb, faces=cb.faces[:])
seam_rep = {'dup_faces': len(dups), 'slit_edges': len(slit), 'nonmanifold_fixed': len(nm),
            'open_after': sum(1 for e in cb.edges if e.is_boundary),
            'nonmanifold_after': sum(1 for e in cb.edges if len(e.link_faces) > 2)}
cb.to_mesh(ob.data); cb.free()
for p in ob.data.polygons:
    p.use_smooth = True
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True, export_format='GLB', export_yup=True,
                          export_materials='NONE', export_attributes=False)
rep = {'seam': seam_rep, 'plane_rot_deg': ang, 'plane_t': t.tolist(), 'mirror_err_mean': float(err.mean()),
       'mirror_err_p90': float(np.percentile(err, 90)), 'size': (P.max(0) - P.min(0)).tolist(),
       'verts': len(ob.data.vertices), 'tris': sum(len(p.vertices) - 2 for p in ob.data.polygons)}
if REP:
    json.dump(rep, open(REP, 'w'), indent=1)
print('SYM ' + json.dumps(rep))
