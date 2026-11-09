"""Workbench shots of 'Body' in a blend (rest pose or POSE=action@frame), solid studio light, optional wire-free.
Args: <blend> <out prefix> <size> <ortho> <cx,cy,cz> <view,...>  views: front back left right top bottom q34 q34l low"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
size, ortho = int(a[2]), float(a[3]); c = Vector([float(x) for x in a[4].split(',')])
for o in sc.objects:
    o.hide_render = not (o.type == 'MESH' and o.name == os.environ.get('MESH', 'Body'))
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = os.environ.get('COLOR', 'SINGLE'); sh.show_backface_culling = bool(os.environ.get('CULL'))
sh.single_color = (0.75, 0.72, 0.68)
if os.environ.get('ATTR'):
    # colour the faces where the named face attribute is 1 (head / hand sets) red
    b = bpy.data.objects[os.environ.get('MESH', 'Body')]; me = b.data
    m0 = bpy.data.materials.new('a0'); m0.diffuse_color = (0.75, 0.72, 0.68, 1)
    m1 = bpy.data.materials.new('a1'); m1.diffuse_color = (0.85, 0.25, 0.2, 1)
    me.materials.clear(); me.materials.append(m0); me.materials.append(m1)
    vals = [0] * len(me.polygons); me.attributes[os.environ['ATTR']].data.foreach_get('value', vals)
    for p, v in zip(me.polygons, vals):
        p.material_index = 1 if v else 0
    sh.color_type = 'MATERIAL'
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (1.0, 0.85, 0.0) if os.environ.get('CULL') else (0.3, 0.3, 0.3); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'front': (0, -1, 0.05), 'back': (0, 1, 0.05), 'left': (-1, 0, 0.05), 'right': (1, 0, 0.05), 'top': (0, -0.0001, 1),
        'bottom': (0, -0.0001, -1), 'q34': (-0.8, -1, 0.3), 'q34l': (0.8, -1, 0.3), 'low': (-0.5, -1, -0.45)}
for v in a[5].split(','):
    d = Vector(dirs[v]).normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{v}.png'; bpy.ops.render.render(write_still=True)
print('SHOT', a[1])
