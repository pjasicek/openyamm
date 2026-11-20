"""Posing helpers shared by stress tests and animation authoring (run inside Blender)."""
import bpy, math
from mathutils import Matrix, Vector, Quaternion

FINGERS = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')


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


def rotate_local(rig, name, axis, degrees):
    bone = pb(rig, name)
    bone.rotation_mode = 'QUATERNION'
    q = Quaternion(Vector({'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}[axis]), math.radians(degrees))
    bone.rotation_quaternion = bone.rotation_quaternion @ q
    bpy.context.view_layer.update()


def curl_hand(rig, side, curl, thumb=None, spread=0.0):
    """Flex every finger joint by `curl` degrees about the bone's local X (positive = toward the palm)."""
    for finger in FINGERS:
        amount = (thumb if thumb is not None else curl * 0.5) if finger == 'Thumb' else curl
        for k in (1, 2, 3):
            name = f'{side}Hand{finger}{k}'
            if 'mixamorig:' + name in rig.pose.bones:
                rotate_local(rig, name, 'X', amount * (0.8 if k == 1 else 1.0))


def bone_world(rig, name, tail=False):
    bone = pb(rig, name)
    return rig.matrix_world @ (bone.tail if tail else bone.head)


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


def two_bone_ik_hinge(rig, upper, lower, target, pole):
    """Two-bone IK where the lower bone only flexes about its rest-relative local X (anatomical elbow hinge).

    The upper bone is aimed at the pole-plane elbow position, then rolled about its own axis together with the
    flexion angle so the lower bone points at the target. Leaves no spurious forearm roll for the wrist to undo.
    """
    elbow = two_bone_ik(rig, upper, lower, target, pole)
    ub = pb(rig, upper); lb = pb(rig, lower)
    inv = rig.matrix_world.inverted()
    rest_rel = ub.bone.matrix_local.inverted() @ lb.bone.matrix_local
    U0 = ub.matrix.copy()
    head = ub.head.copy()
    axis = (ub.tail - ub.head).normalized()
    desired = (inv @ Vector(target) - (inv @ elbow)).normalized()

    def lower_matrix(rho, phi):
        U = Matrix.Translation(head) @ Matrix.Rotation(rho, 4, axis) @ Matrix.Translation(-head) @ U0
        return U, U @ rest_rel @ Matrix.Rotation(phi, 4, 'X')

    def error(rho, phi):
        return lower_matrix(rho, phi)[1].col[1].xyz.normalized().angle(desired)

    best = min(((error(math.radians(r), math.radians(p)), math.radians(r), math.radians(p))
                for r in range(-180, 180, 6) for p in range(-30, 165, 6)), key=lambda x: x[0])
    _, rho, phi = best
    step = math.radians(3)
    while step > math.radians(0.05):
        cur = error(rho, phi)
        cand = min(((error(rho + dr, phi + dp), rho + dr, phi + dp)
                    for dr in (-step, 0, step) for dp in (-step, 0, step)), key=lambda x: x[0])
        if cand[0] >= cur - 1e-9:                    # no strict improvement (also ties): refine, never cycle
            step *= 0.5
            continue
        _, rho, phi = cand
    U, L = lower_matrix(rho, phi)
    ub.matrix = U
    bpy.context.view_layer.update()
    lb.matrix = L
    bpy.context.view_layer.update()
    return elbow
