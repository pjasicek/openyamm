"""Sword-tip speed per half frame of one action on the gated master (grip_pose.json handle axis, tip at +0.85 m), to
locate jerks/whips. Args: -- <blend> <action>"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
blend, an = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
tips = []; ts = np.arange(act.frame_range[0], act.frame_range[1] + 0.01, 0.5)
for f in ts:
    bpy.context.scene.frame_set(int(f), subframe=float(f - int(f)))
    M = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
    tips.append(np.array(M @ Vector(G['handle_centre_hand_local']) + (M.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized() * 0.85))
sp = np.linalg.norm(np.diff(tips, axis=0), axis=1) * 60
for i in np.argsort(-sp)[:8]:
    print(f'TIPSPEED {an} t={ts[i] / 30:.3f}s frame {ts[i]:.1f}: {sp[i]:.1f} m/s')
print('TIPSPEED profile', ' '.join(f'{x:.0f}' for x in sp))
