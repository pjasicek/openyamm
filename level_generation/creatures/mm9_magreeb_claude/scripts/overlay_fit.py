"""Fit check: renders the fitted 'Body' (coloured by chain, core grey) beside the MM9 meshes, views front/left/top.
Args: <fit blend> <out png prefix> [ortho] [cz]"""
import bpy, sys, colorsys
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
OUT = argv[1]
ortho = float(argv[2]) if len(argv) > 2 else 3.6
cz = float(argv[3]) if len(argv) > 3 else 0.3
sc = bpy.context.scene
body = bpy.data.objects['Body']
me = body.data
ch = me.attributes['chain']
pc = me.attributes['piece']
col = me.color_attributes.new('vc', 'FLOAT_COLOR', 'POINT')
for v in me.vertices:
    k = ch.data[v.index].value
    rgb = (0.75, 0.75, 0.75) if k < 0 else colorsys.hsv_to_rgb((k * 0.618) % 1, 0.75, 0.95)
    if pc.data[v.index].value == 3:
        rgb = (0.3, 0.4, 0.9)
    col.data[v.index].color = (*rgb, 1)
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading
sh.light = 'STUDIO'
sc.render.resolution_x = 640; sc.render.resolution_y = 640
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
mm9 = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Body']
c = Vector((0, 0, cz))
for which in ('mm9', 'fit'):
    for o in mm9:
        o.hide_render = which != 'mm9'
    body.hide_render = which != 'fit'
    sh.color_type = 'TEXTURE' if which == 'mm9' else 'VERTEX'
    for name, d in {'front': Vector((0, -1, 0)), 'left': Vector((1, 0, 0)), 'top': Vector((0, 0.0001, 1))}.items():
        cam.location = c + d * 10
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{OUT}_{which}_{name}.png'
        bpy.ops.render.render(write_still=True)
