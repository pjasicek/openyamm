"""Renders the head with the jaw opened by a test angle about the jaw pivot's lateral axis (rest pose otherwise).
Args: blend outdir prefix angle_deg ortho cx,cy,cz views"""
import bpy, sys, os, math
from mathutils import Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rigcfg
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
outdir, prefix, ang, ortho, c, views = argv[1], argv[2], float(argv[3]), float(argv[4]), argv[5], argv[6].split(',')
os.makedirs(outdir, exist_ok=True)
arm = bpy.data.objects['MM9_Rig']
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
pb = arm.pose.bones[rigcfg.JAW_BONES[0]]
axis = pb.bone.matrix_local.inverted().to_3x3() @ Vector((1, 0, 0))
pb.rotation_mode = 'QUATERNION'
pb.rotation_quaternion = Quaternion(axis.normalized(), math.radians(ang))
bpy.context.view_layer.update()
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.show_backface_culling = os.environ.get('CULL', '1') == '1'
sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
C = Vector([float(x) for x in c.split(',')])
dirs = {'q34': (-1, -1.25, 0.2), 'right': (-1, 0, 0), 'front': (0, -1, 0), 'below': (-0.5, -1, -0.7)}
for v in views:
    d = Vector(dirs[v]).normalized()
    cam.location = C + d * 10
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
