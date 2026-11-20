"""MM9 clip strips, Blender workbench renders of the raw (mirrored) conversion. Args: glb outdir clip1,clip2,... N (frames per clip) size ortho views(q34,front,...)"""
import bpy, sys, os, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, clips, N, size, ortho, views = argv[0], argv[1], argv[2].split(','), int(argv[3]), int(argv[4]), float(argv[5]), argv[6].split(',')
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
arm.animation_data_create()
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = os.environ.get('COLOR', 'TEXTURE'); sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': Vector((-1.0, -1.25, 0.4)), 'front': Vector((0, -1, 0.08)), 'left': Vector((1, 0, 0.08)), 'back': Vector((0, 1, 0.08)), 'right': Vector((-1, 0, 0.08)), 'qback': Vector((1, 1.25, 0.4))}
print('ACTIONS', [a.name for a in bpy.data.actions])
for cl in clips:
    act = next(a for a in bpy.data.actions if a.name == cl or a.name.startswith(cl + '_') or a.name.split('|')[-1] == cl)
    arm.animation_data.action = act
    try:
        arm.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = act.frame_range
    for k in range(N):
        fr = f0 + (f1 - f0) * k / max(N - 1, 1)
        sc.frame_set(int(fr), subframe=fr - int(fr))
        c = (arm.matrix_world @ arm.pose.bones['Bip01 Pelvis'].head)
        for v in views:
            d = dirs[v].normalized()
            cam.location = c + d * 10
            cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(outdir, f'{cl}_{k:02d}_{v}.png')
            bpy.ops.render.render(write_still=True)
print('STRIPS DONE')
