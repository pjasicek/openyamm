"""MM9 renders of pieces only. ONLY=substring list (comma), or NOT=... Args: glb out prefix size ortho"""
import bpy, sys, math, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix, size, ortho = argv[0], argv[1], argv[2], int(argv[3]), float(argv[4])
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
only = os.environ.get('ONLY')
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
for o in sc.objects:
    if o.type == 'MESH':
        print('MESH', o.name, len(o.data.polygons))
        o.hide_render = not (only is None or any(s in o.name for s in only.split(',')))
if os.environ.get('POSE'):
    name, frame = os.environ['POSE'].split('@')
    act = bpy.data.actions[name]; arm.animation_data.action = act
    try: arm.animation_data.action_slot = act.slots[0]
    except Exception: pass
    sc.frame_set(int(float(frame)))
bpy.context.view_layer.update()
c = Vector([float(x) for x in os.environ.get('CENTER', '-0.06,0,0.85').split(',')])
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'FLAT' if os.environ.get('FLAT') else 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42); sc.display.shading.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': Vector((-1.0, -1.25, 0.25)), 'front': Vector((0, -1, 0.04)), 'left': Vector((1, 0, 0.04)), 'back': Vector((0, 1, 0.04)), 'right': Vector((-1, 0, 0.04))}
for v, d in dirs.items():
    d = d.normalized(); cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
