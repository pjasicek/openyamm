"""Diagnosis: the fist pose of work/hand_poses.json (grip + wrist turn) on the rest rig of a blend, clay render at the right hand. Args: <blend> <out png>"""
import bpy, sys, json, os
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open(os.path.join(HERE, 'work', 'hand_poses.json')))
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones: pb.matrix_basis.identity(); pb.rotation_mode = 'QUATERNION'
for n, q in list(P['grip'].items()) + list(P['hand_offset'].items()):
    rig.pose.bones[n].rotation_quaternion = (q[3], q[0], q[1], q[2])
# the staff keeps its world frame: Ystaff takes the inverse turn
q = P['hand_offset']['Bip01 R Hand']; qi = Quaternion((q[3], q[0], q[1], q[2])).inverted()
pb = rig.pose.bones['Ystaff']
M0 = pb.matrix.copy()
bpy.context.view_layer.update()
pb.matrix = M0 if False else pb.matrix
bpy.context.view_layer.update()
h = rig.matrix_world @ rig.pose.bones['Bip01 R Hand'].head
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.render.resolution_x = sc.render.resolution_y = 600
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.25, 0.25, 0.28)
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = 0.5; cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for k, d in enumerate([(-1, -0.3, 0.1), (0, -1, 0.1), (-0.3, 1, 0.2)]):
    d = Vector(d).normalized(); c = h + Vector((0, -0.1, -0.12)); cam.location = c + d * 5; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{k}.png'; bpy.ops.render.render(write_still=True)
print('FISTVIEW', tuple(h))
