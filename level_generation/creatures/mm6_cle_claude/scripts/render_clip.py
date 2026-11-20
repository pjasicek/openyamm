"""Clay renders of one clip (env CLIP, default Attack) every 2nd frame over its frame range: front, left and
three-quarter, centred on the hips (env SCALE: ortho height, default 2.4). Args: blend tag."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
blend, tag = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
arm = bpy.data.objects['Cleric_Rig']; act = bpy.data.actions[os.environ.get('CLIP', 'Attack')]; arm.animation_data.action = act
if act.slots: arm.animation_data.action_slot = act.slots[0]
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'SINGLE'
out = os.path.join(common.REVIEW, tag); os.makedirs(out, exist_ok=True)
f0, f1 = (int(round(x)) for x in act.frame_range)
f1 = min(f1, int(os.environ.get('LAST', f1)))
for f in range(f0, f1 + 1, int(os.environ.get('STEP', 2))):
    sc.frame_set(f); h = arm.matrix_world @ arm.pose.bones['Hips'].head
    common.render_views(os.path.join(out, f'f_{f:02d}'), max(0.6, float(h.z) * 1.05), float(os.environ.get('SCALE', 2.4)),
                        views=('front', 'left', 'three_quarter'), resolution=(260, 340), target=(float(h.x), float(h.y)))
