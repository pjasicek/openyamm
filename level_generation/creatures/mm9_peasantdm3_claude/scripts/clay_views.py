"""Clay silhouette renders of a .blend (mesh objects, bind pose) or a converted MM9 .glb at a fixed camera, for overlays.
Args: <in .blend|.glb> <outdir> <prefix> <size> <ortho> <cx,cy,cz> [views=front,left,q34,back]
Writes <prefix>_<view>.png (Workbench, studio light, single colour, transparent film)."""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
src, outdir, prefix, size, ortho = argv[0], argv[1], argv[2], int(argv[3]), float(argv[4])
c = Vector([float(x) for x in argv[5].split(',')])
views = (argv[6] if len(argv) > 6 else 'front,left,q34,back').split(',')
os.makedirs(outdir, exist_ok=True)
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
for o in sc.objects:
    if o.type == 'ARMATURE':
        if o.animation_data: o.animation_data.action = None
        for pb in o.pose.bones: pb.matrix_basis.identity()
    if o.type == 'MESH' and o.name.startswith('Icosphere'): o.hide_render = True
bpy.context.view_layer.update()
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = os.environ.get('COLOR', 'SINGLE'); sh.single_color = (0.75, 0.72, 0.68)
sh.show_backface_culling = bool(os.environ.get('CULL'))
sc.render.resolution_x = sc.render.resolution_y = size
sc.render.film_transparent = True
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': Vector((-1.0, -1.25, 0.3)), 'front': Vector((0, -1, 0)), 'left': Vector((1, 0, 0)), 'right': Vector((-1, 0, 0)),
        'back': Vector((0, 1, 0)), 'low': Vector((-0.6, -1, -0.5)), 'top': Vector((0, -0.3, 1))}
for v in views:
    d = dirs[v].normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
print('CLAY', prefix, views)
