"""G5: the solved right-hand fist (work/grip_pose.json, finger rotations relative to the hand) replaces the retargeted
right-hand finger channels in every action (the source holds one constant grip in all of them). Args: -- <in> <out>"""
import bpy, sys, os, json
from mathutils import Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']
G = json.load(open(os.path.join(HERE, 'work', 'male', 'handle_R.json')))['finger_local']
for act in [a for a in bpy.data.actions if a.name.startswith('Kept_Armed') or a.name=='Kept_MaceAttack']:
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for n, q in G.items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        for f in range(f0, f1 + 1):
            pb.rotation_quaternion = Quaternion(q)
            pb.keyframe_insert('rotation_quaternion', frame=f)
    print('GRIP applied to', act.name, f0, f1)
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
