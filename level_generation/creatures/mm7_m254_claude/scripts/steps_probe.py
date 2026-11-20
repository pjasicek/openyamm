"""World-rotation step (deg) per half frame of bones over a frame range. Args: -- <blend> <action> <f0> <f1> bone [...]"""
import bpy, sys, os, math
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); rig = bpy.data.objects['Rig']; sc = bpy.context.scene
act = bpy.data.actions[a[1]]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
f0, f1 = int(a[2]), int(a[3])


def w(b, f):
    sc.frame_set(int(f), subframe=f - int(f)); return (rig.matrix_world @ rig.pose.bones[b].matrix).to_quaternion()


for b in a[4:]:
    st = []
    for k in range(2 * f0, 2 * f1):
        d = math.degrees(w(b, k / 2).rotation_difference(w(b, k / 2 + 0.5)).angle); st.append(round(min(d, 360 - d), 1))
    print('STEPS', b, f'{f0}..{f1} by 0.5:', st)
