"""MM9 reference renders for the Codex masters: textured bind pose on flat grey.
Args: glb outdir mode(body|head|trident) size ortho. Creature faces -Y. Views q34 front left back right."""
import bpy, sys, math, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, mode, size, ortho = argv[0], argv[1], argv[2], int(argv[3]), float(argv[4])
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
print('OBJECTS', [(o.name, o.type) for o in sc.objects if o.type != 'EMPTY'][:10])
for o in sc.objects:
    if o.name.startswith('Icosphere'):
        o.hide_render = True
    elif o.type == 'MESH':
        tri = 'trident' in o.name.lower() or any('trident' in (m.name or '').lower() for m in o.data.materials)
        o.hide_render = tri if mode != 'trident' else not tri
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for o in sc.objects:
    if o.type == 'MESH' and not o.hide_render:
        me = o.evaluated_get(dg).to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        o.evaluated_get(dg).to_mesh_clear()
lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
print('BOUNDS', lo, hi)
c = Vector([(lo[i] + hi[i]) / 2 for i in range(3)])
if mode == 'head':
    c = Vector((0, min(p[1] for p in pts if p[2] > hi[2] - 0.3) + 0.15, hi[2] - 0.17))
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42)
sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': Vector((-1.0, -1.25, 0.45)), 'front': Vector((0, -1, 0.05)), 'left': Vector((1, 0, 0.05)),
        'back': Vector((0, 1, 0.05)), 'right': Vector((-1, 0, 0.05))}
for v, d in dirs.items():
    d = d.normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{mode}_{v}.png')
    bpy.ops.render.render(write_still=True)
