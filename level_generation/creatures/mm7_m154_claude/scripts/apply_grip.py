"""G5: the solved right-hand fist (work/grip_pose.json, finger rotations relative to the hand) replaces the retargeted
right-hand finger channels in every action (the source holds one constant grip in all of them).
LEFT_CURL (default 1): the empty left hand keeps that share of the source finger curl (slerp rest -> source), the
thumb THUMB_CURL (default LEFT_CURL; m154 0: its mis-fitted base tore the web 6.3x); the
playbook's open-hand rule; m154 0.5 (a web edge between the middle finger and the pinky base stretched 5-7x).
Args: -- <in> <out>"""
import bpy, sys, os, json
from mathutils import Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']
G = json.load(open(os.path.join(HERE, 'work', 'grip_pose.json')))['finger_local']
for act in [a for a in bpy.data.actions if a.use_fake_user]:
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for n, q in G.items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        for f in range(f0, f1 + 1):
            pb.rotation_quaternion = Quaternion(q)
            pb.keyframe_insert('rotation_quaternion', frame=f)
    k = float(os.environ.get('LEFT_CURL', '1'))
    if k < 1:
        for pb in [p for p in rig.pose.bones if p.name.startswith('B_L_Finger')]:
            kk = float(os.environ.get('THUMB_CURL', k)) if pb.name.startswith('B_L_Finger0') else k
            pb.rotation_mode = 'QUATERNION'
            qs = []
            for f in range(f0, f1 + 1):
                bpy.context.scene.frame_set(f); qs.append(pb.rotation_quaternion.copy())
            for f, q in zip(range(f0, f1 + 1), qs):
                pb.rotation_quaternion = Quaternion().slerp(q, kk); pb.keyframe_insert('rotation_quaternion', frame=f)
    print('GRIP applied to', act.name, f0, f1, 'left curl share', k)
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
