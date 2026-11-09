"""Solid/texture renders of every visible mesh of a blend or GLB. Args: <src> <out prefix> <cx,cy,cz> <ortho>
<views comma> [size] [color SINGLE|TEXTURE|VERTEX|MATERIAL] [action@frame]"""
import bpy, sys, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
src, out, c, ortho, views = argv[0], argv[1], Vector([float(x) for x in argv[2].split(',')]), float(argv[3]), argv[4].split(',')
size = int(argv[5]) if len(argv) > 5 else 512
color = argv[6] if len(argv) > 6 else 'SINGLE'
pose = argv[7] if len(argv) > 7 else None
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
for o in sc.objects:
    if o.name.startswith('Icosphere') or (o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name)):
        o.hide_render = True
if pose:
    act, fr = pose.split('@')
    arm = next(o for o in sc.objects if o.type == 'ARMATURE')
    arm.animation_data_create(); arm.animation_data.action = bpy.data.actions[act]
    try:
        arm.animation_data.action_slot = bpy.data.actions[act].slots[0]
    except Exception:
        pass
    f = float(fr); sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = color; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
sc.render.film_transparent = False
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.35, 0.38, 0.35)
sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
D = {'front': (0, -1, 0.02), 'left': (1, 0, 0.0), 'right': (-1, 0, 0.0), 'q34': (-1, -1.25, 0.55),
     'top': (0, 0.0001, 1), 'bottom': (0, 0.0001, -1), 'back': (0, 1, 0.02), 'q34b': (1, 1.2, 0.5),
     'q34l': (1, -1.25, 0.4), 'below34': (-1, -1, -0.6)}
for v in views:
    d = Vector(D[v]).normalized()
    cam.location = c + d * 10
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{v}.png'
    bpy.ops.render.render(write_still=True)
print('RENDERED', out)
