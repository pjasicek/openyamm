"""Retarget Mixamo FBX clips (mixamorig:* bones, the library's Warrok skeleton) onto our rig (work/rig_v1.blend,
frames cloned from the humanoid set by build_rig.py), for upright one-handed clips the set lacks (user review
2026-10-11: the set's Armed/1Hand clips are a low guard, pelvis ~0.65 of the leg length, knees 60-90 deg).
Rule: the library's Mixamo files are retargeted to Warrok (hunched, knees bent ~40 deg in its rest pose), so absolute
bone directions would copy his build. Each bone copies Mixamo's WORLD rotation change from its rest pose instead,
D(t) = M(t) M_rest^-1, applied to the humanoid set's rest frame: S(t) = D(t) R_src. retarget.py's world rule then
holds unchanged (our rest = q @ R_src, posed world = S), so the mesh-measured hands and fingers keep their calibration.
Pelvis: horizontal travel = Mixamo hips travel x the leg-length ratio; height = rest height moved so that the lowest
foot point (ankle or toe, against its rest height) lifts exactly as the source's, scaled - feet stay on the floor
whatever the leg proportions. Forearms keep only their hinge swing (the hand takes their roll, as in the set).
Keys at 30 fps. Unmapped bones (twist bones are added later) keep their rest pose.
Stance plant (<fbx>:<ActionName>:plant, after Standing): the Mixamo attack and battle cry lunge or stagger into a
wide stance (pelvis 20-27 cm lower; user review 2026-10-11 asked for upright clips, and the native attack stands in
place). Pelvis (world) and legs (local) hold Standing's frame 0; every other bone keeps its world motion, carried by a
yaw C(t) that turns the source chest at frame 0 onto Standing's chest and removes the source pelvis's later yaw change
(druidess rule, mm6_dru1_claude/scripts/retarget.py).
<fbx>:<ActionName>:turn applies only that yaw (legs free; clip_timing.py blends part of it into the planted clip).
Args: -- <in blend> <out blend> <fbx>:<ActionName>[:plant|:turn] [...]"""
import bpy, sys, os, json, math
from mathutils import Matrix, Vector, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src_blend, out_blend, items = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src_blend))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']
OFF = json.loads(scene['rig_offsets'])
MAP = {'B_Pelvis': 'Hips', 'B_Spine': 'Spine', 'B_Spine1': 'Spine1', 'B_Spine2': 'Spine2', 'B_Neck': 'Neck',
       'B_Head': 'Head'}
for s, side in (('L', 'Left'), ('R', 'Right')):
    MAP.update({f'B_{s}_Clavicle': f'{side}Shoulder', f'B_{s}_UpperArm': f'{side}Arm',
                f'B_{s}_Forearm': f'{side}ForeArm', f'B_{s}_Hand': f'{side}Hand', f'B_{s}_Thigh': f'{side}UpLeg',
                f'B_{s}_Calf': f'{side}Leg', f'B_{s}_Foot': f'{side}Foot', f'B_{s}_Toe0': f'{side}ToeBase'})
    for i, f in enumerate(('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')):
        chain = [f'B_{s}_Finger{i}', f'B_{s}_Finger{i}1', f'B_{s}_Finger{i}2']
        if s == 'R' and i == 0:
            chain = ['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']
        for j, n in enumerate(chain):
            MAP[n] = f'{side}Hand{f}{j + 1}'
names = [b.name for b in rig.data.bones]                                       # parents first
R_SRC = {n: Matrix([Vector(r) for r in OFF[n]['R_src']]) for n in names}
OUT_FPS = 30.0
HINGE = ('B_L_Forearm', 'B_R_Forearm')


def foot_lift(P, rest):
    """lowest rise of either ankle or toe joint above its rest height"""
    return min(P(n).z - rest[n] for n in rest)


def leg_length(P, hip, knee, ankle):
    return (P(hip) - P(knee)).length + (P(knee) - P(ankle)).length


LEGS = [n for n in names if any(t in n for t in ('Thigh', 'Calf', 'Foot', 'Toe'))]
CHEST_FWD = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
PEL_FWD = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))
yaw_of = lambda R, fwd: math.atan2((R @ fwd).y, (R @ fwd).x)
report = {}
for item in items:
    parts = item.split(':')
    mode = parts[-1] if parts[-1] in ('plant', 'turn') else ''
    fbx, act_name = parts[-3:-1] if mode else parts[-2:]
    plant = None
    if mode:
        st = bpy.data.actions['Standing']
        rig.animation_data_create(); rig.animation_data.action = st
        if getattr(st, 'slots', None) is not None and len(st.slots):
            rig.animation_data.action_slot = st.slots[0]
        scene.frame_set(0)
        plant = {'pelvis': (rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix).copy(),
                 'chest': (rig.matrix_world @ rig.pose.bones['B_Spine2'].matrix).to_3x3().normalized(),
                 'legs': {n: rig.pose.bones[n].matrix_basis.copy() for n in LEGS}}
        rig.animation_data.action = None
    before = set(bpy.data.objects); acts_before = set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
    fps_src = scene.render.fps / scene.render.fps_base                       # the FBX import sets its own rate
    new = set(bpy.data.objects) - before
    src = next(o for o in new if o.type == 'ARMATURE')
    pre = next(b.name for b in src.data.bones if b.name.endswith('Hips'))[:-4]
    sact = next(iter(set(bpy.data.actions) - acts_before))
    mapped = [n for n in names if n in MAP and pre + MAP[n] in src.data.bones]
    SW = src.matrix_world
    M0inv = {n: (SW @ src.data.bones[pre + MAP[n]].matrix_local).to_3x3().normalized().inverted() for n in mapped}
    hips0 = SW @ src.data.bones[pre + 'Hips'].head_local
    SP = lambda n: SW @ src.pose.bones[pre + n].head
    src.animation_data.action = None
    for pb in src.pose.bones:
        pb.matrix_basis = Matrix()
    rig.animation_data_create(); rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix()
    bpy.context.view_layer.update()
    RP = lambda n: rig.matrix_world @ rig.pose.bones[n].head
    s_rest = {n: SP(n).z for n in ('LeftFoot', 'RightFoot', 'LeftToeBase', 'RightToeBase')}
    o_rest = {n: RP(n).z for n in ('B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0')}
    k = leg_length(RP, 'B_L_Thigh', 'B_L_Calf', 'B_L_Foot') / leg_length(SP, 'LeftUpLeg', 'LeftLeg', 'LeftFoot')
    pelvis0 = rig.matrix_world @ rig.pose.bones['B_Pelvis'].head
    src.animation_data.action = sact
    f0, f1 = sact.frame_range
    n_out = int(round((f1 - f0) / fps_src * OUT_FPS))
    if act_name in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[act_name])
    act = bpy.data.actions.new(act_name); act.use_fake_user = True
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    lifts = []; rolls = []; previous = {}
    for i in range(n_out + 1):
        sf = f0 + i / OUT_FPS * fps_src
        scene.frame_set(int(math.floor(sf)), subframe=sf - math.floor(sf))
        hips = SW @ src.pose.bones[pre + 'Hips'].head
        lift_src = foot_lift(SP, s_rest) * k
        S = lambda n: (SW @ src.pose.bones[pre + MAP[n]].matrix).to_3x3().normalized() @ M0inv[n] @ R_SRC[n]
        C = Matrix.Identity(3)
        if plant is not None:      # plant and turn: same yaw alignment; only plant holds pelvis and legs
            if i == 0:
                yaw0 = yaw_of(plant['chest'], CHEST_FWD) - yaw_of(S('B_Spine2'), CHEST_FWD)
                py0 = yaw_of(S('B_Pelvis'), PEL_FWD)
            dpy = (yaw_of(S('B_Pelvis'), PEL_FWD) - py0 + math.pi) % (2 * math.pi) - math.pi
            C = Matrix.Rotation(yaw0 - dpy, 3, 'Z')
        for n in names:
            pb = rig.pose.bones[n]
            pb.rotation_mode = 'QUATERNION'
            if n not in mapped:
                pb.matrix_basis = Matrix(); bpy.context.view_layer.update()
                pb.keyframe_insert('rotation_quaternion', frame=i)
                continue
            if mode == 'plant' and n in LEGS:
                pb.matrix_basis = plant['legs'][n]; bpy.context.view_layer.update()
                pb.keyframe_insert('rotation_quaternion', frame=i)
                continue
            M = (C @ S(n)).to_4x4()
            if n == 'B_Pelvis' and mode == 'plant':
                M = plant['pelvis'].copy()
            elif n == 'B_Pelvis':
                d = (hips - hips0) * k
                M.translation = pelvis0 + Vector((d.x, d.y, 0.0))
            else:
                M.translation = rig.matrix_world @ pb.head
            pb.matrix = rig.matrix_world.inverted() @ M
            if n in HINGE:
                # Mixamo rolls the forearm bone itself (90-125 deg in the attack and battle cry); the set's forearm is a
                # pure hinge and the hand carries the roll, which twist_bones.py distributes. Keep only the swing about
                # the bone axis (local Y); the hand, set in world space next, takes the removed roll.
                q = pb.rotation_quaternion
                t = 2 * math.atan2(q.y, q.w)
                pb.rotation_quaternion = q @ Quaternion((0, 1, 0), -t)
                rolls.append(abs((math.degrees(t) + 180) % 360 - 180))
            if 'Finger' in n:
                pb.rotation_quaternion = Quaternion().slerp(pb.rotation_quaternion, .20)
            if n in previous and pb.rotation_quaternion.dot(previous[n]) < 0:
                pb.rotation_quaternion = -pb.rotation_quaternion
            previous[n] = pb.rotation_quaternion.copy()
            bpy.context.view_layer.update()
            pb.keyframe_insert('rotation_quaternion', frame=i)
        # floor: lift the pelvis so our lowest foot point rises as the source's does (planted: Standing's feet)
        dz = 0.0 if mode == 'plant' else lift_src - foot_lift(RP, o_rest)
        pb = rig.pose.bones['B_Pelvis']
        M = rig.matrix_world @ pb.matrix
        M.translation = M.translation + Vector((0, 0, dz))
        pb.matrix = rig.matrix_world.inverted() @ M
        bpy.context.view_layer.update()
        pb.keyframe_insert('rotation_quaternion', frame=i)
        pb.keyframe_insert('location', frame=i)
        lifts.append((M.translation.z - pelvis0.z, lift_src))
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n_out
    rig.animation_data.action = None
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    for x in set(bpy.data.actions) - acts_before - {act}:
        bpy.data.actions.remove(x)
    scene.render.fps = 24; scene.render.fps_base = 1
    drop = [d for d, _ in lifts]
    print(f'RETARGET {act_name} <- {os.path.basename(fbx)}{" (planted on Standing)" if mode == "plant" else " (turned onto Standing)" if mode else ""}: {n_out + 1} frames = {n_out / OUT_FPS:.3f} s, '
          f'{len(mapped)} bones, leg ratio {k:.3f}, pelvis drop cm mean {100 * sum(drop) / len(drop):.1f} '
          f'min {100 * min(drop):.1f}, max foot lift cm {100 * max(l for _, l in lifts):.1f}, forearm roll moved to the '
          f'hand max {max(rolls):.0f} deg')
    report[act_name] = {'clip': os.path.relpath(os.path.abspath(fbx), os.path.dirname(os.path.abspath(out_blend))),
                        'source': 'mixamo', 'frames': n_out + 1}
for pb in rig.pose.bones:
    pb.matrix_basis = Matrix()
scene.render.fps = 30; scene.render.fps_base = 1
prev = json.loads(scene.get('retarget_report', '{}')); prev.update(report)
scene['retarget_report'] = json.dumps(prev)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
