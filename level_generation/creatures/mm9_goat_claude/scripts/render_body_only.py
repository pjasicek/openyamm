"""Solid render of object 'Body' only from a blend or of the glb mesh. Args: src outdir prefix views size ortho cx,cy,cz"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
src, outdir, prefix, views, size, ortho, c = argv
os.makedirs(outdir, exist_ok=True)
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'MESH' and o.name != 'Body' and src.endswith('.blend'):
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
sc.render.resolution_x = sc.render.resolution_y = int(size)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(ortho); cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
C = Vector([float(x) for x in c.split(',')])
dirs = {'q34': (-1, -1.25, 0.55), 'right': (-1, 0, 0), 'top': (0, 0.0001, 1), 'back': (0, 1, 0), 'q34br': (-1, 1.25, 0.4)}
for v in views.split(','):
    d = Vector(dirs[v]).normalized()
    cam.location = C + d * 10
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
