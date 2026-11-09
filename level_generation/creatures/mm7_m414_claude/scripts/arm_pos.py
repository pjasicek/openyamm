"""Probe: arm joint positions in the chest (B_Spine2 bone) frame per listed frame. Args: -- <blend> <action> <f,f,...>"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
act = bpy.data.actions[a[1]]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
fr = [int(x) for x in a[2].split(',')]
W = lambda n, t='head': rig.matrix_world @ getattr(rig.pose.bones[n], t)
for f in fr:
    sc.frame_set(f)
    P = rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix
    inv = P.inverted()
    def loc(v): v = inv @ v; return '(%+.2f %+.2f %+.2f)' % tuple(v)
    print('POS f%d chest-frame: Rsh %s Rel %s Rwr %s | Lsh %s Lel %s Lwr %s' % (f, loc(W('B_R_UpperArm')), loc(W('B_R_Forearm')), loc(W('B_R_Hand')), loc(W('B_L_UpperArm')), loc(W('B_L_Forearm')), loc(W('B_L_Hand'))))
import math
if 'Spear' in rig.pose.bones:
    for f in fr:
        sc.frame_set(f)
        M = rig.matrix_world @ rig.pose.bones['Spear'].matrix; y = M.to_3x3().col[1].normalized()
        ch = (rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix).to_3x3().col[2]
        print('POS f%d spear dir world (%+.2f %+.2f %+.2f) yaw from -Y %.0f deg, pitch %.0f; chest lateral axis yaw %.0f; grip at (%+.2f %+.2f %+.2f)' % (
            f, *y, math.degrees(math.atan2(y.x, -y.y)), math.degrees(math.asin(y.z)), math.degrees(math.atan2(-ch.y, ch.x)), *M.translation))
for f in fr:
    sc.frame_set(f)
    print('POS f%d world: Rwr (%+.3f %+.3f %+.3f) Lwr (%+.3f %+.3f %+.3f)' % (f, *W('B_R_Hand'), *W('B_L_Hand')))
