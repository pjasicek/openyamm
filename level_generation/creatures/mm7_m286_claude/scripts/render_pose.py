"""Clay render of the rig's Body at one clip frame (review): review/<tag>_<view>.png. Optional ZOOM=cx,cz,height for
a close-up target (metres). Args: -- <blend> <clip> <frame> <tag> [views comma list]"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, clip, frame, tag = a[:4]
views = tuple(a[4].split(',')) if len(a) > 4 else ('front', 'left')
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data_create()
act = bpy.data.actions[clip]; rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(frame))
for p in body.data.polygons:
    p.use_smooth = True
sc = bpy.context.scene; common.workbench_clay(sc)
z = os.environ.get('ZOOM')
if z:
    cx, cz, h = (float(x) for x in z.split(','))
    common.render_views(os.path.join(common.REVIEW, tag), cz, h, views=views, resolution=(700, 700), target=(cx, 0.0))
else:
    common.render_views(os.path.join(common.REVIEW, tag), 1.05, 2.3, views=views, resolution=(600, 900))
