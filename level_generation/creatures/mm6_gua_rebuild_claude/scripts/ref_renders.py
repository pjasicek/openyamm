"""MM9 reference renders for the Codex HD masters: textured bind pose, flat-lit, the pole hidden unless SHOW=pole (then only it).
POSE=action@frame renders a clip pose. Args: glb outdir prefix width height ortho [centre x,y,z]. The creature faces -Y."""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix, width, height, ortho = argv[0], argv[1], argv[2], int(argv[3]), int(argv[4]), float(argv[5])
centre = Vector([float(x) for x in argv[6].split(',')]) if len(argv) > 6 else None
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
show = os.environ.get('SHOW', 'guard')
for o in sc.objects:
    if o.name.startswith('Icosphere') or (o.type == 'MESH' and not o.name.startswith(show)):
        o.hide_render = True
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
print('BOUNDS', [round(min(p[i] for p in pts), 3) for i in range(3)], [round(max(p[i] for p in pts), 3) for i in range(3)])
c = centre or Vector([(min(p[i] for p in pts) + max(p[i] for p in pts)) / 2 for i in range(3)])
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = os.environ.get('LIGHT', 'FLAT'); sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = width; sc.render.resolution_y = height
w = bpy.data.worlds.new('w'); sc.world = w
w.color = (0.42, 0.42, 0.42)
sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': Vector((-1.0, -1.25, 0.35)), 'front': Vector((0, -1, 0.02)), 'left': Vector((1, 0, 0.02)),
        'back': Vector((0, 1, 0.02)), 'right': Vector((-1, 0, 0.02))}
for v, d in dirs.items():
    d = d.normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
print('REFS', prefix)
