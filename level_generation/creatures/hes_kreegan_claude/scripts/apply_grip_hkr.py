"""hkr G5: both curled fists (work/grip_pose_L/R.json from curl_hkr.py, finger rotations relative to the hand)
replace the retargeted finger channels in every action (the carbine is held in all of them; the death keeps the fists).
Args: -- <in> <out>"""
import bpy, sys, os, json
from mathutils import Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']
G = {}
for s in 'LR':
    G.update(json.load(open(os.path.join(HERE, 'work', f'grip_pose_{s}.json')))['finger_local'])
for act in [a for a in bpy.data.actions if a.use_fake_user and not a.name.startswith('Demon_')]:
    rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for fc in [fc for fc in act.fcurves if any(f'"{n}"' in fc.data_path for n in G)] if hasattr(act, 'fcurves') else []:
        act.fcurves.remove(fc)
    for n, q in G.items():
        pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
        for f in range(f0, f1 + 1):
            pb.rotation_quaternion = Quaternion(q); pb.keyframe_insert('rotation_quaternion', frame=f)
    print('GRIP applied to', act.name, f0, f1)
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
