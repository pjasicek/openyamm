"""Probe: head and pelvis height per frame of an action (cm), to read the walk's vertical bob.
Args: -- <blend> <action> [...]"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    hz, pz = [], []
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        sc.frame_set(f)
        hz.append((rig.matrix_world @ rig.pose.bones['B_Head'].head).z * 100)
        pz.append((rig.matrix_world @ rig.pose.bones['B_Pelvis'].head).z * 100)
    print(f'BOB {an} head ' + ' '.join(f'{z - min(hz):.1f}' for z in hz))
    print(f'BOB {an} pelv ' + ' '.join(f'{z - min(pz):.1f}' for z in pz))
