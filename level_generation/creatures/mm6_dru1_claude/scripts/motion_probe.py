"""Motion measurements on a rig blend (review round 1):
- PELVIS per clip: roll (about forward), yaw and lateral (x) sway ranges of B_Pelvis in world space;
- CLOAKJERK per clip: per cloak chain point (bone heads and tails of the Cloak_* bones) the second difference of its
  world position per frame (m/frame^2): p95 and max, the worst chain/frame; and the frame-to-frame direction flips of
  the hem velocity (sign changes of the velocity along its mean direction) as an 'erratic' count.
Args: -- <blend> clip [clip ...]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']
cloak = [b.name for b in rig.data.bones if b.name.startswith('Cloak_')]
PEL_FWD = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
PEL_UP = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((0, 0, 1))
for clip in a[1:]:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    roll, yaw, xs, P, P_extra = [], [], [], [], []
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        M = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix
        up = (M.to_3x3() @ PEL_UP).normalized(); fw = (M.to_3x3() @ PEL_FWD).normalized()
        roll.append(math.degrees(math.atan2(up.x, up.z))); yaw.append(math.degrees(math.atan2(fw.x, -fw.y)))
        xs.append(M.translation.x)
        P_extra.append([(rig.matrix_world @ rig.pose.bones[n].head).x for n in ('B_Spine2', 'B_Head')])
        P.append([tuple(rig.matrix_world @ rig.pose.bones[n].tail) for n in cloak])
    P = np.array(P)
    print(f'PELVIS {clip}: roll {min(roll):+.1f}..{max(roll):+.1f} deg, yaw {min(yaw):+.1f}..{max(yaw):+.1f} deg, '
          f'x sway {100 * (max(xs) - min(xs)):.1f} cm; chest x {100 * np.ptp(np.array(P_extra)[:, 0]):.1f} cm, head x {100 * np.ptp(np.array(P_extra)[:, 1]):.1f} cm')
    if len(P) > 2:
        acc = np.linalg.norm(P[2:] - 2 * P[1:-1] + P[:-2], axis=2)
        k = np.unravel_index(np.argmax(acc), acc.shape)
        v = np.diff(P, axis=0); flips = 0
        for c in range(P.shape[1]):
            vv = v[:, c]; s = np.sign(vv @ vv.mean(0)) if np.linalg.norm(vv.mean(0)) > 1e-6 else np.sign(vv[:, 0])
            flips += int((np.diff(s) != 0).sum())
        print(f'CLOAKJERK {clip}: p95 {np.percentile(acc, 95) * 100:.2f} cm/f2, max {acc.max() * 100:.2f} at frame {k[0] + 1} '
              f'{cloak[k[1]]}; velocity sign flips per point {flips / P.shape[1]:.1f}')
