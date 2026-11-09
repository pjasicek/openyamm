"""Eevee-free check of work/build.blend: Workbench material colours with the base texture: front, eye close-up,
below and sensor. Args: -- <out prefix>"""
import bpy, os, sys
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cust_common as cc
prefix = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=cc.path('work/build.blend'))
for m, c in (('Cust_Glow', (1.0, 0.55, 0.1, 1)), ('Cust_Lens', (0.6, 0.85, 1.0, 1))):
    bpy.data.materials[m].diffuse_color = c
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'FLAT'; sc.display.shading.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 700
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
for k, (d, c, s) in {'front': (Vector((-0.3, -1, 0.1)), Vector((0, 0, 1.7)), 4.0), 'eye': (Vector((-0.25, -1, 0.05)), Vector((0, -1.1, 1.9)), 1.0),
                     'below': (Vector((0, -0.35, -1)), Vector((0, -0.2, 0.7)), 3.2), 'sensor': (Vector((-0.4, -1, 0.3)), Vector((0, -0.2, 3.1)), 0.8)}.items():
    cam.data.ortho_scale = s; d = d.normalized(); cam.location = c + d * 10; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = cc.path(f'{prefix}_{k}.png'); bpy.ops.render.render(write_still=True)
