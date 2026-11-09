"""Retarget the selected Mixamo clips (work/clips.json) onto the queen's upper body (work/rig_v1.blend), bar1 rule.

The library's Mixamo files carry the Warrok skeleton (hunched rest, bent knees), so each bone copies Mixamo's WORLD
rotation change from its rest pose onto the humanoid set's rest frame: S(t) = M(t) M_rest^-1 R_src; our posed world
frame is then C(t) S(t), where C(t) is a yaw that turns the source chest at frame 0 onto ours and removes the source
pelvis's later yaw (the queen's pelvis sits on her abdomen and never turns). B_Pelvis and the abdomen hold the rest
pose (the abdomen's own sway is added in author_clips.py); legs do not exist. Forearms keep only their hinge swing
(the hand takes the roll), as in the humanoid set. Keys at the source's 30 fps.
work/clips.json: {"<Action>": {"fbx": "<name under anim_library/mixamo>", "start": s, "end": s}} (seconds; optional).
Writes work/anim_v1.blend (actions named as the keys) and work/retarget.json."""
import bpy, sys, json, math
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
P = Path(__file__).resolve().parents[1]
REPO = P.parents[2]
CLIPS = json.loads((P / 'work' / 'clips.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'rig_v1.blend'))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']
OFF = json.loads(scene['rig_offsets'])
MAP = {'B_Pelvis': 'Hips', 'B_Spine': 'Spine', 'B_Spine1': 'Spine1', 'B_Spine2': 'Spine2', 'B_Neck': 'Neck',
       'B_Head': 'Head'}
for s, side in (('L', 'Left'), ('R', 'Right')):
    MAP.update({f'B_{s}_Clavicle': f'{side}Shoulder', f'B_{s}_UpperArm': f'{side}Arm',
                f'B_{s}_Forearm': f'{side}ForeArm', f'B_{s}_Hand': f'{side}Hand'})
    for i, f in enumerate(('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')):
        chain = [f'B_{s}_Finger{i}', f'B_{s}_Finger{i}1', f'B_{s}_Finger{i}2']
        if s == 'R' and i == 0:
            chain = ['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']
        for j, n in enumerate(chain):
            MAP[n] = f'{side}Hand{f}{j + 1}'
names = [b.name for b in rig.data.bones if b.name in OFF]            # parents first
R_SRC = {n: Matrix([Vector(r) for r in OFF[n]['R_src']]) for n in names}
OUT_FPS = 30.0
HINGE = ('B_L_Forearm', 'B_R_Forearm')
CHEST_FWD = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
PEL_FWD = R_SRC['B_Pelvis'].inverted() @ Vector((0, -1, 0))
yaw_of = lambda R, fwd: math.atan2((R @ fwd).y, (R @ fwd).x)
rest_chest = (rig.matrix_world @ rig.data.bones['B_Spine2'].matrix_local).to_3x3().normalized()
report = {}
for act_name, spec in CLIPS.items():
    before = set(bpy.data.objects); acts_before = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=str(REPO / 'anim_library/mixamo' / (spec['fbx'] + '.fbx')))
    fps_src = scene.render.fps / scene.render.fps_base
    new = set(bpy.data.objects) - before
    src = next(o for o in new if o.type == 'ARMATURE')
    pre = next(b.name for b in src.data.bones if b.name.endswith('Hips'))[:-4]
    sact = next(iter(set(bpy.data.actions) - acts_before))
    mapped = [n for n in names if n in MAP and pre + MAP[n] in src.data.bones]
    SW = src.matrix_world
    M0inv = {n: (SW @ src.data.bones[pre + MAP[n]].matrix_local).to_3x3().normalized().inverted() for n in mapped}
    src.animation_data.action = sact
    f0, f1 = sact.frame_range
    t0 = spec.get('start', 0.0); t1 = spec.get('end', (f1 - f0) / fps_src)
    n_out = int(round((t1 - t0) * OUT_FPS))
    rig.animation_data_create(); rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix()
    if act_name in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[act_name])
    act = bpy.data.actions.new(act_name); act.use_fake_user = True
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    rolls = []
    for i in range(n_out + 1):
        sf = f0 + (t0 + i / OUT_FPS) * fps_src
        scene.frame_set(int(math.floor(sf)), subframe=sf - math.floor(sf))
        S = lambda n: (SW @ src.pose.bones[pre + MAP[n]].matrix).to_3x3().normalized() @ M0inv[n] @ R_SRC[n]
        if i == 0:
            yaw0 = yaw_of(rest_chest, CHEST_FWD) - yaw_of(S('B_Spine2'), CHEST_FWD)
            py0 = yaw_of(S('B_Pelvis'), PEL_FWD)
        dpy = (yaw_of(S('B_Pelvis'), PEL_FWD) - py0 + math.pi) % (2 * math.pi) - math.pi
        C = Matrix.Rotation(yaw0 - dpy, 3, 'Z')
        for n in names:
            pb = rig.pose.bones[n]
            pb.rotation_mode = 'QUATERNION'
            if n not in mapped or n == 'B_Pelvis':
                pb.matrix_basis = Matrix(); bpy.context.view_layer.update()
                pb.keyframe_insert('rotation_quaternion', frame=i)
                continue
            M = (C @ S(n)).to_4x4()
            M.translation = rig.matrix_world @ pb.head
            pb.matrix = rig.matrix_world.inverted() @ M
            if n in HINGE:
                q = pb.rotation_quaternion
                t = 2 * math.atan2(q.y, q.w)
                pb.rotation_quaternion = q @ Quaternion((0, 1, 0), -t)
                rolls.append(abs((math.degrees(t) + 180) % 360 - 180))
            bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n_out
    rig.animation_data.action = None
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    for x in set(bpy.data.actions) - acts_before - {act}:
        bpy.data.actions.remove(x)
    report[act_name] = {'fbx': spec['fbx'], 'seconds': n_out / OUT_FPS, 'frames': n_out + 1, 'bones': len(mapped),
                        'forearm_roll_to_hand_max_deg': round(max(rolls) if rolls else 0.0, 1)}
    print('RETARGET', act_name, json.dumps(report[act_name]))
for pb in rig.pose.bones:
    pb.matrix_basis = Matrix()
scene.render.fps = 30; scene.render.fps_base = 1
(P / 'work' / 'retarget.json').write_text(json.dumps(report, indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / 'anim_v1.blend'))
