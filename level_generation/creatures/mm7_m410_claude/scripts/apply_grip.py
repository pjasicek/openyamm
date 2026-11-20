"""G5: the solved right-hand fist (work/grip_pose.json, finger rotations relative to the hand) replaces the retargeted
right-hand finger channels in every action (the source holds one constant grip in all of them). Args: -- <in> <out>"""
import bpy, sys, os, json
from mathutils import Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
S = os.environ.get('SIDE', 'R')                            # m214: the bow fist is the LEFT hand (SIDE=L)
SUF = '' if S == 'R' else '_' + S
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']
G = json.load(open(os.path.join(HERE, 'work', f'grip_pose{SUF}.json')))['finger_local']
# m410: FIST_WEIGHTS=<json {action: [weight per frame]}> applies the fist only to the listed actions, slerped from the
# clip's own fingers by the per-frame weight (the dagger is in the hand only between the draw and the sheathing)
FW = json.load(open(os.environ['FIST_WEIGHTS'])) if os.environ.get('FIST_WEIGHTS') else None
for act in [a for a in bpy.data.actions if a.use_fake_user and (FW is None or a.name in FW)]:
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for n, q in G.items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        for f in range(f0, f1 + 1):
            if FW is None:
                pb.rotation_quaternion = Quaternion(q)
            else:
                bpy.context.scene.frame_set(f); q0 = pb.rotation_quaternion.copy(); qg = Quaternion(q)
                if q0.dot(qg) < 0:
                    qg = -qg
                pb.rotation_quaternion = q0.slerp(qg, FW[act.name][f - f0])
            pb.keyframe_insert('rotation_quaternion', frame=f)
    print('GRIP applied to', act.name, f0, f1)
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
