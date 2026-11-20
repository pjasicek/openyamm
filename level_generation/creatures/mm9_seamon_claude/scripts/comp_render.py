"""Render a GLB's connected components in random colours (separate by loose parts, workbench RANDOM).
Args: glb outdir prefix views(comma) [size] [ortho]"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix, views = argv[0], argv[1], argv[2], argv[3].split(',')
size = int(argv[4]) if len(argv) > 4 else 640
ortho = float(argv[5]) if len(argv) > 5 else 1.2
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
meshes = [o for o in sc.objects if o.type == 'MESH']
for o in meshes:
    bpy.context.view_layer.objects.active = o
    for x in sc.objects:
        x.select_set(x == o)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=1e-5)
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')
pts = [o.matrix_world @ v.co for o in sc.objects if o.type == 'MESH' for v in o.data.vertices]
c = Vector([(min(p[i] for p in pts) + max(p[i] for p in pts)) / 2 for i in range(3)])
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'RANDOM'
sc.render.resolution_x = sc.render.resolution_y = size
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': Vector((-1.0, -1.25, 0.55)), 'front': Vector((0, -1, 0)), 'left': Vector((1, 0, 0)),
        'top': Vector((0, 0.0001, 1)), 'bottom': Vector((0, 0.0001, -1))}
for v in views:
    d = dirs[v].normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
print('COMPS', len([o for o in sc.objects if o.type == 'MESH']))
