"""Renders a clip at twice its key rate (the review viewer plays 48 fps, so half frames show interpolation glitches):
three-quarter and front views, centred on the hips. Env CLIP, LAST (viewer frame), SCALE. Args: blend tag."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
blend, tag = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
arm = bpy.data.objects['Mage_Rig']; act = bpy.data.actions[os.environ.get('CLIP', 'Attack')]; arm.animation_data.action = act
if act.slots: arm.animation_data.action_slot = act.slots[0]
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'SINGLE'
out = os.path.join(common.REVIEW, tag); os.makedirs(out, exist_ok=True)
f0, f1 = (int(round(x)) for x in act.frame_range)
for v in range(0, min(2 * f1, int(os.environ.get('LAST', 2 * f1))) + 1):
    sc.frame_set(v // 2, subframe=0.5 * (v % 2)); h = arm.matrix_world @ arm.pose.bones['mixamorig:Hips'].head
    common.render_views(os.path.join(out, f'v_{v:02d}'), 1.15, float(os.environ.get('SCALE', 1.6)), views=('three_quarter', 'front'),
                        resolution=(220, 280), target=(float(h.x), float(h.y)))
