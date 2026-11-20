import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['Lizardman_Rig']; sc = bpy.context.scene
for t in rig.animation_data.nla_tracks: t.mute = True
act = bpy.data.actions[a[1]]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
names = ['Head', 'neck', 'Spine', 'LeftShoulder', 'RightShoulder', 'LeftHand', 'RightHand', 'Hips', 'LeftFoot', 'RightFoot', 'LeftToeBase', 'RightToeBase']
pos = {n: [] for n in names}; rot = {n: [] for n in ['LeftFoot', 'RightFoot']}
end = int(act.frame_range[1])
for f in range(end + 1):
    sc.frame_set(f)
    for n in names: pos[n].append(np.array(rig.pose.bones[n].head))
    for n in rot: rot[n].append(np.array(rig.pose.bones[n].matrix.to_quaternion()))
for n in names:
    p = np.array(pos[n]); print(n, 'range mm', np.round((p.max(0) - p.min(0)) * 1000, 1), 'loop gap mm', round(float(np.linalg.norm(p[0] - p[-1])) * 1000, 3))
for n in rot:
    q = np.array(rot[n]); d = np.degrees(2 * np.arccos(np.clip(np.abs(q @ q[0]), 0, 1))); print(n, 'rot dev deg max', round(float(d.max()), 4))
