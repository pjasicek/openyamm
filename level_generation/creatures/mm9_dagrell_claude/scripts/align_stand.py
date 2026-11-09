"""Dagrell step 1: the Meshy pieces aligned (uniform scale + translation, then similarity ICP) to the MM9 mesh posed at
MM9 Stand frame 0 (the open four-legged pose the HD masters show). Saves a blend with 'Meshy' (welded, aligned, in the
Stand pose space) beside the posed MM9 rig/meshes, and overlay renders.
Args: <mm9 source blend> <meshy glb> <out blend> <out dir> <report json>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, MESHY, OUT, OUTDIR, REP = argv
POSE = ('Stand', 0)
bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
act = bpy.data.actions[POSE[0]]
arm.animation_data_create(); arm.animation_data.action = act
try:
    arm.animation_data.action_slot = act.slots[0]
except Exception:
    pass
sc.frame_set(POSE[1]); bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
A = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        me = o.evaluated_get(dg).to_mesh()
        A += [tuple(o.matrix_world @ v.co) for v in me.vertices]
        o.evaluated_get(dg).to_mesh_clear()
A = np.array(A)


def kdt(P):
    k = KDTree(len(P))
    for i, p in enumerate(P):
        k.insert(Vector(p), i)
    k.balance()
    return k


before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in before]
src = next(o for o in new if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
for o in new:
    bpy.data.objects.remove(o)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.verts.ensure_lookup_table()
B = np.array([tuple(v.co) for v in bm.verts])
s = (A[:, 2].max() - A[:, 2].min()) / (B[:, 2].max() - B[:, 2].min())
t = np.array([(A[:, 0].min() + A[:, 0].max()) / 2 - s * (B[:, 0].min() + B[:, 0].max()) / 2,
              (A[:, 1].min() + A[:, 1].max()) / 2 - s * (B[:, 1].min() + B[:, 1].max()) / 2,
              A[:, 2].min() - s * B[:, 2].min()])
kA = kdt(A)
rng = np.random.default_rng(0)
Bs = B[rng.choice(len(B), min(3000, len(B)), replace=False)]
R = np.eye(3)
for it in range(40):
    X = s * Bs @ R.T + t
    kX = kdt(X)
    p, q = [], []
    for i, x in enumerate(X):
        p.append(Bs[i]); q.append(A[kA.find(Vector(x))[1]])
    for a in A[::max(1, len(A) // 3000)]:
        p.append(Bs[kX.find(Vector(a))[1]]); q.append(a)
    p, q = np.array(p), np.array(q)
    mp, mq = p.mean(0), q.mean(0)
    P0, Q0 = p - mp, q - mq
    if it >= 10:  # translation/scale first, then rotation too
        U, S_, Vt = np.linalg.svd(Q0.T @ P0)
        D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
        R = U @ D @ Vt
    s = float((Q0 * (P0 @ R.T)).sum() / (P0 * P0).sum())
    t = mq - s * (R @ mp)
X = s * B @ R.T + t
for v, x in zip(bm.verts, X):
    v.co = Vector(x)
me = bpy.data.meshes.new('Meshy'); bm.to_mesh(me)
ob = bpy.data.objects.new('Meshy', me); sc.collection.objects.link(ob)
d = np.array([kA.find(Vector(x))[2] for x in X])
rot = math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2))))
rep = {'scale': s, 'rot_deg': rot, 't': t.tolist(), 'dist_mean': float(d.mean()), 'dist_p90': float(np.percentile(d, 90)),
       'mm9_bounds': [A.min(0).tolist(), A.max(0).tolist()], 'meshy_bounds': [X.min(0).tolist(), X.max(0).tolist()]}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
# overlay renders
red = bpy.data.materials.new('red'); red.diffuse_color = (1, 0.15, 0.15, 1)
grey = bpy.data.materials.new('grey'); grey.diffuse_color = (0.85, 0.85, 0.85, 1)
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.data.materials.clear(); o.data.materials.append(grey if o is ob else red)
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = 512
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = 3.0; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector(((A.min(0) + A.max(0)) / 2).tolist())
os.makedirs(OUTDIR, exist_ok=True)
for v, dv in {'left': (1, 0, 0), 'front': (0, -1, 0), 'top': (0, 0.0001, 1), 'q34': (-1, -1.25, 0.55)}.items():
    dv = Vector(dv).normalized(); cam.location = c + dv * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUTDIR, f'al_{v}.png'); bpy.ops.render.render(write_still=True)
print('ALIGN ' + json.dumps(rep))
