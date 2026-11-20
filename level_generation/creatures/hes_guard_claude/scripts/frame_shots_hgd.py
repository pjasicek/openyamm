"""Clay close-ups of given clip frames from several views (rig file, rifle included).
Args: -- <blend> <out prefix> <clip> <frame,...> <views> [cz ch]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out, clip, frames, views = a[1], a[2], [float(x) for x in a[3].split(',')], a[4].split(',')
cz, ch = (float(a[5]), float(a[6])) if len(a) > 6 else (1.2, 1.0)
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; common.workbench_clay(sc)
act = bpy.data.actions[clip]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
import math
from mathutils import Vector
for f in frames:
    sc.frame_set(int(f), subframe=f - int(f))
    tgt = (0.0, 0.0)
    if os.environ.get('FOCUS_RIFLE'):                     # centre on the rifle's grip
        g = rig.matrix_world @ rig.pose.bones['Rifle'].matrix
        tgt = (g.translation.x, g.translation.y); cz = g.translation.z
    side = [v for v in views if v != 'top']
    if side:
        common.render_views(f'{out}_{clip}_{f:g}', cz, ch, views=tuple(side), resolution=(420, 420), target=tgt)
    if 'top' in views:                                    # straight down from above
        cam = common.ortho_camera('cam_top', (tgt[0], tgt[1], cz + 4.0), (0, 0, 0), ch)
        sc.camera = cam; sc.render.resolution_x = sc.render.resolution_y = 420
        sc.render.filepath = f'{out}_{clip}_{f:g}_top.png'; bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam, do_unlink=True)
