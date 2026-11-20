"""MM9 reference frames (textured Workbench) for the MM9-vs-ours sheets: Args: <rig blend> <outdir> <clip> <seconds,comma> <view> <size> <ortho> <cx,cy,cz>"""
import bpy, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
outdir, clip, secs, view, size, ortho, c = argv[1], argv[2], argv[3], argv[4], int(argv[5]), float(argv[6]), argv[7]
os.makedirs(outdir, exist_ok=True)
sc = bpy.context.scene
fps = sc.render.fps / sc.render.fps_base
arm = bpy.data.objects['MM9_Rig']
arm.animation_data_create()
if clip != '-':
    arm.animation_data.action = bpy.data.actions[clip]
    try:
        arm.animation_data.action_slot = bpy.data.actions[clip].slots[0]
    except Exception:
        pass
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = size
sc.render.film_transparent = True
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_end = 100
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
C = Vector([float(x) for x in c.split(',')])
d = Vector({'right': (-1, 0, 0.0), 'left': (1, 0, 0), 'front': (0, -1, 0), 'quarter': (-0.7, -1, 0.1), 'back': (0, 1, 0)}[view]).normalized()
cam.location = C + d * 10
cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
for s in secs.split(','):
    if clip != '-':
        f = float(s) * fps
        sc.frame_set(int(f), subframe=f - int(f))
    sc.render.filepath = os.path.join(outdir, f'{clip}_{s}_{view}.png')
    bpy.ops.render.render(write_still=True)
print('MM9FRAMES', fps, arm.animation_data.action.frame_range if arm.animation_data.action else None)
