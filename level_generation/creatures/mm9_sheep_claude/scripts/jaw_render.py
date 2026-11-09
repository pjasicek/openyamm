"""Head close-ups with the jaw posed as MM9 clip@frame (or bind). Args: <blend> <outdir> <prefix> <clip@frame|-> [ortho]"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc = bpy.context.scene
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for x in bpy.data.objects:
    if x.type == 'MESH' and x.name != 'Body' and x.name != 'Horns':
        x.hide_render = True
if argv[3] != '-':
    c, f = argv[3].split('@')
    arm.animation_data.action = bpy.data.actions[c]
    sc.frame_set(int(f))
else:
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
bpy.context.view_layer.update()
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = os.environ.get('COLOR', 'MATERIAL')
sc.display.shading.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 500
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(argv[4]) if len(argv) > 4 else 0.22
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
pb = arm.pose.bones['Xhead']
M = arm.matrix_world @ pb.matrix
c = M @ (pb.bone.matrix_local.inverted() @ Vector((0, -0.66, 0.79)))
R = M.to_3x3() @ pb.bone.matrix_local.to_3x3().inverted()
for n, d in {'front': (0, -1, 0.1), 'side': (1, -0.2, 0.05), 'below': (0.3, -0.8, -0.6), 'q34': (-1, -1.2, 0.3)}.items():
    cam.location = c + (R @ Vector(d)).normalized() * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(argv[1], f'{argv[2]}_{n}.png'); bpy.ops.render.render(write_still=True)
