"""Larger clay renders of chosen frames of a clip. env CLIP, FRAMES (comma list), VIEWS (comma list), RES (w,h),
SCALE. Args: blend tag -> review/<tag>/fNN_<view>.png; sheet_views.py composes review/<tag>_sheet.png."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
blend, tag = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
arm = bpy.data.objects['Thief_Rig']; act = bpy.data.actions[os.environ.get('CLIP', 'Walking')]
arm.animation_data.action = act
if act.slots: arm.animation_data.action_slot = act.slots[0]
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'SINGLE'
frames = [int(x) for x in os.environ.get('FRAMES', '0,4,8,12,16,20,24').split(',')]
views = os.environ.get('VIEWS', 'left,back,front').split(',')
W, H = (int(x) for x in os.environ.get('RES', '360,520').split(','))
d = os.path.join(common.REVIEW, tag); os.makedirs(d, exist_ok=True)
for i, f in enumerate(frames):
    sc.frame_set(f); h = arm.matrix_world @ arm.pose.bones['Hips'].head
    for j, v in enumerate(views):
        common.render_views(os.path.join(d, f'f{f:02d}'), max(0.75, float(h.z)), float(os.environ.get('SCALE', 1.9)),
                                views=(v,), resolution=(W, H), target=(float(h.x), float(h.y)))[0]
