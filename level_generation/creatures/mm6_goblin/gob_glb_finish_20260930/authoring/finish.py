"""Finish the supplied goblin without changing its source GLB or UV layout."""
import bpy
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'inputs/gob_source.glb'
REVIEW = ROOT / 'review'
scene = bpy.context.scene
scene.render.fps = 48
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
body = next(o for o in scene.objects if o.type == 'MESH' and o.find_armature() == rig)
rig.name = 'MM6 Goblin Rig'
body.name = 'MM6 Goblin Body'
scene.name = 'MM6 Goblin Finished'
source_actions = {a.name: a for a in bpy.data.actions}
for track in rig.animation_data.nla_tracks:
    track.mute = True
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
    pb.custom_shape = None
for o in scene.objects:
    if o.type == 'MESH' and o != body:
        o.hide_render = True
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name, parent in [('Bone_050', 'mixamorig:LeftShoulder'), ('Bone_045', 'mixamorig:RightShoulder')]:
    rig.data.edit_bones[name].parent = rig.data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()
rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
source_positions = np.array([v.co[:] for v in body.data.vertices])
original_weights = [{body.vertex_groups[g.group].name: g.weight for g in v.groups} for v in body.data.vertices]

# Classify the painted metal on the unchanged UVs; skin is strongly yellow/green.
bsdf = next(n for n in body.data.materials[0].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
color_node = bsdf.inputs['Base Color'].links[0].from_node
image = color_node.image
pixels = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
image.pixels.foreach_get(pixels)
pixels = pixels.reshape(image.size[1], image.size[0], 4)
uv = np.zeros((len(body.data.vertices), 2))
for loop in body.data.loops:
    uv[loop.vertex_index] = body.data.uv_layers.active.data[loop.index].uv
ix = np.clip(np.round(uv[:, 0] * (image.size[0] - 1)).astype(int), 0, image.size[0] - 1)
iy = np.clip(np.round(uv[:, 1] * (image.size[1] - 1)).astype(int), 0, image.size[1] - 1)
rgb = pixels[iy, ix, :3]
metal = (rgb.max(1) - rgb.min(1) < .19) & (rgb[:, 2] > rgb[:, 0] * .80) & (rgb.mean(1) < .62)
head_names = {b.name for b in rig.data.bones if b.name == 'mixamorig:Head' or
              'mixamorig:Head' in [p.name for p in b.parent_recursive]}
changed_weights = {'head_consolidated': 0, 'toe_consolidated': 0, 'armor_rigid': 0,
                   'right_palm_repaired': 0, 'limited_to_four': 0}
right_hand_inverse = rest['mixamorig:RightHand'].inverted()
groups = {g.name: g for g in body.vertex_groups}
for vertex, old in zip(body.data.vertices, original_weights):
    w = old.copy()
    head = sum(w.pop(n, 0) for n in head_names)
    if head:
        w['mixamorig:Head'] = w.get('mixamorig:Head', 0) + head
        changed_weights['head_consolidated'] += 1
    for side in ['Left', 'Right']:
        toe = sum(w.pop('mixamorig:' + side + n, 0) for n in ['ToeBase', 'Toe_End'])
        if toe:
            name = 'mixamorig:' + side + 'Foot'
            w[name] = w.get(name, 0) + toe
            changed_weights['toe_consolidated'] += 1
    p = vertex.co
    # Keep shoulder/back plate sections and forearm bracers from shearing like skin.
    if metal[vertex.index] and 1.15 < p.z < 1.48:
        name = 'mixamorig:Spine2' if abs(p.x) < .155 else 'mixamorig:' + ('Left' if p.x > 0 else 'Right') + 'Shoulder'
        w = {name: 1.0}
        changed_weights['armor_rigid'] += 1
    elif metal[vertex.index] and .82 < p.z < 1.18 and abs(p.x) > .32:
        name = 'mixamorig:' + ('Left' if p.x > 0 else 'Right') + 'ForeArm'
        w = {name: 1.0}
        changed_weights['armor_rigid'] += 1
    # The palm/fingers form one closed grip. Forearm weights on their distal
    # vertices collapsed the palm when the wrist rotated. Confine the wrist
    # blend to its anatomical joint; retain finger groups for open-hand posing.
    hp = right_hand_inverse @ p
    hand_weights = {n: v for n, v in w.items() if n.startswith('mixamorig:RightHand')}
    hand_total = sum(hand_weights.values())
    if hand_total > .001 and -.025 < hp.y and abs(hp.x) < .105 and abs(hp.z) < .105:
        t = min(1, max(0, (hp.y+.025)/.055))
        t = t*t*(3-2*t)
        t = max(t, hand_total)
        w = {n: v*t/hand_total for n, v in hand_weights.items()}
        if t < 1:
            w['mixamorig:RightForeArm'] = 1-t
        changed_weights['right_palm_repaired'] += 1
    if len([x for x in w.values() if x > 1e-6]) > 4:
        changed_weights['limited_to_four'] += 1
    w = sorted(w.items(), key=lambda x: -x[1])[:4]
    total = sum(value for _, value in w)
    for group in vertex.groups[:]:
        body.vertex_groups[group.group].remove([vertex.index])
    for name, value in w:
        if value > 1e-7:
            groups[name].add([vertex.index], value / total, 'REPLACE')

# Repair the left outer claw with a small, smoothly blended rest-mesh rotation.
# It remains on the original UV island and follows the now-stable foot transform.
toe_pivot = Vector((.220, -.115, .037))
toe_angle = math.radians(-12)
toe_repair_count = 0
for v in body.data.vertices:
    p = v.co.copy()
    if p.x <= .205 or p.y >= -.125 or p.z >= .070:
        continue
    blend = min(1, max(0, (p.x - .205) / .025)) * min(1, max(0, (-p.y - .125) / .045))
    if blend:
        v.co = p.lerp(toe_pivot + Quaternion((0, 0, 1), toe_angle) @ (p - toe_pivot), blend)
        toe_repair_count += 1
body.data.update()

# Derive the grip basis from this rig's own knuckles, rather than the earlier model.
HAND = 'mixamorig:RightHand'
hand_rest = rest[HAND]
hand_inv = hand_rest.inverted()
index = hand_inv @ rig.data.bones['mixamorig:RightHandIndex1'].head_local
pinky = hand_inv @ rig.data.bones['mixamorig:RightHandPinky1'].head_local
long_axis = Vector((0, 1, 0))
width = index - pinky
width -= long_axis * width.dot(long_axis)
width.normalize()
bend = width.cross(long_axis).normalized()
knuckles = [hand_inv @ rig.data.bones['mixamorig:RightHand' + f + '1'].head_local
            for f in ['Index', 'Middle', 'Ring', 'Pinky']]
grip_local = sum(knuckles, Vector()) / 4 + bend * .024
sword_basis = Matrix((bend, width, long_axis)).transposed()
grip_rotations = {}
for finger in ['Index', 'Middle', 'Ring', 'Pinky', 'Thumb']:
    for part in range(1, 5):
        name = 'mixamorig:RightHand' + finger + str(part)
        grip_rotations[name] = Quaternion()

# The generated hand lacks sufficient joint loops for a tight skeletal fist.
# A volume-preserving centerline bend makes the armed grip reversible and keeps
# the native UVs. Reset this key to zero when authoring an open hand with fingers.
body.shape_key_add(name='Basis')
grip_key = body.shape_key_add(name='SwordGrip')
finger_chains = {}
for finger in ['Index', 'Middle', 'Ring', 'Pinky', 'Thumb']:
    points = [hand_inv @ rig.data.bones['mixamorig:RightHand' + finger + str(k)].head_local for k in range(1, 5)]
    lengths = [(b - a).length for a, b in zip(points, points[1:])]
    finger_chains[finger] = (points, lengths)
grip_vertices = 0
for vertex, dest in zip(body.data.vertices, grip_key.data):
    total = sum(value for name, value in original_weights[vertex.index].items()
                if name.startswith('mixamorig:RightHand'))
    if total < .55:
        continue
    p = hand_inv @ vertex.co
    candidates = []
    for finger, (points, lengths) in finger_chains.items():
        passed = 0
        for a, b, length in zip(points, points[1:], lengths):
            tangent = (b - a).normalized()
            distance = (p - a).dot(tangent)
            u = max(0, min(length, distance))
            center = a + tangent * u
            candidates.append(((p - center).length, finger, passed + u, center, tangent, distance))
            passed += length
    _, finger, travel, original_center, original_tangent, along = min(candidates, key=lambda x: x[0])
    points, lengths = finger_chains[finger]
    if travel <= .001 or (travel < .004 and along < 0):
        continue
    root = points[0]
    if finger == 'Thumb':
        t = min(1, travel / sum(lengths))
        end = grip_local + width * .033 + bend * .010
        a = root
        b = root + (points[1] - root).normalized() * .026
        c = end - (end - root).normalized() * .023
        d = end
        center = a * (1-t)**3 + b * (3*(1-t)**2*t) + c * (3*(1-t)*t*t) + d * t**3
        tangent = ((b-a)*3*(1-t)**2 + (c-b)*6*(1-t)*t + (d-c)*3*t*t).normalized()
    else:
        long = (points[1] - root).normalized()
        curl = width.cross(long).normalized()
        radius = .027
        theta = travel / radius
        center = root + long * radius * math.sin(theta) + curl * radius * (1-math.cos(theta))
        tangent = (long * math.cos(theta) + curl * math.sin(theta)).normalized()
    delta = p - original_center
    rotation = original_tangent.rotation_difference(tangent)
    q = center + rotation @ delta
    blend = min(1, travel / .012)
    blend = blend * blend * (3 - 2*blend)
    dest.co = vertex.co.lerp(hand_rest @ q, blend)
    grip_vertices += 1
grip_key.value = 1

def apply_grip():
    for name, q in grip_rotations.items():
        pb = rig.pose.bones[name]
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = q

# Keep the imported body motion; replace finger curves with a constant armed grip.
for action in source_actions.values():
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in list(bag.fcurves):
                    if any(fc.data_path.startswith('pose.bones["' + name + '"]') for name in grip_rotations):
                        bag.fcurves.remove(fc)
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    apply_grip()
    for frame in action.frame_range:
        for name in grip_rotations:
            rig.pose.bones[name].keyframe_insert('rotation_quaternion', frame=frame, group=name)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
apply_grip()

def material(name, color, metallic, roughness):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Metallic'].default_value = metallic
    bs.inputs['Roughness'].default_value = roughness
    return m

steel = material('Sword worn warm steel', (.31, .29, .25), .75, .37)
edge = material('Sword sharpened edge', (.58, .55, .47), .80, .28)
gold = material('Sword aged gold hilt', (.48, .27, .06), .75, .40)
leather = material('Sword dark leather grip', (.035, .014, .006), 0, .72)
sword_matrix = hand_rest @ Matrix.Translation(grip_local) @ sword_basis.to_4x4()
sword_objects = []

def part(name, verts, faces, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([sword_matrix @ Vector(v) for v in verts], [], faces)
    mesh.materials.append(mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.parent = rig
    group = obj.vertex_groups.new(name=HAND)
    group.add(list(range(len(mesh.vertices))), 1, 'REPLACE')
    mod = obj.modifiers.new('Sword follows gripping hand', 'ARMATURE')
    mod.object = rig
    sword_objects.append(obj)
    return obj

def tube(name, points, radius, mat, sides=8):
    points = [Vector(p) for p in points]
    verts, faces = [], []
    for i, p in enumerate(points):
        tangent = (points[min(i + 1, len(points) - 1)] - points[max(0, i - 1)]).normalized()
        u = tangent.cross(Vector((1, 0, 0)))
        if u.length < .01:
            u = tangent.cross(Vector((0, 0, 1)))
        u.normalize()
        v = tangent.cross(u)
        for j in range(sides):
            a = j * math.tau / sides
            verts.append(p + radius * (math.cos(a) * u + math.sin(a) * v))
    for i in range(len(points) - 1):
        for j in range(sides):
            a = i * sides + j
            b = i * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces += [tuple(reversed(range(sides))), tuple((len(points) - 1) * sides + j for j in range(sides))]
    ob = part(name, verts, faces, mat)
    for f in ob.data.polygons:
        f.use_smooth = True
    return ob

verts, faces = [], []
sections = 17
for i in range(sections):
    t = i / (sections - 1)
    y = .072 + .675 * t
    z = .015 * t * t + .102 * t ** 5
    half = max(.0006, (.022 + .022 * math.sin(math.pi * t)) * (1 - t ** 9))
    thick = .0032 * (1 - .8 * t * t)
    verts += [(0, y, z - half), (thick, y, z - half * .70), (thick, y, z + half * .70),
              (0, y, z + half), (-thick, y, z + half * .70), (-thick, y, z - half * .70)]
for i in range(sections - 1):
    for j in range(6):
        a = i * 6 + j
        b = i * 6 + (j + 1) % 6
        faces.append((a, b, b + 6, a + 6))
faces += [tuple(reversed(range(6))), tuple((sections - 1) * 6 + j for j in range(6))]
blade = part('Goblin curved blade', verts, [tuple(reversed(f)) for f in faces], steel)
blade.data.materials.append(edge)
for i, f in enumerate(blade.data.polygons):
    f.material_index = int(i % 6 in [0, 5])
tube('Sword wrapped grip', [(0, -.065, 0), (0, .065, 0)], .019, leather, 12)
tube('Sword pommel', [(0, -.079, 0), (0, -.067, 0)], .023, gold, 10)
tube('Sword ferrule', [(0, .058, 0), (0, .076, 0)], .022, gold, 10)
tube('Sword swept crossguard', [(0, .065, -.069), (0, .077, -.060), (0, .083, -.025),
                              (0, .079, .026), (0, .062, .061), (0, .046, .067)], .006, gold)
tube('Sword knuckle bow', [(0, -.068, 0), (.008, -.064, -.047), (.014, -.040, -.070),
                         (.014, .025, -.072), (.007, .069, -.055)], .004, gold)

# Six native pose starts, plus the exact idle endpoint at 0.75 seconds.
KEYS = [
    (0.000, dict(twist=0, lean=2, r=(-.28, -.22, 1.02), l=(.28, -.04, .87), d=(.83, -.20, .52), lift=0)),
    (0.125, dict(twist=30, lean=-3, r=(.15, -.27, 1.26), l=(.23, -.20, 1.07), d=(.56, -.12, .82), lift=.055)),
    (0.250, dict(twist=16, lean=0, r=(.13, -.29, 1.28), l=(.18, -.28, 1.14), d=(.49, -.18, .85), lift=.055)),
    (0.375, dict(twist=-10, lean=5, r=(-.28, -.30, 1.13), l=(.03, -.27, 1.02), d=(.83, -.25, -.49), lift=.012)),
    (0.500, dict(twist=-25, lean=13, r=(-.38, -.26, 1.00), l=(-.02, -.25, .90), d=(-.97, -.20, -.15), lift=0)),
    (0.625, dict(twist=-6, lean=5, r=(-.29, -.22, .98), l=(.24, -.10, .86), d=(.36, -.30, -.88), lift=0)),
]
KEYS.append((.75, KEYS[0][1].copy()))

def interpolate(t):
    for (ta, a), (tb, b) in zip(KEYS, KEYS[1:]):
        if t <= tb:
            u = max(0, (t - ta) / (tb - ta))
            u = u * u * (3 - 2 * u)
            return {k: tuple(x + (y - x) * u for x, y in zip(a[k], b[k])) if isinstance(a[k], tuple)
                    else a[k] + (b[k] - a[k]) * u for k in a}
    return KEYS[-1][1].copy()

def solve_two(origin, target, a, b, pole):
    delta = target - origin
    dist = max(.001, min(delta.length, a + b - .0003))
    axis = delta.normalized()
    target = origin + axis * dist
    along = (a * a - b * b + dist * dist) / (2 * dist)
    height = math.sqrt(max(0, a * a - along * along))
    direction = Vector(pole) - origin
    direction -= axis * direction.dot(axis)
    return origin + axis * along + direction.normalized() * height, target

def hierarchy():
    return sorted(rig.data.bones, key=lambda b: len(b.parent_recursive))

def arm_frames(start, elbow, wrist):
    """Map the rest elbow plane to the posed plane without forearm pronation."""
    upper, lower, hand = [rest['mixamorig:Right'+s].translation for s in ['Arm', 'ForeArm', 'Hand']]
    original = [(lower-upper).normalized(), (hand-lower).normalized()]
    current = [(elbow-start).normalized(), (wrist-elbow).normalized()]
    normal_rest = original[0].cross(original[1])
    if normal_rest.length < .001:
        normal_rest = original[0].cross(Vector((0, -1, 0)))
    normal_rest.normalize()
    normal = current[0].cross(current[1]).normalized()
    matrices = []
    for old, new, name, origin in zip(original, current, ['Arm', 'ForeArm'], [start, elbow]):
        basis_old = Matrix((old, normal_rest, old.cross(normal_rest))).transposed()
        basis_new = Matrix((new, normal, new.cross(normal))).transposed()
        rotation = basis_new @ basis_old.transposed() @ rest['mixamorig:Right'+name].to_3x3()
        matrices.append(Matrix.Translation(origin) @ rotation.to_4x4())
    return matrices

def pose(params):
    targets = {}
    def inherited(name):
        b = rig.data.bones[name]
        if b.parent:
            return targets[b.parent.name] @ rest[b.parent.name].inverted() @ rest[name]
        return rest[name].copy()
    def aim(name, start, end):
        bone = rig.data.bones[name]
        q = (bone.tail_local - bone.head_local).rotation_difference(end - start) @ rest[name].to_quaternion()
        targets[name] = Matrix.Translation(start) @ q.to_matrix().to_4x4()
    for short, fraction in [('Hips', .22), ('Spine', .48), ('Spine1', .76), ('Spine2', 1), ('Neck', 1), ('Head', 1)]:
        name = 'mixamorig:' + short
        m = inherited(name)
        q = Quaternion((0, 0, 1), math.radians(params['twist'] * fraction))
        q @= Quaternion((1, 0, 0), math.radians(params['lean'] * fraction))
        orientation = q @ rest[name].to_quaternion()
        targets[name] = Matrix.Translation(m.translation) @ orientation.to_matrix().to_4x4()
        if short == 'Hips':
            targets[name].translation += Vector((0, 0, -.018))
    for side, sign in [('Right', -1), ('Left', 1)]:
        prefix = 'mixamorig:' + side
        targets[prefix + 'Shoulder'] = inherited(prefix + 'Shoulder')
        upper, lower, foot = [prefix + x for x in ['UpLeg', 'Leg', 'Foot']]
        start = inherited(upper).translation
        endpoint = rest[foot].translation.copy()
        if side == 'Left':
            endpoint += Vector((0, .025 * params['lift'] / .055, params['lift']))
        joint, endpoint = solve_two(start, endpoint, rig.data.bones[upper].length, rig.data.bones[lower].length,
                                    (sign * .28, -.8, .45))
        aim(upper, start, joint)
        aim(lower, joint, endpoint)
        targets[foot] = rest[foot].copy()
        targets[foot].translation = endpoint
        upper, lower, hand = [prefix + x for x in ['Arm', 'ForeArm', 'Hand']]
        start = inherited(upper).translation
        pole = Vector((-.45, .15, 1.02)) if side == 'Right' else Vector((.40, -.025, 1.02))
        if side == 'Right':
            blade_direction = Vector(params['d']).normalized()
            wrist = Vector(params['r']) - Vector((0, -.105, -.02))
            # The grip offset depends on the hand orientation. Relax this
            # fixed-point solve instead of alternating between wrist targets.
            # Keep the final orientation on the final solved forearm axis.
            for iteration in range(64):
                elbow, wrist = solve_two(start, wrist, rig.data.bones[upper].length, rig.data.bones[lower].length, pole)
                upper_matrix, lower_matrix = arm_frames(start, elbow, wrist)
                fore_axis = (wrist - elbow).normalized()
                # Allow a modest wrist bend so the blade can follow the native
                # silhouette without folding the hand into the forearm.
                palm_long = fore_axis - blade_direction * fore_axis.dot(blade_direction)
                if palm_long.length < .01:
                    palm_long = fore_axis
                palm_long.normalize()
                swing = fore_axis.rotation_difference(palm_long)
                swing = Quaternion((1, 0, 0, 0)).slerp(swing, min(1, math.radians(35)/max(.0001, swing.angle)))
                palm_long = swing @ fore_axis
                blade_axis = blade_direction - palm_long * blade_direction.dot(palm_long)
                if blade_axis.length < .05:
                    blade_axis = Vector((1, 0, 0))
                    blade_axis -= palm_long * blade_axis.dot(palm_long)
                blade_axis.normalize()
                normal = blade_axis.cross(palm_long).normalized()
                wanted = Matrix((normal, blade_axis, palm_long)).transposed() @ sword_basis.inverted()
                inherited_hand = lower_matrix.to_3x3() @ rest[lower].to_3x3().inverted() @ rest[hand].to_3x3()
                relative = (inherited_hand.inverted() @ wanted).to_quaternion()
                swing, twist = relative.to_swing_twist('Y')
                swing = Quaternion((1, 0, 0, 0)).slerp(swing, min(1, math.radians(30)/max(.0001, swing.angle)))
                twist = max(-math.radians(75), min(math.radians(75), twist))
                hand_rot = inherited_hand @ (swing @ Quaternion((0, 1, 0), twist)).to_matrix()
                candidate = Vector(params['r']) - hand_rot @ grip_local
                if iteration == 63:
                    break
                wrist = wrist.lerp(candidate, .35)
            targets[upper], targets[lower] = upper_matrix, lower_matrix
            targets[hand] = Matrix.Translation(wrist) @ hand_rot.to_4x4()
        else:
            wrist = Vector(params['l'])
            elbow, wrist = solve_two(start, wrist, rig.data.bones[upper].length, rig.data.bones[lower].length, pole)
            aim(upper, start, elbow)
            aim(lower, elbow, wrist)
            orientation = targets[lower].to_3x3() @ rest[lower].to_3x3().inverted() @ rest[hand].to_3x3()
            targets[hand] = Matrix.Translation(wrist) @ orientation.to_4x4()
    for bone in hierarchy():
        name = bone.name
        if name not in targets:
            targets[name] = inherited(name)
        kw = {'parent_matrix': targets[bone.parent.name], 'parent_matrix_local': rest[bone.parent.name]} if bone.parent else {}
        rig.pose.bones[name].matrix_basis = bone.convert_local_to_pose(targets[name], rest[name], invert=True, **kw)
    apply_grip()
    bpy.context.view_layer.update()

def bake(name, params_at, duration):
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    key_poses = []
    key_times = [t for t, _ in KEYS] if name == 'MM6_Attack' else [0, duration]
    for t in key_times:
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.rotation_mode = 'QUATERNION'
            pb.matrix_basis.identity()
        pose(params_at(t))
        key_poses.append({pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy())
                          for pb in rig.pose.bones})
    # Recover to the same idle pose, including arm roll, rather than resolving
    # an IK branch again at the endpoint. Intermediate motion is ordinary FK.
    key_poses[-1] = key_poses[0]
    previous = {}
    for frame in range(round(duration * scene.render.fps) + 1):
        t = frame / scene.render.fps
        interval = min(len(key_times)-2, next((i for i in range(len(key_times)-1)
                                              if t <= key_times[i+1]), len(key_times)-2))
        u = (t-key_times[interval]) / (key_times[interval+1]-key_times[interval])
        u = u*u*(3-2*u)
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.rotation_mode = 'QUATERNION'
            a, b = key_poses[interval][pb.name], key_poses[interval+1][pb.name]
            qa, qb = a[1], b[1].copy()
            if qa.dot(qb) < 0:
                qb.negate()
            pb.location = a[0].lerp(b[0], u)
            pb.rotation_quaternion = qa.slerp(qb, u)
            pb.scale = a[2].lerp(b[2], u)
        for pb in rig.pose.bones:
            if pb.name in previous and pb.rotation_quaternion.dot(previous[pb.name]) < 0:
                pb.rotation_quaternion.negate()
            previous[pb.name] = pb.rotation_quaternion.copy()
        rig.animation_data.action = action
        for pb in rig.pose.bones:
            for prop in ['location', 'rotation_quaternion', 'scale']:
                pb.keyframe_insert(prop, frame=frame, group=pb.name)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:
                        key.interpolation = 'LINEAR'
    return action

idle = bake('Idle_Sword', lambda t: KEYS[0][1], 1)
attack = bake('MM6_Attack', interpolate, .75)

# Preserve each clip's gesture and airborne intervals, raising only penetrating
# frames. Bake root translation at the same 48 Hz used by the portable export.
ground_corrections = {}
for label, action in {**source_actions, idle.name: idle, attack.name: attack}.items():
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    rows = []
    for frame in range(round(action.frame_range[0]), round(action.frame_range[1]) + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        obj = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = obj.to_mesh()
        floor = min((obj.matrix_world @ v.co).z for v in mesh.vertices)
        obj.to_mesh_clear()
        correction = max(0, -floor) + .0006
        pb = rig.pose.bones['mixamorig:Hips']
        target = pb.matrix.copy()
        target.translation += rig.matrix_world.to_3x3().inverted() @ Vector((0, 0, correction))
        basis = rig.data.bones[pb.name].convert_local_to_pose(target, rest[pb.name], invert=True)
        rows.append((frame, basis.translation.copy(), correction))
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in list(bag.fcurves):
                    if fc.data_path == 'pose.bones["mixamorig:Hips"].location':
                        bag.fcurves.remove(fc)
    for frame, location, _ in rows:
        rig.pose.bones['mixamorig:Hips'].location = location
        rig.pose.bones['mixamorig:Hips'].keyframe_insert('location', frame=frame, group='mixamorig:Hips')
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:
                        if fc.data_path == 'pose.bones["mixamorig:Hips"].location':
                            key.interpolation = 'LINEAR'
    ground_corrections[label] = max(row[2] for row in rows)

# Optional authoring IK controls. FK animations/export are independent of these.
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for side, sign in [('Right', -1), ('Left', 1)]:
    for kind, position in [('Hand', rest['mixamorig:' + side + 'Hand'].translation),
                           ('Elbow', Vector((sign * .40, -.20, 1.05))),
                           ('Foot', rest['mixamorig:' + side + 'Foot'].translation),
                           ('Knee', Vector((sign * .20, -.55, .50)))]:
        bone = rig.data.edit_bones.new('CTRL.' + kind + '.' + side)
        bone.head = position
        bone.tail = position + Vector((0, 0, .07))
        bone.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
rig['use_ik'] = 0.0
rig.id_properties_ui('use_ik').update(min=0, max=1, description='0 plays baked FK clips; 1 enables hand/foot IK controls for authoring')
for side in ['Right', 'Left']:
    for bone, effector, pole in [('ForeArm', 'Hand', 'Elbow'), ('Leg', 'Foot', 'Knee')]:
        con = rig.pose.bones['mixamorig:' + side + bone].constraints.new('IK')
        con.name = 'Optional authoring ' + effector + ' IK'
        con.target = rig
        con.subtarget = 'CTRL.' + effector + '.' + side
        con.pole_target = rig
        con.pole_subtarget = 'CTRL.' + pole + '.' + side
        con.chain_count = 2
        con.influence = 0
        driver = con.driver_add('influence').driver
        var = driver.variables.new()
        var.name = 'enabled'
        var.type = 'SINGLE_PROP'
        var.targets[0].id = rig
        var.targets[0].data_path = '["use_ik"]'
        driver.expression = 'enabled'
control_collection = rig.data.collections.new('IK authoring controls')
for b in rig.data.bones:
    if b.name.startswith('CTRL.'):
        control_collection.assign(b)
        rig.pose.bones[b.name].color.palette = 'THEME04'
rig.show_in_front = True

actions = {**source_actions, idle.name: idle, attack.name: attack}
scene['actions'] = json.dumps({k: a.name for k, a in actions.items()})
scene['native_attack_pose_times'] = json.dumps([t for t, _ in KEYS])
scene['source_sha256'] = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
scene['rig_notes'] = 'Use use_ik=0 for clips; use_ik=1 enables hand/foot controls. SwordGrip=1 is the armed shape; reset to 0 for open-hand finger posing.'
notes = bpy.data.texts.new('START_HERE')
notes.use_fake_user = True
notes.write('''Finished supplied goblin — MM6 attack pilot

The source GLB remains unchanged. This scene owns one goblin, its sword and
optional authoring controls. Textures are packed into the Blender file.

Play MM6_Attack at 48 fps, frames 0–36 (0.75 seconds). Frame 36 is the
exact Idle_Sword pose and equals frame 0. The six native pose starts are
frames 0, 6, 12, 18, 24 and 30; intermediate frames are baked FK motion.

Other actions: Running 0–32; Walking 0–50; Hit_Reaction_1 0–58;
Idle_Sword 0–48. Select the rig, open the Action Editor and choose an
action. Set the playback range to its range above. NLA tracks are stored
muted so the chosen action plays alone.

Rig custom property use_ik=0 plays the baked clips. For new animation,
duplicate an action and enable use_ik=1 for hand/foot position controls;
elbow and knee controls are poles. Position controls at the current
joints before switching on IK. Rotate Hand bones for sword orientation.
Turn IK off or bake visual transforms before portable export.

Body shape key SwordGrip=1 holds the sword. Set it to 0 to recover the
original open hand for independent finger posing. UVs are unchanged.
The left toe is stabilized to the foot; shoulder plate parents/weights
are repaired. Every exported vertex has at most four normalized weights.

This is a 3D interpretation of the native six-frame attack, ready for
motion/art review. Source Running, Walking and Hit_Reaction_1 remain
available with the same durations and repaired skin/ground clearance.
''')
for track in list(rig.animation_data.nla_tracks):
    rig.animation_data.nla_tracks.remove(track)
rig.animation_data.action = None
for name, action in actions.items():
    track = rig.animation_data.nla_tracks.new()
    track.name = name
    strip = track.strips.new(name, 0, action)
    strip.action_slot = action.slots[0]
    strip.extrapolation = 'NOTHING'
    strip.blend_type = 'REPLACE'
    track.mute = True
for im in bpy.data.images:
    if im.source == 'FILE' and not im.packed_file:
        im.pack()
scene.frame_start = 0
scene.frame_end = 36
rig.animation_data.action = attack
rig.animation_data.action_slot = attack.slots[0]
scene.frame_set(6)
for obj in scene.objects:
    obj.select_set(False)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'goblin_finished.blend'))

# Export all named clips, a four-influence skin and the selected asset only.
rig.animation_data.action = None
for track in rig.animation_data.nla_tracks:
    track.mute = False
for obj in scene.objects:
    obj.select_set(False)
rig.select_set(True)
body.select_set(True)
for obj in sword_objects:
    obj.select_set(True)
scene.frame_set(0)
export_options = dict(filepath=str(ROOT / 'goblin_finished.glb'), export_format='GLB', use_selection=True,
                      use_active_scene=True, export_animations=True, export_animation_mode='NLA_TRACKS',
                      export_force_sampling=True, export_anim_slide_to_zero=True, export_optimize_animation_size=False,
                      export_skins=True, export_influence_nb=4, export_all_influences=False, export_current_frame=False)
if 'export_def_bones' in bpy.ops.export_scene.gltf.get_rna_type().properties:
    export_options['export_def_bones'] = True
bpy.ops.export_scene.gltf(**export_options)
for track in rig.animation_data.nla_tracks:
    track.mute = True
rig.animation_data.action = attack
rig.animation_data.action_slot = attack.slots[0]
scene.frame_set(6)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'goblin_finished.blend'))

report = dict(source_sha256=scene['source_sha256'], weights=changed_weights, toe_geometry_vertices=toe_repair_count,
              grip_shape_vertices=grip_vertices, maximum_ground_correction=ground_corrections,
              interpolation='Six native pose keys; smooth FK quaternion interpolation; exact idle recovery',
              max_influences=max(len(v.groups) for v in body.data.vertices), body_triangles=len(body.data.polygons),
              weapon_triangles=sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sword_objects),
              animations={k: {'duration': (a.frame_range[1] - a.frame_range[0]) / 48} for k, a in actions.items()},
              grip_local=list(grip_local), grip_basis=list(map(list, sword_basis)), native_keys=KEYS)
(ROOT / 'authoring/construction.json').write_text(json.dumps(report, indent=2) + '\n')
print('FINISHED', json.dumps(report))
