"""Witch Standing: the native stands with her bare right palm raised beside her head, facing the viewer (xeen frames
mon_*). The magic attack clip (Cast, Mixamo Standing 1H Magic Attack 02, planted on Standing) starts and ends in that
stance, so Standing's right arm (clavicle, upper arm, forearm, hand, fingers) takes Cast frame 0's local rotations in
every frame; the idle's trunk, head, legs and left (staff) arm stay. Also makes Cast start/end on Standing.
Args: -- <in blend> <out blend> [source action] [target action ...]"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
src, out = a[0], a[1]; srcact = a[2] if len(a) > 2 else 'Cast'; targets = a[3:] or ['Standing']
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
ARM = [b.name for b in rig.data.bones if b.name.startswith('B_R_') and not any(k in b.name for k in ('Thigh', 'Calf', 'Foot', 'Toe'))]
def set_act(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if act is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
set_act(bpy.data.actions[srcact]); sc.frame_set(0)
pose = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in ARM}
for t in targets:
    act = bpy.data.actions[t]; set_act(act)
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        for n in ARM:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = pose[n]
            pb.keyframe_insert('rotation_quaternion', frame=f)
    print('STANCE', t, 'right arm from', srcact, 'frame 0:', len(ARM), 'bones x', f1 - f0 + 1, 'frames')
set_act(None)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
