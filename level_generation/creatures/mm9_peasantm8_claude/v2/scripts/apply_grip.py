"""G5: the solved right-hand fist (work/grip_pose.json, finger rotations relative to the hand) replaces the retargeted
right-hand finger channels in every action (the source holds one constant grip in all of them).
LEFT_CURL (default 1): the empty left hand keeps that share of the source finger curl (slerp rest -> source), the
playbook's open-hand rule; hvm 0.5 (a web edge between the middle finger and the pinky base stretched 5-7x).
Args: -- <in> <out>"""
import bpy, sys, os, json
from mathutils import Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']
GP = os.path.join(HERE, 'work', 'grip_pose.json')
# hvm (unarmed peasant): no solved fist; both empty hands keep a share of the source curl (RIGHT_CURL / LEFT_CURL)
G = json.load(open(GP))['finger_local'] if os.path.exists(GP) and os.environ.get('UNARMED') != '1' else {}
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
    for sd, k in (('L', float(os.environ.get('LEFT_CURL', '1'))), ('R', float(os.environ.get('RIGHT_CURL', '1')) if not G else 1.0)):
      if k < 1:
        for pb in [p for p in rig.pose.bones if p.name.startswith(f'B_{sd}_Finger')]:
            pb.rotation_mode = 'QUATERNION'
            qs = []
            for f in range(f0, f1 + 1):
                bpy.context.scene.frame_set(f); qs.append(pb.rotation_quaternion.copy())
            for f, q in zip(range(f0, f1 + 1), qs):
                pb.rotation_quaternion = Quaternion().slerp(q, k); pb.keyframe_insert('rotation_quaternion', frame=f)
    print('GRIP applied to', act.name, f0, f1, 'solved fist' if G else 'no fist', 'curl L/R', os.environ.get('LEFT_CURL', '1'), os.environ.get('RIGHT_CURL', '1'))
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
