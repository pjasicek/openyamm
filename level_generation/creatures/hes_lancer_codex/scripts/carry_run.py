"""Mixamo Standard Run legs with the shared, calibrated two-handed upper-body carry."""
from pathlib import Path
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
import armik

P = Path(__file__).resolve().parents[1]
source, output = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=str(Path(source).resolve()))
rig = bpy.data.objects['Rig']
scene = bpy.context.scene
run = bpy.data.actions['Running']
carry = bpy.data.actions['Carbine_Running']
legs = {b.name for b in rig.pose.bones if any(x in b.name for x in ('Thigh', 'Calf', 'Foot', 'Toe'))}
legs.add('B_Pelvis')
poses = []
spines = []


def sample(action, frame):
    rig.animation_data_create()
    rig.animation_data.action = action
    if action.slots:
        rig.animation_data.action_slot = action.slots[0]
    scene.frame_set(int(frame), subframe=frame-int(frame))
    return {b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones}


end = int(run.frame_range[1])
for frame in range(end):
    lower = sample(run, frame)
    upper = sample(carry, frame/end*carry.frame_range[1])
    spine = armik.W(rig, 'B_Spine').copy()
    old_pelvis = armik.W(rig, 'B_Pelvis').translation.copy()
    sample(run, frame)
    spine.translation += armik.W(rig, 'B_Pelvis').translation - old_pelvis
    spines.append(spine)
    poses.append({n: lower[n] if n in legs else upper[n] for n in lower})
poses.append(poses[0])
spines.append(spines[0])
action = bpy.data.actions.new('Lancer_Running')
action.use_fake_user = True
rig.animation_data.action = action
previous = {}
for frame, pose in enumerate(poses):
    rig.animation_data.action = None
    for name, (rotation, location) in pose.items():
        bone = rig.pose.bones[name]
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_quaternion = rotation
        bone.location = location
    bpy.context.view_layer.update()
    armik.set_world(rig, 'B_Spine', spines[frame])
    corrected = {b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones}
    rig.animation_data.action = action
    for name, (rotation, location) in corrected.items():
        bone = rig.pose.bones[name]
        bone.rotation_mode = 'QUATERNION'
        if name in previous and rotation.dot(previous[name]) < 0:
            rotation = -rotation
        previous[name] = rotation.copy()
        bone.rotation_quaternion = rotation
        bone.location = location
        bone.keyframe_insert('rotation_quaternion', frame=frame)
        bone.keyframe_insert('location', frame=frame)
action.use_frame_range = True
action.frame_start = 0
action.frame_end = end
assert end == 22, 'Standard Run source duration changed'
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=str(Path(output).resolve()))
