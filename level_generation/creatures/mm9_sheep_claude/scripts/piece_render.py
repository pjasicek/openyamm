"""Render the head with the separate pieces of 'Body' in red. Args: <blend> <outdir>"""
import bpy, bmesh, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc = bpy.context.scene
o = bpy.data.objects['Body']
for x in bpy.data.objects:
    if x.type == 'MESH' and x != o:
        x.hide_render = True
piece = o.data.attributes['piece']
red = bpy.data.materials.new('r'); red.diffuse_color = (1, .1, .1, 1)
grey = bpy.data.materials.new('g'); grey.diffuse_color = (.8, .8, .8, 1)
o.data.materials.clear(); o.data.materials.append(grey); o.data.materials.append(red)
for p in o.data.polygons:
    p.material_index = 1 if piece.data[p.vertices[0]].value == 2 else 0
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = 500
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.45
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((0, -0.55, 0.85))
for n, d in {'front': (0, -1, 0), 'left': (1, 0, 0), 'top': (0, 0.0001, 1), 'q34': (-1, -1.25, 0.55)}.items():
    cam.location = c + Vector(d).normalized() * 5
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(argv[1], f'pc_{n}.png'); bpy.ops.render.render(write_still=True)
