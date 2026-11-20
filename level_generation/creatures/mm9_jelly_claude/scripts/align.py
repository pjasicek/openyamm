"""Global similarity alignment of the Meshy mesh onto the MM9 bind mesh (re-oriented source blend), then overlay
renders (MM9 red, Meshy grey) front/left/top.
Args: <mm9 source blend> <meshy glb> <out blend> <out dir> <prefix>
Meshy is scaled by the bounding-box height ratio (z), centred on x/y, bottom on the floor, then refined by
symmetric nearest-point ICP (uniform scale, rotation about z only, translation)."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, MESHY, OUT, ODIR, PRE = argv
bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
mm9 = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        vs = [o.matrix_world @ v.co for v in me.vertices]
        for t in me.loop_triangles:  # surface samples
            a, b, c = (vs[i] for i in t.vertices)
            for u, v in ((1/3, 1/3), (0.6, 0.2), (0.2, 0.6), (0.2, 0.2)):
                mm9.append(a * u + b * v + c * (1 - u - v))
        o.evaluated_get(dg).to_mesh_clear()
A = np.array([tuple(p) for p in mm9])
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in before]
mesh = next(o for o in new if o.type == 'MESH')
mesh.name = 'Meshy'
bpy.context.view_layer.update()
mesh.data.transform(mesh.matrix_world)
mesh.parent = None
mesh.matrix_world = Matrix()
for o in new:
    if o is not mesh:
        bpy.data.objects.remove(o)
B = np.array([tuple(v.co) for v in mesh.data.vertices])
s = (A[:, 2].max() - A[:, 2].min()) / (B[:, 2].max() - B[:, 2].min())
cA = (A.min(0) + A.max(0)) / 2; cB = (B.min(0) + B.max(0)) / 2
t = np.array([cA[0] - s * cB[0], cA[1] - s * cB[1], A[:, 2].min() - s * B[:, 2].min()])
R = np.eye(3)


def tree(P):
    k = KDTree(len(P))
    for i, p in enumerate(P):
        k.insert(p, i)
    k.balance()
    return k


kA = tree(A)
rng = np.random.default_rng(0)
Bs = B[rng.choice(len(B), min(3000, len(B)), replace=False)]
As = A[rng.choice(len(A), min(3000, len(A)), replace=False)]
for it in range(40):
    X = (s * Bs @ R.T) + t
    kX = tree(X)
    src, dst = [], []
    for i, x in enumerate(X):
        dst.append(A[kA.find(x)[1]]); src.append(Bs[i])
    for a in As:
        j = kX.find(a)[1]
        src.append(Bs[j]); dst.append(a)
    src, dst = np.array(src), np.array(dst)
    # similarity with rotation about z only
    ms, md = src.mean(0), dst.mean(0)
    S0, D0 = src - ms, dst - md
    num = (S0[:, 0] * D0[:, 1] - S0[:, 1] * D0[:, 0]).sum(); den = (S0[:, 0] * D0[:, 0] + S0[:, 1] * D0[:, 1]).sum()
    th = math.atan2(num, den)
    R = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    s = float((D0 * (S0 @ R.T)).sum() / (S0 * S0).sum())
    t = md - s * (R @ ms)
X = (s * B @ R.T) + t
for v, x in zip(mesh.data.vertices, X):
    v.co = Vector(x)
d = np.array([kA.find(Vector(x))[2] for x in X])
rep = {'scale': s, 'yaw_deg': math.degrees(math.atan2(R[1, 0], R[0, 0])), 'translate': t.tolist(),
       'dist_mean': float(d.mean()), 'dist_p90': float(np.percentile(d, 90)), 'dist_max': float(d.max())}
print('ALIGN ' + json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
# overlay renders
red = bpy.data.materials.new('red'); red.diffuse_color = (1, 0.1, 0.1, 1)
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not mesh:
        o.data.materials.clear(); o.data.materials.append(red)
        o.show_wire = True
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_xray = True; sh.xray_alpha = 0.6
sc.render.resolution_x = sc.render.resolution_y = 512
lo, hi = A.min(0), A.max(0); c = Vector(((lo + hi) / 2).tolist())
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float((hi - lo).max()) * 1.15; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
os.makedirs(ODIR, exist_ok=True)
for v, dv in {'front': (0, -1, 0), 'left': (1, 0, 0), 'top': (0, 0.0001, 1)}.items():
    dv = Vector(dv).normalized()
    cam.location = c + dv * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(ODIR, f'{PRE}_{v}.png')
    bpy.ops.render.render(write_still=True)
