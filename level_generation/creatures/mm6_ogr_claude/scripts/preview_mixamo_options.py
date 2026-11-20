"""Fit the shortlisted local FBXs to an isolated Ogre viewer copy, preserving production assets."""
from pathlib import Path
import ast, hashlib, json, math
import bpy
from mathutils import Matrix, Vector, Quaternion

p = Path(__file__).resolve().parents[1]
out = p / 'review/motion_options'
out.mkdir(parents=True, exist_ok=True)
lib = Path('/home/pjasicek/Downloads/mixamo_library')
bpy.ops.wm.open_mainfile(filepath=str(p / 'export/mm6_ogr.blend'))
rig = bpy.data.objects['Rig']
body = bpy.data.objects['Ogre']
scene = bpy.context.scene
scene.render.fps = 30
scene.render.fps_base = 1
mapping = {'B_Pelvis': 'Hips', 'B_Spine': 'Spine', 'B_Spine1': 'Spine1', 'B_Spine2': 'Spine2',
           'B_Neck': 'Neck', 'B_Head': 'Head'}
for side, long in [('L', 'Left'), ('R', 'Right')]:
    for target, source in [('Clavicle', 'Shoulder'), ('UpperArm', 'Arm'), ('Forearm', 'ForeArm'),
                           ('Hand', 'Hand'), ('Thigh', 'UpLeg'), ('Calf', 'Leg'), ('Foot', 'Foot'), ('Toe0', 'ToeBase')]:
        mapping[f'B_{side}_{target}'] = f'{long}{source}'
mapping = {n: 'mixamorig:' + mapping[n] for n in rig.data.bones.keys() if n in mapping}
options = [
    ('Running_Weighted', 'Running (5)', 'Running · A — weighted run', 'Running'),
    ('Running_SlowJog', 'Slow Jog', 'Running · B — slow jog', 'Running'),
    ('Attack_Downward', 'Standing Melee Attack Downward', 'Attack · A — overhead chop', 'Attack'),
    ('Attack_Horizontal', 'Standing Melee Attack Horizontal', 'Attack · B — horizontal cut', 'Attack'),
    ('Hit_SmallFront', 'Standing React Small From Front', 'Hit · A — small front recoil', 'Hit'),
    ('Hit_GettingHit', 'Getting Hit', 'Hit · B — stronger forward flinch', 'Hit'),
    ('Fidget_NeckStretch', 'Neck Stretching', 'Fidget · A — neck stretching', 'Fidget'),
    ('Fidget_OrcIdle', 'Orc Idle (1)', 'Fidget · B — orc idle', 'Fidget'),
]

def select(arm, action):
    arm.animation_data_create()
    arm.animation_data.action = action
    if action and len(action.slots):
        arm.animation_data.action_slot = action.slots[0]


def load_source(path):
    before, acts = set(bpy.data.objects), set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=str(path), use_anim=True)
    new = set(bpy.data.objects) - before
    arm = next(o for o in new if o.type == 'ARMATURE')
    return arm, arm.animation_data.action, new, set(bpy.data.actions) - acts


def discard(objects, actions):
    for o in objects:
        bpy.data.objects.remove(o, do_unlink=True)
    for a in actions:
        bpy.data.actions.remove(a)

# A posed neutral calibration avoids transferring the downloaded character's permanently bent rest legs.
# Both calibration poses are relaxed standing poses, never a T-pose mapped onto the Ogre's A-pose.
select(rig, bpy.data.actions['Standing'])
scene.frame_set(0)
neutral = {n: rig.matrix_world @ rig.pose.bones[n].matrix for n in mapping}
neutral_local = {b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones}
source, action, objects, actions = load_source(lib / 'Standard Idle.fbx')
scene.frame_set(int(action.frame_range[0]))
source_neutral = {n: source.matrix_world @ source.pose.bones[s].matrix for n, s in mapping.items()}
offsets = {n: source_neutral[n].to_quaternion().inverted() @ neutral[n].to_quaternion() for n in mapping}
# The cleaver's handle must exit the index/thumb side of the source fist. Neutral open-hand rotation alone
# inverted the weapon during the overhead swing, so map measured palm/grip axes rather than carrying that offset.
hand_source = source.data.bones['mixamorig:RightHand'].matrix_local
source_inverse = hand_source.inverted()
sa = (source_inverse.to_3x3() @ (source.data.bones['mixamorig:RightHandIndex1'].head_local
      - source.data.bones['mixamorig:RightHandPinky1'].head_local)).normalized()
sf = (source_inverse @ source.data.bones['mixamorig:RightHandMiddle1'].head_local).normalized()
hand_target = rig.data.bones['B_R_Hand'].matrix_local
hand_grip = json.loads((p / 'work/grip_pose.json').read_text())
ta = Vector(hand_grip['handle_axis_hand_local']).normalized()
tf = (hand_target.inverted() @ rig.data.bones['B_R_Finger2'].head_local).normalized()
def palm_basis(axis, forward):
    forward = (forward - axis * axis.dot(forward)).normalized()
    return Matrix([axis, forward, axis.cross(forward)]).transposed()
offsets['B_R_Hand'] = (palm_basis(sa, sf) @ palm_basis(ta, tf).transposed()).to_quaternion()
scale = neutral['B_Pelvis'].translation.z / source_neutral['B_Pelvis'].translation.z
neutral_floor = min((rig.matrix_world @ rig.pose.bones[f'B_{s}_Foot'].head).z for s in 'LR')
discard(objects, actions)

# Existing measured hand grip, twist distribution and cloth fitting; no weight/mesh changes.
G = json.loads((p / 'work/grip_pose.json').read_text())['finger_local']
G.update({b.name: [1, 0, 0, 0] for b in rig.data.bones if b.name.startswith('B_L_Finger')})
tree = ast.parse((p / 'scripts/twist_bones.py').read_text())
functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ['twist_about', 'bake_twist']]
exec(compile(ast.Module(body=functions, type_ignores=[]), 'twist_bones.py', 'exec'), globals())
FA = UA = .5
pelrest = rig.data.bones['B_Pelvis'].matrix_local
axes = {n: (rig.data.bones[n].matrix_local.to_3x3().inverted() @ Vector((1, 0, 0))).normalized()
        for n in ['LoinFront', 'LoinBack']}
restangles = {}
for side in 'LR':
    d = rig.data.bones[f'B_{side}_Calf'].head_local - rig.data.bones[f'B_{side}_Thigh'].head_local
    restangles[side] = math.atan2(-d.y, -d.z)
report = {}
for name, stem, label, role in options:
    select(rig, None)
    source, source_action, objects, actions = load_source(lib / (stem + '.fbx'))
    source_fps = scene.render.fps / scene.render.fps_base
    assert source_fps == 30, source_fps
    f0, f1 = [int(round(f)) for f in source_action.frame_range]
    samples = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        samples.append({n: source.matrix_world @ source.pose.bones[s].matrix for n, s in mapping.items()})
    discard(objects, actions)
    scene.render.fps = 30
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    select(rig, act)
    previous = {}
    for f, sample in enumerate(samples):
        scene.frame_set(f)
        for pb in rig.pose.bones:
            pb.matrix_basis.identity()
            pb.rotation_mode = 'QUATERNION'
        bpy.context.view_layer.update()
        for n in mapping:
            pb = rig.pose.bones[n]
            rotation = sample[n].to_quaternion() @ offsets[n]
            matrix = rotation.to_matrix().to_4x4()
            matrix.translation = rig.matrix_world @ pb.head
            if n == 'B_Pelvis':
                position = neutral[n].translation.copy()
                position.z += (sample[n].translation.z - source_neutral[n].translation.z) * scale
                matrix.translation = position
            pb.matrix = rig.matrix_world.inverted() @ matrix
            # Pose bones carry rotation only, retaining the fitted fixed-length chains.
            if n != 'B_Pelvis':
                pb.location = (0, 0, 0)
            pb.scale = (1, 1, 1)
            bpy.context.view_layer.update()
        # Ground the supporting foot after proportion transfer; no XY root drift in this stationary viewer.
        floor = min((rig.matrix_world @ rig.pose.bones[f'B_{s}_Foot'].head).z for s in 'LR')
        pelvis = rig.pose.bones['B_Pelvis']
        matrix = pelvis.matrix.copy()
        matrix.translation.z += neutral_floor - floor
        pelvis.matrix = matrix
        bpy.context.view_layer.update()
        for n, q in G.items():
            rig.pose.bones[n].rotation_quaternion = Quaternion(q)
        undo = (rig.pose.bones['B_Pelvis'].matrix @ pelrest.inverted()).inverted().to_3x3()
        angles = []
        for side in 'LR':
            d = undo @ (rig.pose.bones[f'B_{side}_Calf'].head - rig.pose.bones[f'B_{side}_Thigh'].head)
            angles.append(math.atan2(-d.y, -d.z) - restangles[side])
        for n, angle in [('LoinFront', -max(0, *angles) * 1.12 - math.radians(8)),
                         ('LoinBack', -min(0, *angles) * 1.12 + math.radians(8))]:
            rig.pose.bones[n].rotation_quaternion = Quaternion(axes[n], angle)
        for pb in rig.pose.bones:
            q = pb.rotation_quaternion.copy()
            if pb.name in previous and q.dot(previous[pb.name]) < 0:
                q.negate()
            pb.rotation_quaternion = q
            previous[pb.name] = q.copy()
            pb.keyframe_insert('rotation_quaternion', frame=f)
            pb.keyframe_insert('location', frame=f)
    act.use_frame_range = True
    act.frame_start, act.frame_end = 0, len(samples) - 1
    bake_twist(act)
    report[name] = {'label': label, 'role': role, 'source': str(lib / (stem + '.fbx')),
                    'source_sha256': hashlib.sha256((lib / (stem + '.fbx')).read_bytes()).hexdigest(),
                    'duration': (len(samples) - 1) / 30, 'source_fps': source_fps,
                    'adaptation': 'Neutral standing calibration, fixed-length chains, in-place root, grounded support foot; retained fitted fingers/twist/cloth.'}
    print('OPTION', name, report[name]['duration'], flush=True)

for act in bpy.data.actions:
    curves = [fc for layer in act.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
    if act.name in report:
        for fc in curves:
            for key in fc.keyframe_points:
                key.interpolation = 'LINEAR'
select(rig, bpy.data.actions['Standing'])
scene.frame_set(0)
for o in bpy.data.objects:
    o.select_set(o in (body, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'ogre_motion_options.blend'))
bpy.ops.export_scene.gltf(filepath=str(out / 'ogre_motion_options.glb'), use_selection=True, export_format='GLB',
    export_yup=True, export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
    export_frame_step=1, export_skins=True, export_all_influences=True, export_attributes=False,
    export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True, export_anim_slide_to_zero=True)
(out / 'sources.json').write_text(json.dumps(report, indent=2) + '\n')
assert len(report) == 8
print('OPTIONS_EXPORTED', flush=True)
