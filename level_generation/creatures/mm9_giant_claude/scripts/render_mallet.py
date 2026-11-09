"""MM9's mallet alone for the Codex HD master (third pass, 2026-11-01): the mallet mesh of a true-handed source in its bind pose, stood
upright (shaft along +Z, head on top, the head's long axis along X), textured, flat light on grey, orthographic. Views: q34 (from front-right,
slightly above), front (-Y), left, back, right, top, and a close view of the head. Args: <glb> <outdir> <prefix> <size>"""
import bpy, sys, math, os
import numpy as np
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix, size = argv[0], argv[1], argv[2], int(argv[3])
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mal = next(o for o in sc.objects if o.type == 'MESH' and o.name.startswith('mallet'))
for o in sc.objects:
    if o.type == 'MESH' and o is not mal: o.hide_render = True
# evaluated (skinned) world vertices of the mallet
dg = bpy.context.evaluated_depsgraph_get(); ev = mal.evaluated_get(dg); me = ev.to_mesh()
P = np.array([ev.matrix_world @ v.co for v in me.vertices]); ev.to_mesh_clear()
c = P.mean(0); u, s, vt = np.linalg.svd(P - c); ax = vt[0]
t = (P - c) @ ax
# the head is the wide end: the side whose far 25 % has the larger spread off the axis
off = np.linalg.norm((P - c) - np.outer(t, ax), axis=1)
if off[t > np.percentile(t, 75)].mean() < off[t < np.percentile(t, 25)].mean(): ax = -ax; t = -t
head = P[t > np.percentile(t, 85)]; hc = head - head.mean(0); hx = np.linalg.svd(hc - np.outer(hc @ ax, ax))[2][0]; hx -= ax * (hx @ ax); hx /= np.linalg.norm(hx)
hy = np.cross(ax, hx)
R = np.array([hx, hy, ax])                  # rows: world X, Y, Z of the upright mallet
M = Matrix.Identity(4)
for i in range(3):
    for j in range(3): M[i][j] = R[i, j]
# move the mallet (and only it) upright: bake the posed mesh into a new object
new = bpy.data.objects.new('MalletUp', ev.data.copy() if False else bpy.data.meshes.new_from_object(ev))
sc.collection.objects.link(new)
new.matrix_world = M @ Matrix.Translation(Vector(-c)) @ ev.matrix_world
mal.hide_render = True
bpy.context.view_layer.update()
Q = np.array([new.matrix_world @ v.co for v in new.data.vertices]); lo, hi = Q.min(0), Q.max(0); cen = (lo + hi) / 2; ext = float((hi - lo).max())
print('MALLET extent', np.round(hi - lo, 3), 'length', round(float(hi[2] - lo[2]), 3))
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.42, 0.42, 0.42, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = size; sc.view_settings.view_transform = 'Standard'
for m in new.data.materials:
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                try: n.inputs['Roughness'].default_value = 1.0
                except Exception: pass
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
def shoot(name, d, scale=1.08, centre=None, up=(0, 0, 1)):
    ce = Vector(centre if centre is not None else cen); d = Vector(d).normalized()
    cam.location = ce + d * 10; cam.data.ortho_scale = ext * scale
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{name}.png'); bpy.ops.render.render(write_still=True)
shoot('q34', (0.75, -0.75, 0.35)); shoot('front', (0, -1, 0)); shoot('left', (-1, 0, 0)); shoot('back', (0, 1, 0)); shoot('right', (1, 0, 0))
shoot('top', (0, -0.01, 1))
hz = float(np.percentile(Q[:, 2], 88)); shoot('head', (0.75, -0.75, 0.35), scale=0.45, centre=(cen[0], cen[1], hz))
print('MALLET renders', outdir, prefix)
