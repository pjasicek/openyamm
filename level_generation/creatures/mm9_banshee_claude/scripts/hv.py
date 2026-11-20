"""Workbench views of named objects of a blend. Args: blend out ortho cx,cy,cz names(comma) views(comma) [wire]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
names = a[4].split(',')
for o in sc.objects:
    if o.type == 'MESH':
        o.hide_render = o.name not in names
        for m in list(o.modifiers):
            if m.type != 'ARMATURE':
                o.modifiers.remove(m)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.75, .72, .68); sh.show_backface_culling = False; sh.show_cavity = True; sh.cavity_type = 'WORLD'
if len(a) > 6:
    for o in sc.objects:
        if o.type == 'MESH' and not o.hide_render:
            m = o.modifiers.new('w', 'WIREFRAME'); m.thickness = 0.0008; m.use_replace = False; m.use_even_offset = False
sc.render.resolution_x = 900; sc.render.resolution_y = 900
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[2]); cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in a[3].split(',')])
D = {'front': (0, -1, .02), 'left': (1, 0, .02), 'right': (-1, 0, .02), 'back': (0, 1, .02), 'q34': (-1, -1.25, .35), 'q34l': (1, -1.25, .15), 'below': (0, -.25, -1), 'top': (0, -.25, 1), 'hand': (.6, -.3, .75), 'palm': (.3, -.2, -1)}
for n in a[5].split(','):
    d = Vector(D[n]).normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{n}.png'; bpy.ops.render.render(write_still=True)
