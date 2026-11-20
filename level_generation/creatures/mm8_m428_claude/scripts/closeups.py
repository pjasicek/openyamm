"""Textured close-ups of the textured master in rest pose (Workbench, texture colour, studio light): face front and
three-quarter, both hands, bodice and skirt front. Args: -- <blend> <out prefix>"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = False
sh.background_type = 'VIEWPORT'; sh.background_color = (0.5, 0.5, 0.5)
sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
shots = {'face': ((0, -2, 1.6), 0, 0.32), 'face34': ((1.2, -1.6, 1.6), 37, 0.32), 'handR': ((-0.31, -2, 0.88), 0, 0.3),
         'handL': ((0.31, -2, 0.88), 0, 0.3), 'bodice': ((0, -2, 1.2), 0, 0.5), 'skirt': ((0, -2, 0.55), 0, 1.1),
         'back': ((0, 2, 1.0), 180, 1.75)}
for name, (loc, yaw, scale) in shots.items():
    cam.location = loc; cam.rotation_euler = (math.radians(90), 0, math.radians(yaw)); cd.ortho_scale = scale
    sc.render.filepath = f'{out}_{name}.png'; bpy.ops.render.render(write_still=True)
