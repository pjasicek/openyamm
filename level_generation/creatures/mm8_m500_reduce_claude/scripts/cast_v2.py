"""Cast v2 for the Water Elemental (user: "some proper casting animation with 2 hands, attack can use the same one").
Both hands gather a charge close in front of the chest, palms facing each other with the fingers curled, while the
trunk leans back and the head rises; then both palms thrust forward together at shoulder height, fingers spread and
pointing up, trunk and head leaning in, the tail coil bracing; release at 0.875 s, a short hold and a smooth return
to the Standing pose at 1.375 s (same length and impact as the production Cast/Attack, so actors.yml is unchanged).

Posed on the production rig (mm8_m500_claude/work/anim_uv_brow.blend, opened read only) with the production posing
code of mm8_m500_claude/scripts/animate_water.py (tail curve, trunk chain, two-bone arm IK in the chest frame, floor
lift on Root); the choreography is a set of keyed states eased with smoothstep. The palm orientation is solved per
frame: each hand turns about the wrist so its palm normal and finger direction meet the state's target directions
(blended by the state's weight), so the IK arms keep their bone lengths. Sampled at 48 fps.
Usage: blender -b -P cast_v2.py  -> work/cast_v2.glb (one action, Cast), work/cast_v2.json (palm sockets, floor,
edge stretch per frame)."""
import bpy
import json
import math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion

HERE = Path(__file__).resolve().parents[1]
SRC = HERE.parent / 'mm8_m500_claude'
bpy.ops.wm.open_mainfile(filepath=str(SRC / 'work/anim_uv_brow.blend'))
rig, body = bpy.data.objects['Rig'], bpy.data.objects['Body']
scene = bpy.context.scene
FPS, LENGTH, RELEASE = 48, 1.375, .875
data = json.loads((SRC / 'work/rig.json').read_text())
bones = data['bones']
rest = {n: rig.data.bones[n].matrix_local.copy() for n in bones}
relative = {n: rest[b['parent']].inverted() @ rest[n] if b['parent'] else rest[n] for n, b in bones.items()}
tail0, trunk0 = np.array(data['tail']), np.array(data['trunk'])
tailLength = np.linalg.norm(np.diff(tail0, axis=0), axis=1)
trunkLength = np.linalg.norm(np.diff(trunk0, axis=0), axis=1)
edges = np.array([e.vertices[:] for e in body.data.edges])

# Keyed states: time and values. Arm offsets are (outward, back, up) from the wrist's rest point in the chest frame,
# the x part mirrored per side; 'S' is the production Standing pose (offset -.18, .10, .10, everything else zero).
STAND = dict(arm=(-.18, .10, .10), pole=(.08, .08, .05), pitch=0, neck=0, head=0, jaw=0, palm=0, curl=0, spread=0, tail=0, tip=0)
STATES = [
    (0.0, STAND),
    (.50, dict(arm=(-.35, .00, .16), pole=(.16, .08, -.04), pitch=-.20, neck=-.08, head=.14, jaw=.05, palm=1, curl=.30, spread=.02,
               tail=.04, tip=.05, facing='gather')),
    (.68, dict(arm=(-.37, .03, .13), pole=(.16, .08, -.04), pitch=-.24, neck=-.10, head=.16, jaw=.06, palm=1, curl=.38, spread=.0,
               tail=.06, tip=.08, facing='gather')),
    (RELEASE, dict(arm=(-.38, -.30, .22), pole=(.12, .04, -.06), pitch=.22, neck=.14, head=-.20, jaw=.22, palm=1, curl=-.12, spread=.16,
                   tail=-.10, tip=-.03, facing='push')),
    (1.0, dict(arm=(-.37, -.27, .20), pole=(.12, .04, -.06), pitch=.19, neck=.12, head=-.17, jaw=.15, palm=1, curl=-.10, spread=.14,
               tail=-.08, tip=-.02, facing='push')),
    (LENGTH, STAND),
]


def smooth(x):
    x = min(1., max(0., x)); return x * x * (3 - 2 * x)


def state(t):
    """values and the palm facings (with weights) at time t"""
    for (t0, a), (t1, b) in zip(STATES, STATES[1:]):
        if t0 <= t <= t1:
            f = smooth((t - t0) / (t1 - t0)); break
    out = {}
    for k, v in STAND.items():
        va, vb = a.get(k, v), b.get(k, v)
        out[k] = tuple(x * (1 - f) + y * f for x, y in zip(va, vb)) if isinstance(v, tuple) else va * (1 - f) + vb * f
    facings = {}
    for s, w in ((a, 1 - f), (b, f)):
        if 'facing' in s:
            facings[s['facing']] = facings.get(s['facing'], 0) + w * s['palm']
    return out, facings


def unit(v):
    return v / max(np.linalg.norm(v), 1e-9)


def matrix(rot, point):
    m = rot.to_4x4(); m.translation = Vector(point); return m


def frame(axis, tail=False):
    y = unit(np.array(axis))
    x = unit(np.cross(y, [0, 0, 1])) if tail else unit(np.array([1., 0, 0]) - y * y[0])
    return Matrix(np.column_stack([x, y, np.cross(x, y)]))


def palm_axes():
    """Per hand, in the hand bone's rest frame: the finger direction (wrist to the mean fingertip), the palm normal
    (the flattest axis of the vertices weighted to the hand and its digits, turned towards the body: palms face the
    flanks at rest) and, per digit, its direction and lateral place for the spread. The digit bones' own axes are not
    consistent between digits, so curl and spread use these directions instead."""
    out = {}
    groups = {g.index: g.name for g in body.vertex_groups}
    for side, sign in [('L', 1), ('R', -1)]:
        hand = rest[f'{side}_Hand']; inv = hand.to_3x3().inverted(); wrist = np.array(hand.translation)
        names = {f'{side}_Hand'} | {n for d in data['fingers'][side] for n in d['names']}
        pts = np.array([v.co[:] for v in body.data.vertices
                        if sum(g.weight for g in v.groups if groups[g.group] in names) > .5])
        tips = np.array([d['points'][-1] for d in data['fingers'][side]])
        fingers = unit(tips.mean(0) - wrist)
        q = pts - pts.mean(0); q -= np.outer(q @ fingers, fingers)
        normal = np.linalg.svd(q, full_matrices=False)[2][1]   # [2] is the removed finger axis
        normal = unit(normal - fingers * (normal @ fingers))
        if normal[0] * sign > 0:
            normal = -normal
        lateral = unit(np.cross(normal, fingers))
        digits = []
        for d in data['fingers'][side]:
            p = np.array(d['points'])
            digits.append((np.array(inv @ Vector(unit(p[-1] - p[0]))), float((p[0] - tips.mean(0)) @ lateral)))
        span = max(abs(x[1]) for x in digits)
        out[side] = (np.array(inv @ Vector(fingers)), np.array(inv @ Vector(normal)),
                     [(dv, l / span) for dv, l in digits])
    return out


PALM = palm_axes()


def facing_targets(kind, sign, chest):
    """wanted finger direction and palm normal (world) for a facing, in the chest frame"""
    if kind == 'gather':   # palms toward each other, fingers forward and up
        fingers, normal = (0, -.6, .8), (-sign, 0, 0)
    else:                  # palms toward the target, fingers up and slightly in
        fingers, normal = (-sign * .25, .1, 1.), (-sign * .15, -1, 0)
    f = unit(np.array(chest @ Vector(fingers))); n = np.array(chest @ Vector(normal))
    return f, unit(n - f * (n @ f))


def turn(fw, nw, fd, nd):
    """rotation taking the (fingers, normal) frame onto the wanted one"""
    a = Matrix(np.column_stack([fw, nw, np.cross(fw, nw)])); b = Matrix(np.column_stack([fd, nd, np.cross(fd, nd)]))
    return b @ a.transposed()


def pose(t):
    v, facings = state(t)
    matrices = {'Root': rest['Root'].copy()}
    tail = tail0.copy()
    for i, length in enumerate(tailLength):
        u = (i + .5) / len(tailLength)
        angle = 1.0 * u + .025 * math.sin(-u * 3) + v['tail'] * u   # production Standing at its frame 0
        w = (i + 1) / len(tailLength)
        z = .14 + .09 * math.exp(-6 * w) + (.50 + v['tip']) * smooth((w - .82) / .18)
        dz = np.clip(z - tail[i, 2], -length * .95, length * .95)
        horizontal = math.sqrt(max(1e-8, length * length - dz * dz))
        tail[i + 1] = tail[i] + [math.sin(angle) * horizontal, math.cos(angle) * horizontal, dz]
        name = data['tail_names'][i]
        rot = frame(tail[i + 1] - tail[i], True) @ frame(tail0[i + 1] - tail0[i], True).transposed()
        matrices[name] = matrix(rot @ rest[name].to_3x3(), tail[i])
    trunk = trunk0.copy()
    for i, length in enumerate(trunkLength):
        u = (i + 1) / len(trunkLength)
        direction = np.array(Matrix.Rotation(v['pitch'] * u, 3, 'X') @ Vector(unit(trunk0[i + 1] - trunk0[i])))
        trunk[i + 1] = trunk[i] + length * direction
        name = data['spine_names'][i]
        rot = Vector(trunk0[i + 1] - trunk0[i]).rotation_difference(Vector(direction)).to_matrix()
        matrices[name] = matrix(rot @ rest[name].to_3x3(), trunk[i])
    for name, b in bones.items():
        if name in matrices:
            continue
        m = matrices[b['parent']] @ relative[name]
        if name == 'Neck':
            m = m @ Matrix.Rotation(v['neck'], 4, 'X')
        elif name == 'Head':
            m = m @ Matrix.Rotation(v['head'], 4, 'X')
        elif name == 'Jaw':
            m = m @ Matrix.Rotation(v['jaw'], 4, 'X')
        if name.startswith('Dorsal_'):   # fins and fan held as in the Standing pose's frame 0
            m = m @ Matrix.Rotation(.045 * math.sin(-int(name.split('_')[-1]) * .5), 4, 'Z')
        elif name == 'Caudal':
            m = m @ Matrix.Rotation(.07 * math.sin(-1.5), 4, 'Y')
        matrices[name] = m
    chest = data['spine_names'][-1]
    carried = matrices[chest] @ rest[chest].inverted()
    rotation = carried.to_3x3()
    for side, sign in [('L', 1), ('R', -1)]:
        names = data['arms'][side]['names']
        p = np.array(data['arms'][side]['points'])
        shoulder = np.array(matrices[names[0]].translation)
        ox, oy, oz = v['arm']
        target = np.array(carried @ Vector(p[2]) + rotation @ Vector((sign * ox, oy, oz)))
        upper, lower = np.linalg.norm(p[1] - p[0]), np.linalg.norm(p[2] - p[1])
        axis = unit(target - shoulder)
        length = np.clip(np.linalg.norm(target - shoulder), abs(upper - lower) + .003, upper + lower - .003)
        target = shoulder + axis * length
        # elbows out and a little down and back while casting (production pole when standing)
        px, py, pz = v['pole']
        pole = np.array(carried @ Vector(p[1]) + rotation @ Vector((sign * px, py, pz))) - shoulder
        pole = unit(pole - axis * np.dot(pole, axis))
        along = (upper * upper - lower * lower + length * length) / (2 * length)
        elbow = shoulder + axis * along + pole * math.sqrt(max(0, upper * upper - along * along))
        for i, (start, end) in enumerate([(shoulder, elbow), (elbow, target)]):
            old = rotation @ Vector(p[i + 1] - p[i])
            delta = old.rotation_difference(Vector(end - start)).to_matrix()
            matrices[names[i]] = matrix(delta @ rotation @ rest[names[i]].to_3x3(), start)
        delta = matrices[names[1]].to_3x3() @ rest[names[1]].to_3x3().transposed()
        hand = delta @ rest[names[2]].to_3x3()
        # turn the palm towards the state's facing (weights of the two neighbouring states)
        fl, nl, digits = PALM[side]
        fw, nw = np.array(hand @ Vector(fl)), np.array(hand @ Vector(nl))
        turns = {k: turn(fw, nw, *facing_targets(k, sign, rotation)).to_quaternion() for k in facings}
        total = sum(facings.values())
        q = Quaternion()
        if total > 0:
            q = turns.get('gather', turns.get('push'))
            if len(turns) == 2:
                q = turns['gather'].slerp(turns['push'], facings['push'] / total)
            q = Quaternion().slerp(q, min(1., total))
        hand = q.to_matrix() @ hand
        matrices[names[2]] = matrix(hand, target)
        nw = np.array(hand @ Vector(nl))
        for k, digit in enumerate(data['fingers'][side]):
            dl, lateral = digits[k]
            for i, name in enumerate(digit['names']):
                m = matrices[bones[name]['parent']] @ relative[name]
                d = np.array(m.to_3x3() @ rest[name].to_3x3().inverted() @ rest[f'{side}_Hand'].to_3x3() @ Vector(dl))
                turn_m = Matrix.Identity(3)
                if i == 0:   # fan the digits out about the palm normal
                    turn_m = Matrix.Rotation(v['spread'] * lateral, 3, Vector(nw))
                if i < 2:    # curl towards the palm; the claws stay rigid, as in production
                    turn_m = Matrix.Rotation(v['curl'], 3, Vector(unit(np.cross(d, nw)))) @ turn_m
                m = matrix(turn_m @ m.to_3x3(), m.translation)
                matrices[name] = m
    for name, b in bones.items():
        parent = b['parent']
        rig.pose.bones[name].matrix_basis = relative[name].inverted() @ (
            matrices[parent].inverted() @ matrices[name] if parent else matrices[name])
    bpy.context.view_layer.update()
    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh(); minimum = min(x.co.z for x in mesh.vertices); evaluated.to_mesh_clear()
    lift = max(0, -minimum)
    if lift:
        rig.pose.bones['Root'].location += rest['Root'].to_3x3().transposed() @ Vector((0, 0, lift))
        bpy.context.view_layer.update()
    return lift


def bake():
    stand = bpy.data.actions['Standing']
    rig.animation_data.action = stand; scene.render.fps = 24; scene.frame_set(1)
    standing = {n: (rig.pose.bones[n].location.copy(), rig.pose.bones[n].rotation_quaternion.copy()) for n in bones}
    count = round(LENGTH * FPS); keys = {n: [] for n in bones}; report = []
    for k in range(count + 1):
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis.identity()
        t = k / FPS; lift = pose(t)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = ev.to_mesh()
        c = np.array([x.co[:] for x in mesh.vertices]); ev.to_mesh_clear()
        length = np.linalg.norm(c[edges[:, 1]] - c[edges[:, 0]], axis=1)
        palms = {s: list(bpy.data.objects[f'Socket_Palm{s}'].matrix_world.translation) for s in 'LR'}
        report.append(dict(t=t, lift=lift, min_z=float(c[:, 2].min()), palms=palms, length=length))
        for n in bones:
            pb = rig.pose.bones[n]; q = pb.rotation_quaternion.copy()
            if keys[n] and keys[n][-1][1].dot(q) < 0:
                q.negate()
            keys[n].append((pb.location.copy(), q))
    # stretch against the rest pose
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = ev.to_mesh()
    c = np.array([x.co[:] for x in mesh.vertices]); ev.to_mesh_clear()
    rest_len = np.maximum(np.linalg.norm(c[edges[:, 1]] - c[edges[:, 0]], axis=1), 1e-6)
    for r in report:
        st = r.pop('length') / rest_len; r['stretch_p99'] = float(np.percentile(st, 99)); r['stretch_max'] = float(st.max())
    start = max(max((keys[n][0][0] - standing[n][0]).length, keys[n][0][1].rotation_difference(standing[n][1]).angle)
                for n in bones)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    action = bpy.data.actions.new('Cast'); action.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = action; scene.render.fps = FPS
    for k in range(count + 1):
        for n in bones:
            pb = rig.pose.bones[n]; pb.location, pb.rotation_quaternion = keys[n][k]
            pb.keyframe_insert('location', frame=k + 1, group=n); pb.keyframe_insert('rotation_quaternion', frame=k + 1, group=n)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
    scene.frame_set(1)
    for o in bpy.data.objects:
        o.select_set(o in (rig, body))
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(filepath=str(HERE / 'work/cast_v2.glb'), use_selection=True, export_format='GLB',
                              export_yup=True, export_animations=True, export_animation_mode='ACTIONS',
                              export_force_sampling=False, export_frame_step=1, export_skins=True,
                              export_all_influences=False, export_attributes=False, export_morph=False,
                              export_reset_pose_bones=True, export_anim_slide_to_zero=True, export_extras=False,
                              export_materials='NONE')
    summary = dict(start_vs_standing=start, min_z=min(r['min_z'] for r in report), max_lift=max(r['lift'] for r in report),
                   stretch_max=max(r['stretch_max'] for r in report), stretch_p99=max(r['stretch_p99'] for r in report),
                   release=next(r for r in report if abs(r['t'] - RELEASE) < 1e-6), frames=report)
    (HERE / 'work/cast_v2.json').write_text(json.dumps(summary, indent=1) + '\n')
    print('CAST_V2', json.dumps({k: v for k, v in summary.items() if k != 'frames'}))


bake()
