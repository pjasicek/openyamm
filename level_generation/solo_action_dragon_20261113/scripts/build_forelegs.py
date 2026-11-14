"""Build the Dragon's first-person forelegs: rig one foreleg mesh, mirror it, key the clips, export the view model.

blender -b --python build_forelegs.py -- --mesh <foreleg.glb|procedural> --out <dir> [--name dragon_forelegs]
    [--install <OpenYAMM>/assets_dev/engine/view_model]

The mesh is one right foreleg hanging down along -Z from its shoulder cut, as in references_hd/00_three_quarter.png
(Meshy keeps the image's up as +Z and its front as -Y). Landmarks come from the geometry: the shoulder cut at the
top, slices for the elbow, wrist and knuckles, and the talon tips as the lowest clusters.

The view model's space is the private Oblivion arms' (reference/oblivion_poc/glb/arms_full.glb imported in Blender,
its ZupToYup root included): up +Z, the eye looking along +Y, screen right +X (the engine's lookAt toward +Y with +Z
up). The poses below are written with forward as -Y and turned by FORWARD before keying.
Node contract (game/render/FirstPersonViewModel): Camera01 (the eye; its translation is used), Weapon (required, an
empty under the right hand), ClawTipR/ClawTipL (talon tips for the slash direction), Mouth (the breath's start).
Clips are claws<action> with Oblivion's text-key conventions in <name>.textkeys.json; <name>_h2h.glb carries the same
motion under the handtohand names so today's engine plays it on an unarmed kit.
"""

import json
import math
import shutil
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

FPS = 30
LEG_LENGTH = 60.0          # shoulder cut to the talon tips, in the arms' units
EYE = Vector((0.0, 0.0, 120.0))
SHOULDER_R = Vector((26.0, 0.0, 82.0))    # below and beside the eye, off screen
MOUTH_OFFSET = Vector((0.0, 10.0, -16.0))
# The poses are authored looking along -Y; the view model looks along +Y: their Y flips.
FORWARD = Vector((1.0, -1.0, 1.0))


def args():
    argv = sys.argv[sys.argv.index('--') + 1:]
    result = {'mesh': 'procedural', 'out': '.', 'name': 'dragon_forelegs'}
    for index in range(0, len(argv), 2):
        result[argv[index].lstrip('-')] = argv[index + 1]
    return result


# ---------------------------------------------------------------------------------------------------- the mesh ---
def procedural_leg():
    """A placeholder foreleg in the master pose: upper arm, forearm, hand, three digits with talons, an inner digit."""
    mesh = bpy.data.meshes.new('foreleg_placeholder')
    bm = bmesh.new()

    def limb(a, b, r1, r2, segments=10):
        a, b = Vector(a), Vector(b)
        axis = b - a
        result = bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=r1, radius2=r2,
                                       depth=axis.length)
        rot = axis.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=result['verts'])

    limb((0, 0, 0), (0, 2, -26), 7.5, 5.8)
    limb((0, 2, -26), (0, 0, -44), 5.8, 4.2)
    limb((0, 0, -44), (0, -1, -53), 4.6, 4.0)
    for x, tip in ((-4.5, (-6, -3, -66)), (0, (0, -4, -70)), (4.5, (6, -3, -66))):
        limb((x, -1, -52), tip, 1.7, 1.3, 8)
        limb(tip, (tip[0] * 1.05, tip[1] - 4, tip[2] - 7), 1.2, 0.05, 8)
    limb((5, 1, -48), (8, 0, -57), 1.3, 1.0, 8)
    limb((8, 0, -57), (9, -2, -62), 1.0, 0.05, 8)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new('foreleg', mesh)
    bpy.context.collection.objects.link(obj)
    material = bpy.data.materials.new('dragon_scales')
    material.use_nodes = True
    material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.08, 0.04, 0.04, 1)
    obj.data.materials.append(material)
    return obj


def imported_leg(path):
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in bpy.context.scene.objects:
        o.select_set(o in meshes)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in list(bpy.context.scene.objects):
        if o is not obj:
            bpy.data.objects.remove(o)
    obj.name = 'foreleg'
    return obj


def normalise(obj):
    """Scale to LEG_LENGTH, shoulder cut centre at the origin, talons down (-Z)."""
    verts = np.array([v.co[:] for v in obj.data.vertices])
    z = verts[:, 2]
    height = z.max() - z.min()
    top = verts[z > z.max() - 0.06 * height]
    bottom = verts[z < z.min() + 0.10 * height]
    # The talons spread wider than the shoulder cut: if not, the leg is upside down.
    if np.ptp(bottom[:, 0]) + np.ptp(bottom[:, 1]) < np.ptp(top[:, 0]) + np.ptp(top[:, 1]):
        obj.data.transform(Matrix.Rotation(math.pi, 4, 'X'))
        verts = np.array([v.co[:] for v in obj.data.vertices])
        z = verts[:, 2]
        top = verts[z > z.max() - 0.06 * height]
    shoulder = top.mean(axis=0)
    shoulder[2] = z.max()
    scale = LEG_LENGTH / height
    obj.data.transform(Matrix.Diagonal((scale, scale, scale, 1.0)) @ Matrix.Translation(-Vector(shoulder)))
    obj.data.update()


def landmarks(obj):
    verts = np.array([v.co[:] for v in obj.data.vertices])
    z = verts[:, 2]
    length = -z.min()

    def slice_centre(fraction, width=0.03):
        band = verts[np.abs(z + fraction * length) < width * length]
        return Vector(band.mean(axis=0)) if len(band) else Vector((0, 0, -fraction * length))

    elbow, wrist, knuckle = slice_centre(0.38), slice_centre(0.60), slice_centre(0.74)
    # The three forward talons: k-means (k=3) in XY over the lowest tenth of the leg.
    low = verts[z < -0.90 * length]
    centres = low[np.argsort(low[:, 0])][[0, len(low) // 2, -1], :2].copy()
    for _ in range(20):
        labels = np.argmin(((low[:, None, :2] - centres[None]) ** 2).sum(-1), axis=1)
        centres = np.array([low[labels == k, :2].mean(axis=0) if np.any(labels == k) else centres[k]
                            for k in range(3)])
    digits = []
    for k in np.argsort(centres[:, 0]):
        cluster = low[labels == k]
        tip = Vector(cluster[np.argmin(cluster[:, 2])])
        # Mid joint: the leg's vertices near this digit's column at 86 % depth.
        band = verts[(np.abs(z + 0.86 * length) < 0.03 * length)
                     & (((verts[:, :2] - centres[k]) ** 2).sum(-1) < (0.08 * length) ** 2)]
        mid = Vector(band.mean(axis=0)) if len(band) else knuckle.lerp(tip, 0.55)
        base = knuckle.copy()
        base.x += (mid.x - knuckle.x) * 0.6
        base.y += (mid.y - knuckle.y) * 0.6
        digits.append((base, mid, tip))
    # The palm faces where the talons hook to: tips against their digit's mid joint, across the leg.
    # The masters show the back of the hand from the front (Meshy's -Y): the palm faces +Y.
    palm = Vector((0, 1, 0))
    return {'shoulder': Vector((0, 0, 0)), 'elbow': elbow, 'wrist': wrist, 'knuckle': knuckle, 'digits': digits,
            'palm': palm, 'length': length}


# ---------------------------------------------------------------------------------------------------- the rig ----
def side_point(point, side, place):
    """A leg-local point to the rig's rest: the right leg at SHOULDER_R, the left mirrored in X."""
    p = Vector(point)
    if side == 'L':
        p.x = -p.x
    origin = SHOULDER_R.copy()
    if side == 'L':
        origin.x = -origin.x
    return origin + p if place else p


def build_rig(marks):
    arm_data = bpy.data.armatures.new('ForelegRig')
    rig = bpy.data.objects.new('ForelegRig', arm_data)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    edit = arm_data.edit_bones

    def bone(name, head, tail, parent=None, roll_to=None, connect=False):
        b = edit.new(name)
        b.head, b.tail = head, tail
        if roll_to is not None:
            b.align_roll(roll_to)
        if parent:
            b.parent = edit[parent]
            b.use_connect = connect
        return b

    camera = bone('Camera01', EYE, EYE + Vector((0, 6, 0)))
    bone('Mouth', EYE + MOUTH_OFFSET, EYE + MOUTH_OFFSET + Vector((0, 4, 0)), 'Camera01')
    for side in ('R', 'L'):
        def P(p):
            return side_point(p, side, True)
        palm = marks['palm'].copy()
        if side == 'L':
            palm.x = -palm.x
        bone(f'Shoulder{side}', P(marks['shoulder']) + Vector((0, 0, 4)), P(marks['shoulder']), roll_to=palm)
        bone(f'Upper{side}', P(marks['shoulder']), P(marks['elbow']), f'Shoulder{side}', palm, True)
        bone(f'Fore{side}', P(marks['elbow']), P(marks['wrist']), f'Upper{side}', palm, True)
        bone(f'Hand{side}', P(marks['wrist']), P(marks['knuckle']), f'Fore{side}', palm, True)
        for index, (base, mid, tip) in enumerate(marks['digits']):
            bone(f'Digit{index}a{side}', P(base), P(mid), f'Hand{side}', palm)
            bone(f'Digit{index}b{side}', P(mid), P(tip), f'Digit{index}a{side}', palm, True)
        tip = marks['digits'][1][2]
        bone(f'ClawTip{side}', P(tip), P(tip) + Vector((0, 0, -2)), f'Digit1b{side}')
        if side == 'R':
            bone('Weapon', P(marks['knuckle']), P(marks['knuckle']) + Vector((0, 0, -3)), 'HandR')
    bpy.ops.object.mode_set(mode='OBJECT')
    for b in rig.pose.bones:
        b.rotation_mode = 'QUATERNION'
    _ = camera
    return rig


def segment_distance(points, a, b):
    ab = b - a
    t = np.clip(((points - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
    return np.linalg.norm(points - (a + t[:, None] * ab), axis=1)


# Blend bands (fractions of the leg length) across the wrist and the knuckle planes. A hard switch at the knuckles
# tore the outer digits open in the idle (2026-11-14): the side digits lie far from the hand bone, so distance alone
# gave them their digit bone only, and the hand above the plane took a share of the forearm; a curl then opened a
# flat, streaked gap across the digit's root.
WRIST_BAND = 0.26
KNUCKLE_BAND = 0.10


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def pair_weights(distances):
    """The two nearest of some bones by segment distance, as shares summing to 1: (indices, shares)."""
    order = np.argsort(distances)[:2]
    w = 1.0 / (distances[order] + 0.4) ** 4
    return order, w / w.sum()


def skin(obj, rig, marks, side):
    """Weights by limb zone with smooth bands: above the wrist the upper arm and forearm by distance, the hand
    between the wrist and the knuckles, below them the nearest digit's chain; across the wrist and knuckle planes
    each blends into the next, so no digit root or wrist is bound to one bone on one side and another on the other."""
    verts = np.array([v.co[:] for v in obj.data.vertices])
    length = marks['length']
    arm = [(f'Upper{side}', marks['shoulder'], marks['elbow']), (f'Fore{side}', marks['elbow'], marks['wrist'])]
    arm_distances = np.stack([segment_distance(verts, np.array(a[:]), np.array(b[:])) for _, a, b in arm], axis=1)
    chains = []
    for index, (base, mid, tip) in enumerate(marks['digits']):
        chain = [(f'Digit{index}a{side}', base, mid), (f'Digit{index}b{side}', mid, tip)]
        chains.append((chain, np.stack([segment_distance(verts, np.array(a[:]), np.array(b[:]))
                                        for _, a, b in chain], axis=1)))
    digit_columns = np.array([[d[1].x, d[1].y] for d in marks['digits']])
    nearest_digit = np.argmin(((verts[:, None, :2] - digit_columns[None]) ** 2).sum(-1), axis=1)
    z = verts[:, 2]
    # Share of the digit (below the knuckles) and of the arm above the wrist; the hand takes what is left.
    digit_share = smoothstep((marks['knuckle'].z - z) / (KNUCKLE_BAND * length) + 0.5)
    arm_share = smoothstep((z - marks['wrist'].z) / (WRIST_BAND * length) + 0.5) * (1.0 - digit_share)
    groups = {}
    for v in range(len(verts)):
        weights = {}
        hand = 1.0 - digit_share[v] - arm_share[v]
        if hand > 0.0:
            weights[f'Hand{side}'] = hand
        if arm_share[v] > 0.0:
            order, shares = pair_weights(arm_distances[v])
            for k, share in zip(order, shares):
                weights[arm[k][0]] = weights.get(arm[k][0], 0.0) + arm_share[v] * share
        if digit_share[v] > 0.0:
            chain, distances = chains[nearest_digit[v]]
            order, shares = pair_weights(distances[v])
            for k, share in zip(order, shares):
                weights[chain[k][0]] = weights.get(chain[k][0], 0.0) + digit_share[v] * share
        for name, weight in weights.items():
            if weight > 1.0e-4:
                group = groups.get(name) or obj.vertex_groups.new(name=name)
                groups[name] = group
                group.add([v], float(weight), 'REPLACE')
    modifier = obj.modifiers.new('Armature', 'ARMATURE')
    modifier.object = rig
    obj.parent = rig


def make_side_meshes(leg, rig, marks):
    right = leg
    left = leg.copy()
    left.data = leg.data.copy()
    left.name = 'forelegL'
    right.name = 'forelegR'
    bpy.context.collection.objects.link(left)
    left.data.transform(Matrix.Diagonal((-1, 1, 1, 1)))
    left.data.flip_normals()
    right.data.transform(Matrix.Translation(SHOULDER_R))
    mirrored_shoulder = SHOULDER_R.copy()
    mirrored_shoulder.x = -mirrored_shoulder.x
    left.data.transform(Matrix.Translation(mirrored_shoulder))

    def placed(side):
        m = {key: (side_point(value, side, True) if isinstance(value, Vector) and key != 'palm' else value)
             for key, value in marks.items()}
        m['digits'] = [tuple(side_point(p, side, True) for p in d) for d in marks['digits']]
        return m

    skin(right, rig, placed('R'), 'R')
    skin(left, rig, placed('L'), 'L')
    return right, left


# ---------------------------------------------------------------------------------------------------- posing -----
def frame_matrix(digits_dir, palm_dir):
    """A hand bone's world rotation: its Y along the digits, its Z along the palm normal."""
    y = Vector(digits_dir).normalized()
    z = Vector(palm_dir)
    z = (z - y * z.dot(y)).normalized()
    x = y.cross(z)
    return Matrix((x, y, z)).transposed()


def setup_controls(rig):
    controls = {}
    for side in ('R', 'L'):
        sign = 1 if side == 'R' else -1
        target = bpy.data.objects.new(f'Target{side}', None)
        pole = bpy.data.objects.new(f'Pole{side}', None)
        for o in (target, pole):
            bpy.context.collection.objects.link(o)
            o.rotation_mode = 'QUATERNION'
        pole.location = SHOULDER_R * Vector((sign, 1, 1)) + Vector((sign * 50, 0, -50))
        fore = rig.pose.bones[f'Fore{side}']
        ik = fore.constraints.new('IK')
        ik.target = target
        ik.pole_target = pole
        ik.pole_angle = -math.pi / 2
        ik.chain_count = 2
        hand = rig.pose.bones[f'Hand{side}']
        copy = hand.constraints.new('COPY_ROTATION')
        copy.target = target
        controls[side] = target
    return controls


# A pose per side: wrist position (relative to the eye), digit direction, palm normal, digit curl (radians).
def pose(wrist, digits=(0, -1, 0.15), palm=(0, 0.2, -1), curl=0.25, shoulder=(0, 0, 0)):
    return {'wrist': Vector(wrist) * FORWARD, 'digits': Vector(digits) * FORWARD, 'palm': Vector(palm) * FORWARD,
            'curl': curl, 'shoulder': Vector(shoulder) * FORWARD}


def mirrored(p):
    flip = Vector((-1, 1, 1))
    return {'wrist': p['wrist'] * flip, 'digits': p['digits'] * flip, 'palm': p['palm'] * flip, 'curl': p['curl'],
            'shoulder': p['shoulder'] * flip}


def moved(p, wrist=(0, 0, 0), curl=0.0):
    flip = FORWARD
    return pose((p['wrist'] + Vector(wrist) * flip) * flip, p['digits'] * flip, p['palm'] * flip, p['curl'] + curl,
                p['shoulder'] * flip)


IDLE_R = pose((21, -30, -20), (0.1, -1, 0.5), (-0.2, 0.2, -1), 0.3)
WIND_R = pose((26, -32, 0), (0.3, -0.5, 1.0), (-0.8, 0.3, -0.2), -0.15, (4, -12, 6))
RAKE_R = pose((4, -38, -8), (-1, -0.6, 0.1), (-0.1, 0.3, -1), 0.55, (-4, -18, 4))
FOLLOW_R = pose((-14, -30, -16), (-0.9, -0.4, -0.4), (0, 0.5, -1), 0.8, (-6, -14, 2))
LOW_R = pose((22, -12, -42), (0.1, -0.8, 0.3), (-0.3, 0.2, -1), 0.4)
GUARD_R = pose((-4, -36, -10), (-0.5, -0.3, 1), (0.1, -1, 0.1), 0.15, (-4, -16, 4))
PART_R = pose((32, -24, -20), (0.6, -1, 0.1), (-0.6, 0.2, -1), -0.1, (6, 0, 4))
CLAW_KEYS = {}


def clip_specs():
    """name -> (length seconds, {time: (pose R, pose L)}, camera keys {time: offset}, text keys)."""
    idle_l = mirrored(IDLE_R)
    specs = {}

    def breathing(length, amplitude, phase=0.0, step=0.0):
        keys = {}
        for i in range(5):
            t = length * i / 4
            s = math.sin(2 * math.pi * (i / 4 + phase))
            r = moved(IDLE_R, (0, step * s, amplitude * s), 0.05 * s)
            l_ = moved(idle_l, (0, -step * s, -amplitude * s), -0.05 * s)
            keys[t] = (r, l_)
        return keys

    def bob(length, amplitude):
        return {length * i / 4: Vector((0, 0, amplitude * abs(math.sin(math.pi * i / 2)))) for i in range(5)}

    specs['idle'] = (3.0, breathing(3.0, 1.2), {0: Vector(), 1.5: Vector((0, 0, 0.6)), 3.0: Vector()}, [])
    for direction, step in (('forward', 3.0), ('backward', -3.0), ('left', 1.5), ('right', 1.5)):
        specs[direction] = (1.0, breathing(1.0, 2.5, step=step), bob(1.0, -1.2), [])
        specs['fast' + direction] = (0.7, breathing(0.7, 4.0, step=step * 1.6), bob(0.7, -2.0), [])

    def attack(r_poses, l_pose, hit, chain, side_key, length=0.6667):
        keys = {}
        for t, p in r_poses.items():
            keys[t] = (p, l_pose)
        return (length, keys, {0: Vector(), hit: Vector((0, -1.5, -0.5)), length: Vector()},
                [(hit, 'Hit'), (chain, side_key)])

    pulled_l = moved(idle_l, (0, 8, -6), 0.1)
    # The rake's key is the Hit: the talons cross the centre at the blow.
    specs['attackright'] = attack({0: IDLE_R, 0.1: WIND_R, 0.2: RAKE_R, 0.36: FOLLOW_R, 0.6667: IDLE_R},
                                  pulled_l, 0.20, 0.4333, 'a:L')
    left = attack({0: IDLE_R, 0.1: WIND_R, 0.2: RAKE_R, 0.36: FOLLOW_R, 0.6667: IDLE_R},
                  pulled_l, 0.20, 0.4333, 'a:R')
    specs['attackleft'] = (left[0], {t: (mirrored(l_), mirrored(r)) for t, (r, l_) in left[1].items()},
                           left[2], left[3])
    specs['equip'] = (0.8, {0: (LOW_R, mirrored(LOW_R)), 0.8: (IDLE_R, idle_l)}, {}, [])
    guard_l = mirrored(GUARD_R)
    guard_l = moved(guard_l, (0, 2, -4))
    specs['blockidle'] = (1.3, {0: (GUARD_R, guard_l), 0.65: (moved(GUARD_R, (0, 0, 1), 0.05), guard_l),
                                1.3: (GUARD_R, guard_l)}, {}, [])
    jolt = Vector((0, 5, -2))
    specs['blockhit'] = (0.3, {0: (GUARD_R, guard_l),
                               0.08: (moved(GUARD_R, jolt, 0.15), moved(guard_l, jolt, 0.15)),
                               0.3: (GUARD_R, guard_l)}, {0: Vector(), 0.08: Vector((0, 2, 0)), 0.3: Vector()},
                         [])
    specs['breath'] = (0.9, {0: (IDLE_R, idle_l), 0.3: (LOW_R, mirrored(LOW_R)), 0.55: (LOW_R, mirrored(LOW_R)),
                             0.9: (IDLE_R, idle_l)},
                       {0: Vector(), 0.3: Vector((0, 2.5, 1.5)), 0.4: Vector((0, -3.0, -0.5)), 0.6: Vector(),
                        0.9: Vector()}, [(0.4, 'Hit')])
    specs['bite'] = (0.6, {0: (IDLE_R, idle_l), 0.15: (PART_R, mirrored(PART_R)),
                           0.35: (PART_R, mirrored(PART_R)), 0.6: (IDLE_R, idle_l)},
                     {0: Vector(), 0.25: Vector((0, -9, -4)), 0.6: Vector()}, [(0.25, 'Hit')])
    return specs


def key_clip(rig, controls, name, spec):
    length, pose_keys, camera_keys, _ = spec
    scene = bpy.context.scene
    end = max(1, round(length * FPS))
    for side in ('R', 'L'):
        target = controls[side]
        target.animation_data_clear()
        target.animation_data_create().action = bpy.data.actions.new(f'_src_{name}_{side}')
    rig.animation_data_create().action = bpy.data.actions.new(f'_src_{name}_rig')
    for t, (r, l_) in sorted(pose_keys.items()):
        frame = round(t * FPS)
        for side, p in (('R', r), ('L', l_)):
            target = controls[side]
            target.location = EYE + p['wrist']
            target.rotation_quaternion = frame_matrix(p['digits'], p['palm']).to_quaternion()
            target.keyframe_insert('location', frame=frame)
            target.keyframe_insert('rotation_quaternion', frame=frame)
            shoulder = rig.pose.bones[f'Shoulder{side}']
            shoulder.location = rig_local_offset(rig, shoulder, p['shoulder'])
            shoulder.keyframe_insert('location', frame=frame)
            for bone in rig.pose.bones:
                if bone.name.startswith('Digit') and bone.name.endswith(side):
                    bone.rotation_quaternion = Quaternion((1, 0, 0), p['curl'] * (0.7 if 'a' in bone.name else 1))
                    bone.keyframe_insert('rotation_quaternion', frame=frame)
    camera = rig.pose.bones['Camera01']
    for t, offset in sorted(camera_keys.items()) or [(0, Vector())]:
        camera.location = rig_local_offset(rig, camera, Vector(offset) * FORWARD)
        camera.keyframe_insert('location', frame=round(t * FPS))
    scene.frame_start, scene.frame_end = 0, end
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.nla.bake(frame_start=0, frame_end=end, only_selected=True, visual_keying=True,
                     clear_constraints=False, use_current_action=False, bake_types={'POSE'})
    bpy.ops.object.mode_set(mode='OBJECT')
    baked = rig.animation_data.action
    baked.name = name
    baked.use_fake_user = True
    return baked


def rig_local_offset(rig, bone, offset):
    """A world offset of the eye in the Camera01 bone's local space (its pose location)."""
    rest = bone.bone.matrix_local.to_3x3()
    return rest.inverted() @ Vector(offset)


def text_keys(specs, prefix):
    result = {}
    for name, (length, _, _, keys) in specs.items():
        entries = [[0.0, 'start']] + [[t, text] for t, text in keys] + [[length, 'end']]
        result[prefix + name] = {'length': length, 'keys': sorted(entries)}
    return result


def export(path, actions, rename):
    for action in bpy.data.actions:
        action.use_fake_user = action in actions
    names = {}
    for action in actions:
        names[action] = action.name
        action.name = rename(action.name)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', export_animation_mode='ACTIONS',
                              export_force_sampling=True, export_frame_range=False, export_yup=True,
                              export_apply=False, export_skins=True, export_def_bones=False)
    for action, name in names.items():
        action.name = name


# The mesh gates over every baked clip (sampled every other frame): no edge both stretched beyond STRETCH_LIMIT of its
# rest length and grown by more than STRETCH_GROWTH units while on screen (a weight tear: the digit-root tear opened
# 0.5-unit edges to 10; a bent wrist doubles a few 0.15-unit slivers, which nobody sees; an elbow bent below the view
# is not seen), and no open edge of the mesh in the eye's 60 degree view at 16:9.
STRETCH_LIMIT = 1.6
STRETCH_GROWTH = 0.75
VIEW_HALF_TAN = math.tan(math.radians(30.0))
VIEW_ASPECT = 16.0 / 9.0


def open_edge_vertices(obj):
    """Vertices on the mesh's open edges, welding the glTF split vertices by position."""
    keys = {}
    ids = []
    for v in obj.data.vertices:
        ids.append(keys.setdefault(tuple(round(c, 4) for c in v.co), len(keys)))
    uses = {}
    for polygon in obj.data.polygons:
        loop = list(polygon.vertices)
        for a, b in zip(loop, loop[1:] + loop[:1]):
            edge = (min(ids[a], ids[b]), max(ids[a], ids[b]))
            uses.setdefault(edge, []).append(a)
    weld = {}
    for v, key in enumerate(ids):
        weld.setdefault(key, v)
    return sorted({weld[k] for edge, faces in uses.items() if len(faces) == 1 for k in edge})


def in_view(points, eye):
    """Which points the eye sees: ahead of it (+Y) and inside the 60 degree vertical view at 16:9."""
    p = points - np.array(eye[:])
    depth = np.maximum(p[:, 1], 1e-6)
    return (p[:, 1] > 1.0) & (np.abs(p[:, 2] / depth) < VIEW_HALF_TAN) \
        & (np.abs(p[:, 0] / depth) < VIEW_HALF_TAN * VIEW_ASPECT)


def mesh_gates(rig, meshes, actions):
    scene = bpy.context.scene
    camera = rig.pose.bones['Camera01']
    edges = {m.name: np.array([e.vertices[:] for e in m.data.edges]) for m in meshes}
    rest = {m.name: np.array([(m.matrix_world @ v.co)[:] for v in m.data.vertices]) for m in meshes}
    open_verts = {m.name: open_edge_vertices(m) for m in meshes}
    failed = []
    for action in actions:
        rig.animation_data.action = action
        start, end = (int(f) for f in action.frame_range)
        worst_stretch, worst_open, worst_growth = 1.0, 0, 0.0
        for frame in range(start, end + 1, 2):
            scene.frame_set(frame)
            depsgraph = bpy.context.evaluated_depsgraph_get()
            eye = rig.matrix_world @ camera.head
            for m in meshes:
                evaluated = m.evaluated_get(depsgraph)
                data = evaluated.to_mesh()
                posed = np.array([(m.matrix_world @ v.co)[:] for v in data.vertices])
                evaluated.to_mesh_clear()
                e, r = edges[m.name], rest[m.name]
                visible = in_view(posed, eye)
                shown = visible[e[:, 0]] | visible[e[:, 1]]
                posed_length = np.linalg.norm(posed[e[:, 0]] - posed[e[:, 1]], axis=1)
                rest_length = np.linalg.norm(r[e[:, 0]] - r[e[:, 1]], axis=1)
                growth = np.where(shown, posed_length - rest_length, 0.0)
                ratio = np.where(growth > STRETCH_GROWTH, posed_length / np.maximum(rest_length, 1e-6), 1.0)
                worst_growth = max(worst_growth, float(growth.max()))
                if ratio.max() > worst_stretch:
                    worst_stretch = float(ratio.max())
                    worst = int(np.argmax(ratio))
                    worst_where = (m.name, frame, [tuple(round(c, 1) for c in r[i]) for i in e[worst]],
                                   [[(m.vertex_groups[g.group].name, round(g.weight, 2))
                                     for g in m.data.vertices[i].groups] for i in e[worst]],
                                   round(float(np.linalg.norm(r[e[worst, 0]] - r[e[worst, 1]])), 3))
                if open_verts[m.name]:
                    worst_open = max(worst_open, int(visible[open_verts[m.name]].sum()))
        ok = worst_stretch <= STRETCH_LIMIT and worst_open == 0
        print('GATE', action.name, 'max stretch of grown edges on screen', round(worst_stretch, 3), 'max growth',
              round(worst_growth, 2), 'open edge vertices in view', worst_open, 'ok' if ok else 'FAIL')
        if not ok:
            failed.append(action.name)
            print('    worst edge (mesh, frame, rest ends, weights, rest length):', worst_where)
    rig.animation_data.action = None
    scene.frame_set(0)
    print('GATES', 'FAIL ' + ', '.join(failed) if failed else 'PASS', f'({len(open_verts[meshes[0].name])} open-edge '
          'vertices per leg)')
    return not failed


def main():
    options = args()
    out = Path(options['out'])
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = FPS
    leg = procedural_leg() if options['mesh'] == 'procedural' else imported_leg(options['mesh'])
    normalise(leg)
    marks = landmarks(leg)
    print('LANDMARKS', {k: (tuple(round(c, 1) for c in v) if isinstance(v, Vector) else v)
                        for k, v in marks.items() if k != 'digits'},
          [[tuple(round(c, 1) for c in p) for p in d] for d in marks['digits']])
    rig = build_rig(marks)
    make_side_meshes(leg, rig, marks)
    controls = setup_controls(rig)
    specs = clip_specs()
    baked = []
    for name, spec in specs.items():
        baked.append(key_clip(rig, controls, name, spec))
    # Constraints and controls off before export; the baked actions hold the motion.
    for bone in rig.pose.bones:
        for constraint in list(bone.constraints):
            bone.constraints.remove(constraint)
        bone.location = Vector()
        bone.rotation_quaternion = Quaternion()
    for side in ('R', 'L'):
        bpy.data.objects.remove(controls[side])
        bpy.data.objects.remove(bpy.data.objects[f'Pole{side}'])
    for action in list(bpy.data.actions):
        if action.name.startswith('_src_'):
            bpy.data.actions.remove(action)
    rig.animation_data.action = None
    if not mesh_gates(rig, [o for o in bpy.data.objects if o.type == 'MESH' and o.parent is rig], baked):
        raise SystemExit('mesh gates failed: not exported')
    name = options['name']
    bpy.ops.wm.save_as_mainfile(filepath=str(out / f'{name}.blend'))
    export(out / f'{name}.glb', baked, lambda n: 'claws' + n)
    keys = text_keys(specs, 'claws')
    (out / f'{name}.textkeys.json').write_text(json.dumps(keys, indent=1))
    # Today's engine plays an unarmed kit's handtohand<action> clips and casts with casttarget.
    h2h = {'breath': 'casttarget'}
    export(out / f'{name}_h2h.glb', baked, lambda n: h2h.get(n, 'handtohand' + n))
    h2h_keys = {h2h.get(k[len('claws'):], 'handtohand' + k[len('claws'):]): v for k, v in keys.items()}
    (out / f'{name}_h2h.textkeys.json').write_text(json.dumps(h2h_keys, indent=1))
    print('EXPORTED', out / f'{name}.glb', len(baked), 'clips')
    if options.get('install'):
        # The engine reads engine/view_model raw (no cooking): the export and its text keys, copied as they are.
        install = Path(options['install'])
        install.mkdir(parents=True, exist_ok=True)
        for file in (f'{name}.glb', f'{name}.textkeys.json'):
            shutil.copyfile(out / file, install / file)
            (install / file).chmod(0o644)
        print('INSTALLED', install / f'{name}.glb')


main()
