"""MM9 clip strips: every clip, N frames, Blender workbench, one sheet per group. Args: glb out_prefix frames view size"""
import bpy, sys, os, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, out, N, view, size = argv[0], argv[1], int(argv[2]), argv[3], int(argv[4])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = os.environ.get('LIGHT', 'FLAT'); sh.color_type = os.environ.get('COL', 'TEXTURE'); sh.single_color = (.72, .68, .6); sh.show_cavity = os.environ.get('LIGHT') == 'STUDIO'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = size
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42); sc.display.shading.background_type = 'WORLD'
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = float(os.environ.get('ORTHO', '2.5')); cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'q34': (1.0, -1.25, 0.35), 'side': (1, 0, 0.05), 'front': (0, -1, 0.05), 'rq': (-1, -1.25, 0.35)}
d = Vector(dirs[view]).normalized()
c = Vector((0, 0, float(os.environ.get('CZ', '0'))))
cam.location = c + d * 10; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.fps = 30
ONLY = os.environ.get('CLIPS'); ONLY = ONLY.split(',') if ONLY else None
for a in sorted(bpy.data.actions, key=lambda x: x.name):
    if ONLY and a.name not in ONLY: continue
    arm.animation_data.action = a
    try: arm.animation_data.action_slot = a.slots[0]
    except Exception: pass
    f0, f1 = a.frame_range
    for i in range(N):
        f = f0 + (f1 - f0) * i / max(1, N - 1)
        sc.frame_set(int(f), subframe=f - int(f))
        sc.render.filepath = f"{out}/{a.name}_{i:02d}.png"
        bpy.ops.render.render(write_still=True)
print('STRIPS done', [a.name for a in bpy.data.actions][:3])
