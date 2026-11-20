"""MM6 Rat posing helpers used by this quadruped rig."""
import bpy, math
from mathutils import Matrix, Vector

def pb(rig, name):
    return rig.pose.bones[name if name in rig.pose.bones else 'mixamorig:' + name]

def reset(rig):
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.location = (0, 0, 0)
        bone.scale = (1, 1, 1)
    bpy.context.view_layer.update()

def rotate_world(rig, name, axis, degrees, pivot=None):
    """Rotate a bone about a world-space axis through its head (armature without object rotation)."""
    bone = pb(rig, name)
    axis = Vector(axis).normalized() if not isinstance(axis, str) else Vector(
        {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}[axis])
    head = bone.head.copy() if pivot is None else Vector(pivot)
    R = Matrix.Translation(head) @ Matrix.Rotation(math.radians(degrees), 4, axis) @ Matrix.Translation(-head)
    bone.matrix = R @ bone.matrix
    bpy.context.view_layer.update()

def aim_bone(rig, name, target, roll_hint=None):
    """Rotate bone (world-space, around its head) so its tail points at target."""
    bone = pb(rig, name)
    current = (bone.tail - bone.head).normalized()
    desired = (Vector(target) - (rig.matrix_world @ bone.head)).normalized()
    q = current.rotation_difference(desired)
    head = bone.head.copy()
    bone.matrix = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ bone.matrix
    bpy.context.view_layer.update()

def two_bone_ik(rig, upper, lower, target, pole):
    """Analytic two-bone IK in world space: place the end of `lower` at target, elbow toward pole."""
    a = pb(rig, upper); b = pb(rig, lower)
    shoulder = rig.matrix_world @ a.head
    la = (a.tail - a.head).length; lb = (b.tail - b.head).length
    target = Vector(target); pole = Vector(pole)
    d = target - shoulder
    dist = min(d.length, (la + lb) * 0.999)
    d = d.normalized()
    cos_a = (la * la + dist * dist - lb * lb) / (2 * la * dist)
    angle = math.acos(max(-1.0, min(1.0, cos_a)))
    pole_dir = (pole - shoulder)
    pole_dir = (pole_dir - d * pole_dir.dot(d)).normalized()
    elbow = shoulder + (d * math.cos(angle) + pole_dir * math.sin(angle)) * la
    aim_bone(rig, upper, elbow)
    aim_bone(rig, lower, shoulder + d * dist)
    return elbow
