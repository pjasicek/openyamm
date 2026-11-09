"""Colour 'Body' by its 'chain' attribute and render views. Args: <blend> <outdir> <prefix> <views> <size> <ortho> [cx,cy,cz]"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
outdir, prefix, views, size, ortho = argv[1], argv[2], argv[3].split(','), int(argv[4]), float(argv[5])
c = Vector([float(x) for x in argv[6].split(',')]) if len(argv) > 6 else Vector((0, 0, 1.4))
pal = [(1, .2, .2), (.2, 1, .2), (.2, .4, 1), (1, 1, .2), (1, .2, 1), (.2, 1, 1), (1, .6, .2), (.6, .2, 1)]
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != 'Body':
        o.hide_render = True
me = bpy.data.objects['Body'].data
ch = me.attributes['chain'].data
col = me.color_attributes.new('dbg', 'FLOAT_COLOR', 'POINT')
for i in range(len(me.vertices)):
    k = ch[i].value
    col.data[i].color = (*(pal[k % len(pal)] if k >= 0 else (.8, .8, .8)), 1)
me.color_attributes.active_color = col
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.color_type = 'VERTEX'; sc.display.shading.light = 'STUDIO'
sc.render.resolution_x = sc.render.resolution_y = size
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'front': (0, -1, 0), 'left': (1, 0, 0), 'top': (0, 0.0001, 1), 'q34': (-1, -1.25, 0.55), 'right': (-1, 0, 0)}
os.makedirs(outdir, exist_ok=True)
for v in views:
    d = Vector(dirs[v]).normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
