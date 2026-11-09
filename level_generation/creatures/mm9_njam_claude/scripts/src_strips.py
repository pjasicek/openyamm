"""Frame strips of the MM9 source clips (diagnosis only): for each clip, N evenly spaced frames, one view per row.
Args: glb outdir size ortho view clip1,clip2,...  (view: front|left|q34)"""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, size, ortho, view, clips = a[0], a[1], int(a[2]), float(a[3]), a[4], a[5].split(',')
N = int(os.environ.get('N', 6))
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
d = {'front': Vector((0, -1, 0.08)), 'left': Vector((1, 0, 0.08)), 'q34': Vector((-1, -1.25, 0.4))}[view].normalized()
c = Vector((0, 0, float(os.environ.get('CZ', 0.0))))
cam.location = c + d * 10
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.fps = 30
for name in clips:
    act = bpy.data.actions.get(name)
    if act is None:
        print('MISSING', name); continue
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = act.frame_range
    for i in range(N):
        f = f0 + (f1 - f0) * i / max(1, N - 1)
        sc.frame_set(int(f), subframe=f - int(f))
        sc.render.filepath = os.path.join(outdir, f'{name}_{i}.png')
        bpy.ops.render.render(write_still=True)
    print('STRIP', name, f0, f1)
