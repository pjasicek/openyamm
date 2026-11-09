"""Retarget library clips (Mixamo FBX `mixamorig:*`, or a humanoid-set GLB `B_*`) onto the cleric rig (Cleric_Rig).

World rule: the rig's rest is first swung, limb by limb, so each joint segment (head -> child head) points like the
humanoid set's upright rest (the minimal swing keeps our own roll). Every frame each bone takes the source's WORLD
rotation change from its own rest, R_ours(t) = R_src(t) R_src_rest^-1 R_ours_matched (natm rule): for set clips this
is a plain world copy; the library's Mixamo files are retargeted to a hunched character (knees ~40 deg in its rest),
so copying their absolute directions crouched every clip. Trunk bones and
hands are not swung (both rests are upright, hands in line with the forearm). Hips position = source pelvis offset
from its rest, scaled by the hip-height ratio. Optional mirror (x -> -x, left/right swapped): the set holds the staff
in its right hand, the cleric in his left. The source's facing is turned to -Y (left hip at +X).
Staff, cloak and helper bones are left unkeyed (cloak_sim bakes the cloak afterwards).
Args: -- <in blend> <out blend> <file>:<clip or ->:<ActionName>[:mirror] [...]"""
import bpy, sys, os, math
from mathutils import Matrix, Vector

a = sys.argv[sys.argv.index('--') + 1:]
in_blend, out_blend, items = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
sc = bpy.context.scene
rig = bpy.data.objects['Cleric_Rig']
OURS = ['Hips', 'Spine02', 'Spine01', 'Spine', 'neck', 'Head',
        'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand', 'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand',
        'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase']
MIXAMO = {o: 'mixamorig:' + s for o, s in zip(OURS, [
    'Hips', 'Spine', 'Spine1', 'Spine2', 'Neck', 'Head',
    'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand', 'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand',
    'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase'])}
SET = dict(zip(OURS, [
    'B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head',
    'B_L_Clavicle', 'B_L_UpperArm', 'B_L_Forearm', 'B_L_Hand', 'B_R_Clavicle', 'B_R_UpperArm', 'B_R_Forearm', 'B_R_Hand',
    'B_L_Thigh', 'B_L_Calf', 'B_L_Foot', 'B_L_Toe0', 'B_R_Thigh', 'B_R_Calf', 'B_R_Foot', 'B_R_Toe0']))
# joint segments that define a limb direction (bone -> child joint); trunk and hands are not swung at the rest match
CHILD = {'LeftShoulder': 'LeftArm', 'LeftArm': 'LeftForeArm', 'LeftForeArm': 'LeftHand',
         'RightShoulder': 'RightArm', 'RightArm': 'RightForeArm', 'RightForeArm': 'RightHand',
         'LeftUpLeg': 'LeftLeg', 'LeftLeg': 'LeftFoot', 'LeftFoot': 'LeftToeBase',
         'RightUpLeg': 'RightLeg', 'RightLeg': 'RightFoot', 'RightFoot': 'RightToeBase'}
MX = Matrix.Diagonal((-1, 1, 1, 1))
REF_GLB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../anim_library/humanoid_set/2Hand Staff.glb')


def other(n):
    return n.replace('Left', '\0').replace('Right', 'Left').replace('\0', 'Right')


def rest_pose(arm):
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()


def src_world(src, names, mirror, turn):
    """world matrices of our-named bones as the source poses them (mirror swaps sides and reflects x)"""
    out = {}
    for o in OURS:
        pb = src.pose.bones[names[other(o) if mirror else o]]
        m = src.matrix_world @ pb.matrix
        if mirror:
            m = MX @ m @ MX
        out[o] = turn @ m
    return out


def rot(m):
    return m.to_quaternion().to_matrix()


def set_world_rot(o, R, head=None):
    pb = rig.pose.bones[o]
    cur = rig.matrix_world @ pb.matrix
    m = Matrix.Translation(head if head is not None else cur.to_translation()) @ R.to_4x4()
    pb.matrix = rig.matrix_world.inverted() @ m
    bpy.context.view_layer.update()


# the set's upright rest is the reference both kinds of source are matched through (imported once, then removed)
_objs, _acts = set(bpy.data.objects), set(bpy.data.actions)
bpy.ops.import_scene.gltf(filepath=REF_GLB)
ref = next(o for o in set(bpy.data.objects) - _objs if o.type == 'ARMATURE')
rest_pose(ref)
_lr = src_world(ref, SET, False, Matrix.Identity(4))
_lr = _lr['LeftUpLeg'].to_translation() - _lr['RightUpLeg'].to_translation()
Wref = src_world(ref, SET, False, Matrix.Rotation(-math.atan2(_lr.y, _lr.x), 4, 'Z'))
for o in set(bpy.data.objects) - _objs:
    bpy.data.objects.remove(o, do_unlink=True)
for x in set(bpy.data.actions) - _acts:
    bpy.data.actions.remove(x)

for item in items:
    parts = item.split(':')
    mirror = parts[-1] == 'mirror'
    if mirror:
        parts = parts[:-1]
    path, clip, act_name = ':'.join(parts[:-2]), parts[-2], parts[-1]
    before, acts_before = set(bpy.data.objects), set(bpy.data.actions)
    if path.lower().endswith('.fbx'):
        bpy.ops.import_scene.fbx(filepath=os.path.abspath(path), automatic_bone_orientation=False)
        names = MIXAMO
    else:
        bpy.ops.import_scene.gltf(filepath=os.path.abspath(path))
        names = SET
    new = set(bpy.data.objects) - before
    src = next(o for o in new if o.type == 'ARMATURE')
    newacts = list(set(bpy.data.actions) - acts_before)
    sact = newacts[0] if clip == '-' else next(x for x in newacts if x.name.split('|')[-1] == clip or x.name == clip)
    # rest of both, the facing turn, the hip-height ratio
    rest_pose(src); rest_pose(rig)
    W0 = src_world(src, names, mirror, Matrix.Identity(4))
    lr = W0['LeftUpLeg'].to_translation() - W0['RightUpLeg'].to_translation()
    yaw = math.atan2(lr.y, lr.x)                        # turn the left-hip direction onto +X
    turn = Matrix.Rotation(-yaw, 4, 'Z')
    Ws0 = src_world(src, names, mirror, turn)
    rw = {o: rig.matrix_world @ rig.pose.bones[o].matrix for o in OURS}
    k = (rw['Hips'].to_translation().z - min(rw['LeftFoot'].to_translation().z, rw['RightFoot'].to_translation().z)) / \
        (Ws0['Hips'].to_translation().z - min(Ws0['LeftFoot'].to_translation().z, Ws0['RightFoot'].to_translation().z))
    for o in OURS:                                      # parents first
        if o in CHILD:
            cur = rig.matrix_world @ rig.pose.bones[o].matrix
            dt = (rig.matrix_world @ rig.pose.bones[CHILD[o]].matrix).to_translation() - cur.to_translation()
            ds = Wref[CHILD[o]].to_translation() - Wref[o].to_translation()
            q = dt.normalized().rotation_difference(ds.normalized()).to_matrix()
            set_world_rot(o, q @ rot(cur))
    C = {o: rot(Ws0[o]).inverted() @ rot(rig.matrix_world @ rig.pose.bones[o].matrix) for o in OURS}
    hips_rest = rw['Hips'].to_translation(); src_hips0 = Ws0['Hips'].to_translation()
    # bake
    src.animation_data.action = sact
    if getattr(sact, 'slots', None) is not None and len(sact.slots):
        src.animation_data.action_slot = sact.slots[0]
    f0, f1 = (int(round(x)) for x in sact.frame_range)
    act = bpy.data.actions.get(act_name)
    if act:
        bpy.data.actions.remove(act)
    act = bpy.data.actions.new(act_name); act.use_fake_user = True
    rest_pose(rig)
    rig.animation_data_create(); rig.animation_data.action = act
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    prev = {}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        Ws = src_world(src, names, mirror, turn)
        for o in OURS:
            R = rot(Ws[o]) @ C[o]
            head = hips_rest + (Ws['Hips'].to_translation() - src_hips0) * k if o == 'Hips' else None
            set_world_rot(o, R, head)
        for o in OURS:
            pb = rig.pose.bones[o]
            q = pb.matrix_basis.to_quaternion()
            if o in prev and prev[o].dot(q) < 0:       # sign-continuous keys
                q.negate()
            prev[o] = q
            pb.rotation_quaternion = q
            pb.keyframe_insert('rotation_quaternion', frame=f - f0)
            if o == 'Hips':
                pb.location = pb.matrix_basis.to_translation()
                pb.keyframe_insert('location', frame=f - f0)
    rig.animation_data.action = None
    for o in list(new):
        bpy.data.objects.remove(o, do_unlink=True)
    for x in newacts:
        bpy.data.actions.remove(x)
    print('RETARGET', act_name, 'from', os.path.basename(path), clip, 'mirror' if mirror else '', 'frames', f1 - f0 + 1,
          'hip ratio', round(k, 3), 'yaw', round(math.degrees(yaw), 1))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
