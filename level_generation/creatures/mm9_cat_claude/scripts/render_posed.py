"""Render a fit/sym blend with the posed armature: Body grey and the posed MM9 mesh in one view (bones checked by eye).
Args: <blend> <outdir> <prefix> <views comma> <size> <ortho> <cx,cy,cz> [hide mesh name]"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
blend, outdir, prefix, views, size, ortho, cen = argv[:7]
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name.startswith('Icosphere'):
        o.hide_render = True
    if len(argv) > 7 and o.name == argv[7]:
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_xray = len(argv) <= 7; sh.xray_alpha = 0.5
sc.render.resolution_x = sc.render.resolution_y = int(size)
w = bpy.data.worlds.new('w'); sc.world = w; sc.display.shading.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float(ortho); cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector([float(x) for x in cen.split(',')])
dirs = {'q34': Vector((-1, -1.25, .55)), 'front': Vector((0, -1, 0)), 'left': Vector((1, 0, 0)), 'back': Vector((0, 1, 0))}
for v in views.split(','):
    d = dirs[v].normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
print('POSED done')
