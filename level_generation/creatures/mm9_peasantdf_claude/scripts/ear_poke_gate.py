"""Job 7 gate: the modelled ears against the hair/hood shell (and DF3's braids) in every clip. For each ear vertex of the
posed LOD0 mesh a ray toward the head's centre (the posed mean of the head skin) must meet the skin before any
hair/hood/braid face; a hair face first means the ear stands outside the hair there (pokes through it) by that distance.
Every 2nd frame at 30 fps of every animation. Prints per clip the worst poke (mm) and the frames over 1 mm, plus the
same for the braids. Args: <unmirrored runtime glb (work/mm9_pdfN_floor.glb)> <ears npz> [step 2]"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
glb, npz = a[0], a[1]; STEP = int(a[2]) if len(a) > 2 else 2
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
ob = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'PeasantDF')
actions = [act for act in bpy.data.actions]
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
dg = bpy.context.evaluated_depsgraph_get(); bpy.context.view_layer.update()


def posed():
    dg = bpy.context.evaluated_depsgraph_get()
    e = ob.evaluated_get(dg); m = e.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    M = np.array(ob.matrix_world); co = co @ M[:3, :3].T + M[:3, 3]
    tri = np.empty(len(m.loop_triangles) * 3, int) if m.loop_triangles else None
    m.calc_loop_triangles(); tri = np.empty(len(m.loop_triangles) * 3, int); m.loop_triangles.foreach_get('vertices', tri)
    e.to_mesh_clear()
    return co, tri.reshape(-1, 3)


rest, tri = posed()
# the undeformed mesh (bind pose) for matching the npz; `rest` (the imported rest pose) can differ by ~1-2 mm
bind = np.empty(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get('co', bind); bind = bind.reshape(-1, 3)
Mw = np.array(ob.matrix_world); bind = bind @ Mw[:3, :3].T + Mw[:3, 3]
E = np.load(npz); ep = E['pos']; ep_b = np.stack([ep[:, 0], -ep[:, 2], ep[:, 1]], 1)    # glTF -> Blender axes
kt = KDTree(len(rest))
for i, p in enumerate(bind): kt.insert(Vector(tuple(p)), i)
kt.balance()
for _ in range(3):        # the npz's export-frame lift is nominal: align by the mean nearest-vertex offset
    hits = [kt.find(Vector(tuple(p))) for p in ep_b]
    off = np.median(np.array([tuple(h[0]) for h in hits]) - ep_b, 0); ep_b = ep_b + off
d = np.array([kt.find(Vector(tuple(p)))[2] for p in ep_b])
print('EARGATE npz offset mm', np.round(off * 1000, 2))
ear_tol = np.median(d)
assert ear_tol < 0.001, f'ear vertices not found in the GLB (median {ear_tol:.4f} m)'
near_i = np.array([kt.find(Vector(tuple(p)))[1] for p in ep_b], int)
# welded components
key = np.round(rest, 4); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
par = np.arange(inv.max() + 1)
def find(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x
for t in tri:
    r = [find(inv[v]) for v in t]
    for q in r[1:]:
        if q != r[0]: par[q] = r[0]
root = np.array([find(inv[v]) for v in range(len(rest))])
labs, cnt = np.unique(root, return_counts=True)
skin = labs[cnt.argmax()]
for l, c in sorted(zip(labs, cnt), key=lambda x: -x[1])[:12]:
    q = rest[root == l]; print('EARGATE part', c, np.round(q.mean(0), 3), np.round(q.min(0), 3), np.round(q.max(0), 3))
rl, rc = np.unique(root[near_i], return_counts=True)
ear_roots = {l for l, c in zip(rl, rc) if c > 50 and (root == l).sum() < 1000}     # the two ear parts
earv = np.nonzero(np.isin(root, list(ear_roots)))[0]
hair_roots = {l for l, c in zip(labs, cnt) if l != skin and l not in ear_roots and c > 300 and rest[root == l, 2].mean() > 0.95}
braid_roots = {l for l, c in zip(labs, cnt) if l != skin and l not in ear_roots and l not in hair_roots and 60 < c <= 300
               and rest[root == l, 2].mean() > 0.85 and np.abs(rest[root == l, 0]).mean() < 0.15}
tri_root = root[tri[:, 0]]
skin_t = tri[(tri_root == skin)]; hair_t = tri[np.isin(tri_root, list(hair_roots))]; braid_t = tri[np.isin(tri_root, list(braid_roots))]
headskin = np.nonzero((root == skin) & (rest[:, 2] > 0.98) & (np.abs(rest[:, 0]) < 0.11))[0]
print('EARGATE ear verts', len(earv), 'match median mm', round(float(ear_tol) * 1000, 2), 'hair parts', len(hair_roots),
      'braid parts', len(braid_roots), 'hair tris', len(hair_t), 'braid tris', len(braid_t))
res = {}


def check(co):
    c = Vector(tuple(co[headskin].mean(0)))
    bs = BVHTree.FromPolygons([Vector(tuple(p)) for p in co], skin_t.tolist())
    out = {}
    for name, tt in (('hair', hair_t), ('braid', braid_t)):
        if not len(tt): out[name] = 0.0; continue
        bh = BVHTree.FromPolygons([Vector(tuple(p)) for p in co], tt.tolist())
        worst = 0.0
        for v in earv:
            p = Vector(tuple(co[v])); dv = (c - p); L = dv.length; dv.normalize()
            hh = bh.ray_cast(p + dv * 1e-4, dv, L)
            if hh[0] is None: continue
            hs = bs.ray_cast(p + dv * 1e-4, dv, L)
            dh = (hh[0] - p).length
            if hs[0] is None or dh < (hs[0] - p).length:
                worst = max(worst, dh)
        out[name] = worst * 1000
    return out


r0 = check(rest); res['rest'] = {k: round(v, 1) for k, v in r0.items()}
for act in actions:
    rig.animation_data.action = act
    f0, f1 = [int(round(x)) for x in act.frame_range]
    w = {'hair': 0.0, 'braid': 0.0}; over = {'hair': 0, 'braid': 0}; n = 0
    for f in range(f0, f1 + 1, STEP):
        bpy.context.scene.frame_set(f)
        co, _ = posed(); r = check(co); n += 1
        for k in w:
            w[k] = max(w[k], r[k]); over[k] += r[k] > 1.0
    res[act.name] = {'frames': n, 'hair_max_mm': round(w['hair'], 1), 'hair_frames_over_1mm': over['hair'],
                     'braid_max_mm': round(w['braid'], 1), 'braid_frames_over_1mm': over['braid']}
    print('EARGATE', act.name, json.dumps(res[act.name]))
print('EARGATE_RESULT', json.dumps(res))
