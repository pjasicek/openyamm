"""Clay renders of chosen clip frames, four views each. Args: blend clip:frame[,clip:frame...] tag [scale]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, a[0]))
arm = bpy.data.objects['Guard_Rig']
scale = float(a[3]) if len(a) > 3 else 1.9
sc = bpy.context.scene
common.workbench_clay(sc)
sc.display.shading.color_type = 'SINGLE'
for item in a[1].split(','):
    clip, f = item.split(':')
    act = bpy.data.actions[clip]
    arm.animation_data.action = act
    if act.slots:
        arm.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(f))
    h = arm.matrix_world @ arm.pose.bones['Hips'].head
    common.render_views(os.path.join(common.REVIEW, a[2], f'{clip}_{int(f):02d}'), max(0.6, float(h.z) * 1.1), scale,
                        views=('front', 'three_quarter', 'right', 'back'), resolution=(400, 500),
                        target=(float(h.x), float(h.y)))
