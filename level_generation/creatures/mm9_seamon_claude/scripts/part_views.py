"""Renders aimed at a bone of a GLB at clip times (tail fins, eyes). Args: <glb> <outdir> <prefix> <shots> [size]
Shot = name:clip@seconds:bone:view:distance[:lens]; clip '-' = bind. Views in world axes (the creature faces -Y):
side (from -X), sidel (+X), top, below, front (-Y), back (+Y), q (above-left-behind). Workbench, studio light,
textured, backface culling on; LOD0 only."""
import bpy, sys, os, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix, shots = argv[0], argv[1], argv[2], argv[3].split(',')
size = int(argv[4]) if len(argv) > 4 else 700
os.makedirs(outdir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
for o in sc.objects:
    if o.type == 'MESH' and ('LOD' in o.name and 'LOD0' not in o.name or o.name.startswith('Icosphere')):
        o.hide_render = True
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = size
sc.render.image_settings.file_format = 'PNG'
cd = bpy.data.cameras.new('cam'); cd.clip_start = 0.01
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
fps = sc.render.fps / sc.render.fps_base
D = {'side': (-1, 0, 0.05), 'sidel': (1, 0, 0.05), 'top': (0, 0.001, 1), 'below': (0, 0.001, -1), 'front': (0, -1, 0.1),
     'back': (0, 1, 0.15), 'q': (0.8, 0.5, 0.6), 'qb': (-0.7, 0.3, -0.6)}
for shot in shots:
    parts = shot.split(':')
    name, pose, bone, view, dist = parts[:5]
    lens = float(parts[5]) if len(parts) > 5 else 35
    clip, t = pose.split('@')
    arm.animation_data_create()
    if clip == '-':
        arm.animation_data.action = None
        for pb in arm.pose.bones:
            pb.matrix_basis.identity()
        sc.frame_set(0)
    else:
        act = bpy.data.actions[clip]
        arm.animation_data.action = act
        try:
            arm.animation_data.action_slot = act.slots[0]
        except Exception:
            pass
        f = float(t) * fps
        sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
    bpy.context.view_layer.update()
    target = arm.matrix_world @ arm.pose.bones[bone].head
    d = Vector(D[view]).normalized()
    cd.lens = lens
    cam.location = target + d * float(dist)
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{name}.png')
    bpy.ops.render.render(write_still=True)
print('PART VIEWS', prefix, len(shots))
