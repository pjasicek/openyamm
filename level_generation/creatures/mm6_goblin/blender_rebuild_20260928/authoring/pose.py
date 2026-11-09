"""Portable poses from short analytical limb solves; no runtime constraints or external rig."""
import json
import math

import bpy
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

from mesh_tools import ROOT

MARKS = {key: Vector(value) for key, value in json.loads((ROOT / 'authoring/landmarks.json').read_text()).items()
         if not isinstance(value[0], list)}
GRIP = json.loads((ROOT / 'authoring/grip_angles.json').read_text()) if (ROOT / 'authoring/grip_angles.json').exists() else {}
WEAPON = json.loads((ROOT / 'authoring/weapon.json').read_text())


def rig():
    return bpy.data.objects['GB15 Goblin rig']


def update():
    bpy.context.view_layer.update()


def reset():
    for bone in rig().pose.bones:
        bone.matrix_basis = Matrix.Identity(4)
    update()


def local(name, xyz):
    from mathutils import Euler
    rig().pose.bones[name].rotation_quaternion = Euler(tuple(math.radians(v) for v in xyz), 'XYZ').to_quaternion()
    update()


def aim(name, direction, twist=0):
    arm = rig()
    bone = arm.pose.bones[name]
    head = bone.head.copy()
    rest = bone.bone.matrix_local.to_quaternion()
    wanted = Vector(direction).normalized()
    rot = (rest @ Vector((0, 1, 0))).rotation_difference(wanted) @ rest
    if twist:
        rot = Quaternion(wanted, math.radians(twist)) @ rot
    bone.matrix = Matrix.Translation(head) @ rot.to_matrix().to_4x4()
    update()


def aim_in_hand(name, direction, hand_name):
    arm = rig()
    pb, hand = arm.pose.bones[name], arm.pose.bones[hand_name]
    relative = hand.bone.matrix_local.to_quaternion().inverted() @ pb.bone.matrix_local.to_quaternion()
    wanted = hand.matrix.to_quaternion().inverted() @ Vector(direction).normalized()
    rotation = hand.matrix.to_quaternion() @ ((relative @ Vector((0, 1, 0))).rotation_difference(wanted) @ relative)
    pb.matrix = Matrix.Translation(pb.head) @ rotation.to_matrix().to_4x4()
    update()


def limb(first, second, target, pole, hinge=False):
    arm = rig()
    a = arm.pose.bones[first].head.copy()
    length_a, length_b = arm.data.bones[first].length, arm.data.bones[second].length
    direction = Vector(target) - a
    distance = max(.015, min(direction.length, (length_a + length_b) * .998))
    direction.normalize()
    x = (distance * distance + length_a * length_a - length_b * length_b) / (2 * distance)
    y = math.sqrt(max(.000001, length_a * length_a - x * x))
    pole = Vector(pole) - a
    normal = (pole - direction * pole.dot(direction)).normalized()
    knee = a + direction * x + normal * y
    tip = a + direction * distance
    if hinge:
        # Rotate the entire rest bend plane with the limb. Independent segment aiming
        # can turn elbow flexion into sideways/backward bending of the skinned joint.
        rest_a, rest_b = arm.data.bones[first], arm.data.bones[second]
        rest_upper = (rest_a.tail_local - rest_a.head_local).normalized()
        rest_lower = (rest_b.tail_local - rest_b.head_local).normalized()
        rest_axis = rest_upper.cross(rest_lower).normalized()
        upper, lower = (knee - a).normalized(), (tip - knee).normalized()
        axis = upper.cross(lower).normalized()
        rest_frame = Matrix((rest_axis, rest_upper, rest_axis.cross(rest_upper))).transposed()
        frame = Matrix((axis, upper, axis.cross(upper))).transposed()
        swing = (frame @ rest_frame.transposed()).to_quaternion()
        upper_rotation = swing @ rest_a.matrix_local.to_quaternion()
        lower_rotation = (Quaternion(axis, upper.angle(lower) - rest_upper.angle(rest_lower))
                          @ swing @ rest_b.matrix_local.to_quaternion())
        arm.pose.bones[first].matrix = Matrix.Translation(a) @ upper_rotation.to_matrix().to_4x4()
        update()
        bone = arm.pose.bones[second]
        bone.matrix = Matrix.Translation(bone.head) @ lower_rotation.to_matrix().to_4x4()
        update()
    else:
        aim(first, knee - a)
        aim(second, tip - knee)
    return tip


def set_hand_rotation(suffix, rotation):
    """Distribute pronation through the distal forearm, then place the hand explicitly."""
    arm = rig()
    forearm = arm.pose.bones['forearm' + suffix]
    twist = arm.pose.bones['forearm_twist' + suffix]
    axis = forearm.vector.normalized()
    dorsal = forearm.matrix.to_quaternion() @ Vector((0, 0, 1))
    target = rotation.to_quaternion() @ Vector((0, 0, 1))
    dorsal = (dorsal - axis * dorsal.dot(axis)).normalized()
    target = (target - axis * target.dot(axis)).normalized()
    angle = math.atan2(axis.dot(dorsal.cross(target)), dorsal.dot(target))
    twist_rotation = Quaternion(axis, angle) @ forearm.matrix.to_quaternion()
    twist.matrix = Matrix.Translation(twist.head) @ twist_rotation.to_matrix().to_4x4()
    update()
    hand = arm.pose.bones['hand' + suffix]
    hand.matrix = Matrix.Translation(hand.head) @ rotation
    update()


def free_hand(suffix='.L', palm=(-1, 0, 0), direction=None):
    """A hanging hand has its palm toward the hip and its thumb toward the front."""
    y = Vector(direction) if direction is not None else rig().pose.bones['forearm' + suffix].vector.copy()
    y.normalize()
    z = -Vector(palm)
    z = (z - y * z.dot(y)).normalized()
    x = y.cross(z).normalized()
    set_hand_rotation(suffix, Matrix((x, y, z)).transposed().to_4x4())
    relaxed_thumb(suffix)


def relaxed_thumb(suffix='.L'):
    """Oppose the resting thumb slightly into the palm, with a soft distal curl."""
    hand = rig().pose.bones['hand' + suffix]
    side = 1 if suffix == '.L' else -1
    for index, direction in enumerate([(.62, .70, -.35), (.08, .98, -.18), (-.30, .94, -.16)]):
        local_direction = Vector((direction[0] * side, direction[1], direction[2]))
        world_direction = hand.matrix.to_3x3() @ local_direction
        aim_in_hand(f'thumb{suffix}.{index + 1:02}', world_direction, 'hand' + suffix)


def hand_orientation(suffix, blade=(0, -1, 0), down=(0, 0, -1), bank=0, edge=None, edge_weight=1):
    # Sword exits the index/thumb end of the right hand, opposite local X.
    x = -Vector(blade).normalized() if suffix == '.R' else Vector(blade).normalized()
    y = Vector(down)
    y = (y - x * y.dot(x)).normalized()
    z = x.cross(y).normalized()
    y = z.cross(x).normalized()
    rot = Matrix((x, y, z)).transposed().to_4x4()
    if suffix == '.R':
        arm = rig()
        weapon = arm.data.bones['weapon.R']
        local_axis = arm.data.bones['hand.R'].matrix_local.inverted().to_3x3() @ (weapon.tail_local - weapon.head_local)
        correction = local_axis.normalized().rotation_difference(Vector((-1, 0, 0)))
        rot = rot @ correction.to_matrix().to_4x4()
    if bank:
        rot = rot @ Quaternion((0, 1, 0), math.radians(bank)).to_matrix().to_4x4()
    if suffix == '.R' and edge is not None:
        axis = Vector(blade).normalized()
        local_edge = rig().data.bones['hand.R'].matrix_local.inverted().to_3x3() @ Vector(WEAPON['broad'])
        current_edge = rot.to_3x3() @ local_edge
        current_edge = (current_edge - axis * current_edge.dot(axis)).normalized()
        wanted = Vector(edge)
        wanted = (wanted - axis * wanted.dot(axis)).normalized()
        angle = math.atan2(axis.dot(current_edge.cross(wanted)), current_edge.dot(wanted))
        rot = Quaternion(axis, angle * edge_weight).to_matrix().to_4x4() @ rot
    set_hand_rotation(suffix, rot)


def chest_rotation():
    chest = rig().pose.bones['chest']
    return chest.matrix.to_quaternion() @ chest.bone.matrix_local.to_quaternion().inverted()


def swing_arm(suffix, swing, bend=24, spread=18):
    """A shoulder-led pendulum, with a soft elbow bend in the same anatomical plane."""
    side = 1 if suffix == '.L' else -1
    outward = math.sin(math.radians(spread))
    vertical = math.cos(math.radians(spread))
    chest = chest_rotation()
    for name, angle in [('upper_arm', swing), ('forearm', swing + bend)]:
        a = math.radians(angle)
        direction = chest @ Vector((side * outward, -math.sin(a) * vertical, -math.cos(a) * vertical))
        aim(name + suffix, direction)


def grip(suffix='.R', strength=1):
    arm = rig()
    for finger in range(4):
        for index, angle in enumerate(GRIP[str(finger)]['degrees'] if GRIP else [71 + finger * 2, 94, 65]):
            pb = arm.pose.bones[f'digit{suffix}.{finger}.{index + 1:02}']
            # Local +Z is dorsal: negative X flexes toward the actual palm.
            pb.rotation_quaternion = Quaternion((1, 0, 0), math.radians(-angle * strength))
    update()
    if strength <= .01:
        return
    if suffix == '.R' and strength > .99:
        hand_matrix = arm.pose.bones['hand.R'].matrix
        center = hand_matrix.inverted() @ arm.pose.bones['weapon.R'].head
        tip = center + Vector((-.014, -.009, -.024))
        final_direction = Vector((.85, -.25, .12)).normalized()
        joint = tip - final_direction * arm.data.bones['thumb.R.03'].length
        limb('thumb.R.01', 'thumb.R.02', hand_matrix @ joint,
             hand_matrix @ Vector((-.075, .043, -.080)))
        directions = [arm.pose.bones['thumb.R.' + str(i).zfill(2)].vector.copy() for i in [1, 2]]
        directions.append(hand_matrix.to_3x3() @ final_direction)
        for index, direction in enumerate(directions):
            aim_in_hand('thumb.R.' + str(index + 1).zfill(2), direction, 'hand.R')
        return
    transform = (arm.pose.bones['hand' + suffix].matrix @ arm.data.bones['hand' + suffix].matrix_local.inverted())
    wrist = MARKS['wrist' + suffix]
    down = (MARKS['hand_end' + suffix] - wrist).normalized()
    across = down.cross(Vector((0, -1, 0))).normalized()
    if suffix == '.L':
        across = -across
    front = Vector((0, 1, 0))
    vectors = [down * .83 + front * .48 + across * .17,
               across * .86 + down * .23 + front * .34,
               across * .80 - down * .25 - front * .18]
    for index, vector in enumerate(vectors):
        name = f'thumb{suffix}.{index + 1:02}'
        desired = transform.to_3x3() @ vector
        current = arm.pose.bones[name].vector.normalized()
        aim(name, current.lerp(desired.normalized(), strength))


def foot(suffix, ankle, angle=0):
    limb('thigh' + suffix, 'shin' + suffix, ankle,
         (MARKS['hip' + suffix].x, -.5, .5))
    direction = MARKS['toe_end' + suffix] - MARKS['ankle' + suffix]
    aim('foot' + suffix, Quaternion((1, 0, 0), math.radians(angle)) @ direction)


def foot_contact_offset(suffix, angle):
    """Roll the actual sole around its lowest contact point, with a 2 mm floor clearance."""
    rotation = Quaternion((1, 0, 0), math.radians(angle))
    points = []
    for obj in bpy.data.collections['GB15 Character'].objects:
        if obj.type != 'MESH' or 'foot' + suffix not in obj.vertex_groups:
            continue
        group = obj.vertex_groups['foot' + suffix].index
        points.extend(vertex.co - MARKS['ankle' + suffix] for vertex in obj.data.vertices
                      if any(g.group == group and g.weight > .999 for g in vertex.groups))
    contact = min(points, key=lambda point: (rotation @ point).z)
    rotated = rotation @ contact
    return contact.y - rotated.y, .002 - rotated.z


def skirt(left_swing=0, right_swing=0, crouch=0):
    for index in range(17):
        angle = index * math.tau / 17
        swing = left_swing if math.sin(angle) > 0 else right_swing
        front = math.cos(angle)
        radial = max(0, swing * front) * .70 + crouch * (.40 + .6 * abs(front))
        axis = Vector((math.cos(angle), math.sin(angle), 0))
        pb = rig().pose.bones[f'skirt.{index:02}']
        world_rotation = Quaternion(axis, math.radians(-radial))
        rest_rotation = pb.bone.matrix_local.to_quaternion()
        pb.rotation_quaternion = rest_rotation.inverted() @ world_rotation @ rest_rotation
    update()
    fit_skirt()
    armor_follow()


def armor_follow():
    """Smooth shoulder attachment; clearance is calibrated across clips, never stepped per frame."""
    arm = rig()
    chest_delta = chest_rotation()
    for suffix in ['.L', '.R']:
        upper = arm.pose.bones['upper_arm' + suffix]
        pb = arm.pose.bones['pauldron' + suffix]
        direction = chest_delta.inverted() @ upper.vector.normalized()
        rest_direction = (upper.bone.tail_local - upper.bone.head_local).normalized()
        swing = rest_direction.rotation_difference(direction)
        # Follow elevation without inheriting the humerus's axial roll.
        follow = chest_delta @ Quaternion().slerp(swing, .5)
        rotation = follow @ pb.bone.matrix_local.to_quaternion()
        elevation = max(0, min(1, (direction.z + .95) / 1.65))
        lift = .035 + .012 * elevation * elevation * (3 - 2 * elevation)
        outward = follow @ Vector((0, 0, 1))
        pb.matrix = Matrix.Translation(upper.head + outward * lift) @ rotation.to_matrix().to_4x4()
    update()


def fit_skirt():
    """Choose the smallest extra flare that clears the posed body at strip rows and width samples."""
    arm = rig()
    skin = bpy.data.objects['GB15 Skin body']
    tree = BVHTree.FromObject(skin, bpy.context.evaluated_depsgraph_get())
    panels = bpy.data.objects['GB15 Leather skirt strips']
    pelvis = arm.pose.bones['pelvis']
    pelvis_deform = pelvis.matrix @ pelvis.bone.matrix_local.inverted()
    for index in range(17):
        pb = arm.pose.bones[f'skirt.{index:02}']
        relative = pelvis.bone.matrix_local.inverted() @ pb.bone.matrix_local
        rest = pb.bone.matrix_local.to_quaternion()
        axis = Vector((math.cos(index * math.tau / 17), math.sin(index * math.tau / 17), 0))
        base = pb.rotation_quaternion.copy()
        best = base
        for added in range(0, 70, 3):
            q = base @ (rest.inverted() @ Quaternion(axis, math.radians(-added)) @ rest)
            deform = pelvis.matrix @ relative @ q.to_matrix().to_4x4() @ pb.bone.matrix_local.inverted()
            clear = True
            for row in range(1, 5):
                weight = min(1, row * .65)
                for col in range(3):
                    point = panels.data.vertices[index * 30 + row * 6 + col].co
                    posed = (pelvis_deform @ point) * (1 - weight) + (deform @ point) * weight
                    hit, normal, face, distance = tree.find_nearest(posed)
                    if hit is not None and (posed - hit).dot(normal) < .005:
                        clear = False
                        break
                if not clear:
                    break
            best = q
            if clear:
                break
        pb.rotation_quaternion = best
    update()


def standing(time=0):
    reset()
    breath = math.sin(time * math.tau)
    arm = rig()
    arm.pose.bones['pelvis'].location = arm.data.bones['pelvis'].matrix_local.to_quaternion().inverted() @ \
        Vector((0, 0, -.025))
    local('spine', (1.5 + breath * .6, 0, 0))
    local('chest', (-1.5, 0, 0))
    local('head', (0, 0, 0))
    for suffix in ['.L', '.R']:
        foot(suffix, MARKS['ankle' + suffix])
    limb('upper_arm.R', 'forearm.R', (-.287, -.116, .986), (-.44, .015, 1.11))
    hand_orientation('.R', (.08, -.995, .035))
    grip()
    limb('upper_arm.L', 'forearm.L', (.315, -.032, .880), (.32, .025, 1.09))
    for index in range(4):
        for joint in range(3):
            arm.pose.bones[f'digit.L.{index}.{joint + 1:02}'].rotation_quaternion = \
                Quaternion((1, 0, 0), math.radians(-[15, 22, 16][joint]))
    free_hand()
    skirt()
    update()


if __name__ == '__main__':
    standing()
