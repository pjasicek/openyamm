"""Render poses of a rigged blend or GLB: one PNG per (clip, time, view).

Args: <blend|glb> <outdir> <clips comma> <times per clip> <views comma> [size] [ortho] [color: TEXTURE|VERTEX]
Times are evenly spaced over each clip (both ends included). Camera framing is fixed per view (centre 0,0,0.1).
"""
import bpy, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
src, outdir, clips, count, views = argv[:5]
size = int(argv[5]) if len(argv) > 5 else 320
ortho = float(argv[6]) if len(argv) > 6 else 2.2
color = argv[7] if len(argv) > 7 else 'TEXTURE'
os.makedirs(outdir, exist_ok=True)
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
for o in list(sc.objects):
    if o.type == 'MESH' and o.name.startswith('Icosphere'):
        o.hide_render = True
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError:
    pass
sh = sc.display.shading
sh.light = 'STUDIO'
sh.color_type = color
sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
sc.render.film_transparent = False
w = bpy.data.worlds.new('w')
sc.world = w
cd = bpy.data.cameras.new('cam')
cd.type = 'ORTHO'
cd.ortho_scale = ortho
cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd)
sc.collection.objects.link(cam)
sc.camera = cam
# floor reference at model z = 0 is not drawn; the sheet shows poses only
dirs = {'q34': Vector((-1.0, -1.25, 0.55)), 'front': Vector((0, -1, 0)), 'left': Vector((1, 0, 0)),
        'right': Vector((-1, 0, 0)), 'top': Vector((0, 0.0001, 1)), 'back': Vector((0, 1, 0))}
centre = Vector((0, 0, 0.1))
fps = sc.render.fps / sc.render.fps_base
for clip in clips.split(','):
    act = bpy.data.actions[clip]
    arm.animation_data_create()
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = act.frame_range
    n = int(count)
    for k in range(n):
        f = f0 + (f1 - f0) * k / max(1, n - 1)
        sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        for v in views.split(','):
            d = dirs[v].normalized()
            cam.location = centre + d * 10
            cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(outdir, f'{clip}_{v}_{k:02d}.png')
            bpy.ops.render.render(write_still=True)
print('POSES done')
