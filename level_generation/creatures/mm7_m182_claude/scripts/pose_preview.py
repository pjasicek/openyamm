"""Workbench renders of the rig in a pose-parameter dict (dragon_pose), several views; for checking fitted poses.
Usage: pose_preview.py -- <rig.blend> <pose.json or inline json> <outprefix> [views...]"""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector, Quaternion
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P / 'scripts'))
import dragon_pose as DP
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
p = json.loads(Path(a[1]).read_text()) if a[1].endswith('.json') else json.loads(a[1])
if rig.animation_data: rig.animation_data.action = None
axes = {n: b.matrix_local.to_3x3().inverted() for n, b in rig.data.bones.items()}
for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.matrix_basis.identity()
ops, shift = DP.ops(p)
for n, axis, ang in ops:
    if n in rig.pose.bones and ang: pb = rig.pose.bones[n]; pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(axes[n] @ Vector(axis), ang)
rig.pose.bones['Root'].location = axes['Root'] @ Vector(shift); bpy.context.view_layer.update()
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.render.resolution_x = 700; sc.render.resolution_y = 600
cam = bpy.data.objects.new('PC', bpy.data.cameras.new('PC')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.4
dirs = {'front': (0, -1, .05), 'side': (-1, 0, .05), 'top': (0, -.01, 1), 'quarter': (1, -1, .5), 'back': (0, 1, .1)}
t = Vector((0, -.05, .25))
for v in (a[3:] or ['front', 'side', 'top', 'quarter']):
    d = Vector(dirs[v]).normalized(); cam.location = t + d * 3; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[2]}_{v}.png'; bpy.ops.render.render(write_still=True)
