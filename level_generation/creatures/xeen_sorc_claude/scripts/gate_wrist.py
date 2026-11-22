"""Arm gate numbers per clip: wrist swing (hand vs forearm, deg) and hand twist about the forearm (deg) for both hands,
max and the frame of the max. Gate: swing <= 60, twist continuous. Args: -- <blend> [action ...]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
acts = a[1:] or [x.name for x in bpy.data.actions if x.use_fake_user and x.name != 'GripRef']
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    res = {}
    for s in 'LR':
        sw, tw = [], []
        for f in range(int(act.frame_range[1]) + 1):
            sc.frame_set(f)
            x, t = armik.wrist_cost(rig, s, armik.W(rig, f'B_{s}_Hand').to_3x3().normalized())
            sw.append(x); tw.append(t)
        jumps = max(abs(tw[i + 1] - tw[i]) for i in range(len(tw) - 1))
        res[s] = f'swing max {max(sw):.0f} @{sw.index(max(sw))} twist {min(tw):.0f}..{max(tw):.0f} step max {jumps:.0f}'
    print('WRIST', name, '| L', res['L'], '| R', res['R'])
