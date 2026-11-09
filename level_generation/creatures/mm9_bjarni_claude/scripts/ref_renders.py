"""MM9 reference renders for the Codex HD masters (from mm9_dagrell_claude): textured model on flat grey, views q34
(front three-quarter from the creature's RIGHT, slightly above), front, left, back, right, top; the creature faces -Y.
POSE=action@frame renders a clip pose. HIDE_MAT=<material index> removes that material's faces (the scimitar).
CENTER=x,y,z fixes the view centre. Args: glb outdir prefix size ortho"""
import bpy, sys, math, os, bmesh
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix, size, ortho = argv[0], argv[1], argv[2], int(argv[3]), float(argv[4])
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
for o in sc.objects:
    if o.name.startswith('Icosphere') or (os.environ.get('HIDE_WEAPONS') and o.type == 'MESH' and o.name.split('.')[0] in ('ShortSword', 'dagger')):
        o.hide_render = True
arm = next((o for o in sc.objects if o.type == 'ARMATURE'), None)
if arm and arm.animation_data:
    arm.animation_data.action = None
for pb in (arm.pose.bones if arm else []):
    pb.matrix_basis.identity()
if os.environ.get('HIDE_MAT'):
    hide = int(os.environ['HIDE_MAT'])
    for o in sc.objects:
        if o.type != 'MESH':
            continue
        names = [m.name for m in o.data.materials]
        print('MATS', o.name, names)
        if any(n.endswith('_' + str(hide)) or n.endswith(str(hide)) for n in names):
            o.hide_render = True
if os.environ.get('POSE'):
    name, frame = os.environ['POSE'].split('@')
    act = bpy.data.actions[name]
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    sc.frame_set(int(float(frame)))
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for o in sc.objects:
    if o.type == 'MESH' and not o.hide_render:
        me = o.evaluated_get(dg).to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        o.evaluated_get(dg).to_mesh_clear()
print('BOUNDS', [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)])
c = Vector([(min(p[i] for p in pts) + max(p[i] for p in pts)) / 2 for i in range(3)])
if os.environ.get('CENTER'):
    c = Vector([float(x) for x in os.environ['CENTER'].split(',')])
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = os.environ.get('LIGHT', 'FLAT'); sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
sc.render.film_transparent = False
w = bpy.data.worlds.new('w'); sc.world = w
w.color = (0.42, 0.42, 0.42)
sc.display.shading.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': Vector((-1.0, -1.25, 0.55)), 'front': Vector((0, -1, 0.08)), 'left': Vector((1, 0, 0.08)),
        'back': Vector((0, 1, 0.08)), 'right': Vector((-1, 0, 0.08)), 'top': Vector((0, 0.0001, 1))}
if os.environ.get('VIEWS'):
    dirs = {k: v for k, v in dirs.items() if k in os.environ['VIEWS'].split(',')}
for v, d in dirs.items():
    d = d.normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
print('REFS', prefix)
