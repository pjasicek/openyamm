"""Hand geometry alone (vertices within 0.2 m of the wrist on its side, rest pose), rendered from six directions in the
hand's own frame (palm, back, thumb side, pinky side, fingertips, plus wire). Args: -- <rig blend> <side> <out>"""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, side, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
for o in list(bpy.data.objects):
    if o is not body:
        bpy.data.objects.remove(o, do_unlink=True)
for m in list(body.modifiers):
    body.modifiers.remove(m)
wr = Vector(json_w := (0, 0, 0))
import json
J = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'joints_final.json')))['joints']
wr = Vector(J[f'{side}_Hand']); fa = Vector(J[f'{side}_Forearm'])
bm = bmesh.new(); bm.from_mesh(body.data)
d = (wr - fa).normalized()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if (v.co - wr).length > 0.2 or (v.co - wr).dot(d) < -0.01 or v.co.x * wr.x < 0], context='VERTS')
bm.to_mesh(body.data); bm.free()
body.show_wire = True
scene = bpy.context.scene; common.workbench_clay(scene)
co = np.array([tuple(v.co) for v in body.data.vertices]); c = co.mean(0)
U = np.linalg.svd(co - c, full_matrices=False)[2]
dirs = {'palm': U[2], 'back': -U[2], 'side_a': U[1], 'side_b': -U[1], 'tips': U[0] if U[0] @ (c - np.array(wr)) > 0 else -U[0]}
for name, v in dirs.items():
    cam_dir = Vector(v).normalized()
    data = bpy.data.cameras.new('c'); data.type = 'ORTHO'; data.ortho_scale = 0.2
    cam = bpy.data.objects.new('c', data); scene.collection.objects.link(cam)
    cam.location = Vector(c) + cam_dir * 1.0
    cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (-cam_dir).to_track_quat('-Z', 'Y')
    scene.camera = cam; scene.render.resolution_x = scene.render.resolution_y = 420
    scene.render.filepath = f'{out}_{name}.png'; bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
print('HANDVERTS', len(co))
