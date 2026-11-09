"""Which way the sickle hand's palm faces, per clip frame: the handle centre (work/grip_pose.json, hand-local) relative
to the hand's knuckle-line midpoint, in world (character faces -Y, right hand at -X: +X = toward the body midline),
and the handle axis direction. Args: -- <blend> <action:frame> [...]"""
import bpy, sys, os, json
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); rig = bpy.data.objects['Rig']; sc = bpy.context.scene
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))
for pk in a[1:]:
    an, fr = pk.split(':'); act = bpy.data.actions[an]
    rig.animation_data_create(); rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    sc.frame_set(int(fr))
    H = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
    c = H @ Vector(G['handle_centre_hand_local']); ax = (H.to_3x3() @ Vector(G['handle_axis_hand_local'])).normalized()
    kn = sum((rig.matrix_world @ rig.pose.bones[f'B_R_Finger{i}'].head for i in (1, 2, 3, 4)), Vector()) / 4
    back = (H.to_3x3() @ Vector((0, 0, 1))).normalized()
    fd = (kn - H.translation).normalized(); pd = ax.cross(fd).normalized()
    if pd.dot(c - kn) < 0:
        pd = -pd                                                      # palm normal, on the handle's side
    print(f'PALM {pk}: palm normal (+x = toward the body) {tuple(round(x, 2) for x in pd)}; handle axis {tuple(round(x, 2) for x in ax)}; '
          f'hand at {tuple(round(x, 3) for x in H.translation)}')
