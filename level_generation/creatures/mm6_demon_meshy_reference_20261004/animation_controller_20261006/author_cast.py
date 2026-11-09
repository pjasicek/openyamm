"""Add a two-handed cast and attachment sockets to a copy of the selected textured animation master."""
import importlib.util
import json
import math
from pathlib import Path
import bpy
from mathutils import Matrix, Quaternion, Vector

stage = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('posing', stage.parent / 'attack_animation_v2/motion.py')
posing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(posing)
bpy.ops.wm.open_mainfile(filepath=str(stage.parent / 'texturing_fixed_20261005/mm6_demon_textured.blend'))
scene = bpy.data.scenes['MM6_Demon_Textured_Animations']
bpy.context.window.scene = scene
scene.render.fps = 48
rig = next(o for o in scene.objects if o.get('material_role') == 'rig')
mesh = next(o for o in scene.objects if o.get('material_role') == 'body')
rig.hide_set(False)
for track in rig.animation_data.nla_tracks:
    track.mute = track.name != 'Standing'
scene.frame_set(0)
standing = {b.name: b.matrix_basis.copy() for b in rig.pose.bones}
standing_hands = {side: rig.pose.bones['mixamorig:' + side + 'Hand'].head.copy() for side in ('Left', 'Right')}
standing_q = {side: rig.pose.bones['mixamorig:' + side + 'Hand'].matrix.to_quaternion() for side in standing_hands}
evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
iris_vertices = {i for p in evaluated.data.polygons if p.material_index == 1 for i in p.vertices}
eye_points = {}
head = rig.pose.bones['mixamorig:Head']
for side, sign in [('Left', 1), ('Right', -1)]:
    points = [evaluated.data.vertices[i].co for i in iris_vertices if evaluated.data.vertices[i].co.x * sign > 0]
    assert points
    point = sum(points, Vector()) / len(points)
    point.y = min(p.y for p in points) - .002
    eye_points[side] = head.bone.matrix_local @ head.matrix.inverted() @ point
for track in rig.animation_data.nla_tracks:
    track.mute = True
action = bpy.data.actions.new('Cast_FireBolt')
rig.animation_data.action = action


def smooth(value):
    value = min(1.0, max(0.0, value))
    return value * value * (3 - 2 * value)


def pose(frame):
    t = frame / 48
    gather = smooth(t / .34)
    release = smooth((t - .84) / .16)
    for bone in rig.pose.bones:
        bone.matrix_basis = standing[bone.name].copy()
    posing.update()
    posing.rotate(rig.pose.bones['mixamorig:Spine2'], Quaternion((1, 0, 0), math.radians(4 * gather - 6 * release)))
    posing.rotate(rig.pose.bones['mixamorig:Head'], Quaternion((1, 0, 0), math.radians(9 * gather - 10 * release)))
    for side, sign in [('Left', 1), ('Right', -1)]:
        upper, lower, hand = [rig.pose.bones['mixamorig:' + side + s] for s in ('Arm', 'ForeArm', 'Hand')]
        # Palms cup a small sphere; fingers converge above it, then the hands thrust apart on release.
        pulse = .004 * math.sin((t - .34) * math.pi * 8) * gather * (1 - release)
        destination = Vector((sign * (.105 + .15 * release), -.63 - .17 * release,
                              1.135 + pulse + .035 * release))
        target = standing_hands[side].lerp(destination, gather)
        a = lower.bone.head_local - upper.bone.head_local
        b = hand.bone.head_local - lower.bone.head_local
        l1, l2 = a.length, b.length
        hip = upper.head.copy()
        delta = target - hip
        distance = delta.length
        assert abs(l1 - l2) < distance < l1 + l2, (side, t, distance, l1 + l2)
        axis = delta.normalized()
        hint = Vector((sign, .10, -.50))
        pole = (hint - axis * hint.dot(axis)).normalized()
        along = (l1*l1 - l2*l2 + distance*distance) / (2*distance)
        elbow = hip + axis * along + pole * math.sqrt(max(0, l1*l1 - along*along))
        posing.assign(upper, a.rotation_difference(elbow - hip) @ upper.bone.matrix_local.to_quaternion(), hip)
        posing.assign(lower, b.rotation_difference(target - elbow) @ lower.bone.matrix_local.to_quaternion(), elbow)
        bases = [rig.data.bones['mixamorig:' + side + 'Hand' + d + '1'].head_local
                 for d in ('Index', 'Middle', 'Pinky', 'Ring')]
        rest_long = sum(bases, Vector()) / 4 - hand.bone.head_local
        rest_width = bases[-1] - bases[0]
        rest_normal = rest_width.cross(rest_long).normalized()
        if side == 'Left':
            rest_normal.negate()
        rest_basis = posing.palm_basis(rest_long, rest_normal)
        long = Vector((-sign * (.78 - .45*release), -.32 - .30*release, .65 - .25*release))
        normal = Vector((-sign, -.15, -.20))
        basis = posing.palm_basis(long, normal)
        desired = (basis @ rest_basis.transposed() @ hand.bone.matrix_local.to_3x3()).to_quaternion()
        desired = standing_q[side].slerp(desired, gather)
        forearm_axis = (target - elbow).normalized()
        difference = desired @ hand.matrix.to_quaternion().inverted()
        if difference.w < 0:
            difference.negate()
        roll = 2 * math.atan2(Vector((difference.x, difference.y, difference.z)).dot(forearm_axis), difference.w)
        posing.rotate(lower, Quaternion(forearm_axis, roll))
        for i, fraction in enumerate((0, 1/3, 2/3)):
            posing.rotate(rig.pose.bones[f'Demon_{side}_ForearmTwist{i}'],
                          Quaternion(forearm_axis, -roll * (1 - fraction)))
        posing.assign(hand, desired, target)
        # Keep the existing claw shapes; modest local joint curls form the channeling cup.
        for digit in ('Index', 'Middle', 'Pinky', 'Ring'):
            for joint, angle in [(1, 8), (2, 12), (3, 5)]:
                bone = rig.pose.bones[f'mixamorig:{side}Hand{digit}{joint}']
                bone.rotation_mode = 'QUATERNION'
                bone.rotation_quaternion = bone.rotation_quaternion @ Quaternion(
                    (1, 0, 0), math.radians(angle * gather * (1 - release)))
        posing.update()


for frame in range(49):
    scene.frame_set(frame)
    pose(frame)
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        for channel in ('location', 'rotation_quaternion', 'scale'):
            bone.keyframe_insert(channel, frame=frame, group=bone.name)
for curve in action.layers[0].strips[0].channelbag(action.slots[0]).fcurves:
    for key in curve.keyframe_points:
        key.interpolation = 'LINEAR'
rig.animation_data.action = None
track = rig.animation_data.nla_tracks.new()
track.name = 'Cast_FireBolt'
track.strips.new('Cast_FireBolt', 0, action)
for other in rig.animation_data.nla_tracks:
    other.mute = other != track
for obj in scene.objects:
    if obj == rig:
        continue
    for owner in (obj, obj.data.shape_keys if obj.type == 'MESH' else None):
        if owner is None or not owner.animation_data:
            continue
        standing_track = next((t for t in owner.animation_data.nla_tracks if t.name == 'Standing'), None)
        if standing_track:
            owner.animation_data.action = None
            new_track = owner.animation_data.nla_tracks.new()
            new_track.name = 'Cast_FireBolt'
            new_track.strips.new('Cast_FireBolt', 0, standing_track.strips[0].action)
            for old_track in owner.animation_data.nla_tracks:
                old_track.mute = old_track != new_track

# Bone-relative empties become named glTF nodes without adding skin joints or vertex influences.
socket_points = {
    'Socket_Eye_Left': ('mixamorig:Head', eye_points['Left']),
    'Socket_Eye_Right': ('mixamorig:Head', eye_points['Right']),
}
for side in ('Left', 'Right'):
    hand = rig.data.bones['mixamorig:' + side + 'Hand']
    bases = [rig.data.bones['mixamorig:' + side + 'Hand' + d + '1'].head_local
             for d in ('Index', 'Middle', 'Pinky', 'Ring')]
    socket_points['Socket_Palm_' + side] = (hand.name, hand.head_local.lerp(sum(bases, Vector()) / 4, .7))
scene.frame_set(0)
for name, (bone_name, rest_point) in socket_points.items():
    obj = bpy.data.objects.new(name, None)
    scene.collection.objects.link(obj)
    obj.parent = rig
    obj.parent_type = 'BONE'
    obj.parent_bone = bone_name
    # Blender's bone-parent origin is its tail, glTF's exported parent node is its head.
    parent = rig.data.bones[bone_name]
    obj.matrix_basis = Matrix.Translation((parent.matrix_local.inverted() @ rest_point) - Vector((0, parent.length, 0)))
    obj.empty_display_type = 'SPHERE'
    obj.empty_display_size = .015
    obj['socket_role'] = name.removeprefix('Socket_').lower()
for obj in scene.objects:
    obj.select_set(obj in [rig, mesh] or obj.name in socket_points)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(stage / 'cast_export.glb'), export_format='GLB', use_selection=True,
    use_active_scene=True, export_animations=True, export_animation_mode='NLA_TRACKS',
    export_frame_range=False, export_force_sampling=True, export_all_influences=True,
    export_def_bones=False, export_optimize_animation_size=False, export_extras=True,
    export_cameras=False, export_lights=False)
# Preserve all original clips in the editable master and leave the new action selected for review.
scene.frame_set(24)
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'mm6_demon_animation_master.blend'), compress=True)
print('Saved master plus casting export; existing anatomy, UVs, materials and native clips unchanged.', flush=True)
