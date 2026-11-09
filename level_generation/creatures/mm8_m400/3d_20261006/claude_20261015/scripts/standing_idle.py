"""Standing v2 (2026-10-18, user review of the reduced model: "he should do something, at least breathe"; the near
arm hung with a bent, pressed-in elbow while the far hand reached forward). Runs after polish_motion.py on
master_motion.blend and saves it again.

Base pose: Standing v1 frame 0 with both arms re-posed like the native m400sa frames (arms hanging slightly forward and
out, elbows ~150 deg, hands beside the front of the thighs), each arm by a two-bone solve that keeps the bone roll.
Idle layered on that base, 4.0 s seamless loop at 48 Hz:
- breathing (two breaths): chest extension, clavicles lift, neck counters so the head stays steady;
- weight shift (one cycle): pelvis sways over each foot with a small roll and yaw, spine counter-rolls,
  legs re-solved every frame so both feet stay exactly where they are in the base pose;
- head drift (slow yaw/nod), arms swing slightly with a lag, elbows flex a little on each inhale.
Hit/Fidget/Death eased from/to the v1 Standing frame 0: their arm bones get the same base correction, in full where
the clip holds the v1 standing pose for that bone, otherwise only in the polish_motion ease ranges.
The previous clips are kept as actions Standing_v1, Hit_v1, Fidget_v1 and Death_v1 (fake user); reruns start from them."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'master_motion.blend'))
rig = bpy.data.objects['Lizardman_Rig']; body = bpy.data.objects['Lizardman_Body']; sc = bpy.context.scene
FPS = 48; LOOP = 4.0; N = int(LOOP * FPS)
ARM_BONES = [s + n for s in ['Left', 'Right'] for n in ['Arm', 'ForeArm', 'Hand']]
for t in rig.animation_data.nla_tracks:
    t.mute = True
if 'Standing_v1' not in bpy.data.actions:
    old = bpy.data.actions['Standing'].copy(); old.name = 'Standing_v1'; old.use_fake_user = True
v1 = bpy.data.actions['Standing_v1']


def activate(action, frame):
    rig.animation_data.action = action; rig.animation_data.action_slot = action.slots[0]
    sc.frame_set(int(frame), subframe=float(frame % 1))


def snapshot():
    return {b.name: (b.location.copy(), b.rotation_quaternion.copy(), b.scale.copy()) for b in rig.pose.bones}


def restore(snap):
    for b in rig.pose.bones:
        b.location, b.rotation_quaternion, b.scale = (x.copy() for x in snap[b.name])
    bpy.context.view_layer.update()


def turn(pb, q, pivot=None):
    """Rotate a pose bone by armature-space quaternion q about pivot (default its head)."""
    m = pb.matrix.copy(); c = pb.head.copy() if pivot is None else pivot
    pb.matrix = Matrix.Translation(c) @ q.to_matrix().to_4x4() @ Matrix.Translation(-c) @ m
    bpy.context.view_layer.update()


def axis_angle(axis, degrees):
    return Quaternion(Vector(axis).normalized(), math.radians(degrees))


def aim(pb, child, target):
    """Turn pb about its head so that child's head points at target (minimal rotation keeps the roll)."""
    turn(pb, (child.head - pb.head).rotation_difference(target - pb.head))


def two_bone(upper, lower, end, target, pole):
    a = (lower.head - upper.head).length; b = (end.head - lower.head).length
    root = upper.head.copy(); delta = target - root; dist = min(delta.length, a + b - 1e-4); direction = delta.normalized()
    side = pole - root; side = (side - direction * side.dot(direction)).normalized()
    along = (a * a - b * b + dist * dist) / (2 * dist)
    joint = root + direction * along + side * math.sqrt(max(a * a - along * along, 0))
    aim(upper, lower, joint); aim(lower, end, root + direction * dist)


pb = rig.pose.bones
activate(v1, 0); rig.animation_data.action = None; v1_base = snapshot()
# Arms like the native standing frames: hanging slightly forward and out, elbows behind and outward.
for s, x in [('Left', 1), ('Right', -1)]:
    shoulder = pb[s + 'Arm'].head.copy(); hand_local = pb[s + 'Hand'].rotation_quaternion.copy()
    target = Vector((x * .31, -.07, shoulder.z - .425)); pole = (shoulder + target) / 2 + Vector((x * .25, .30, 0))
    two_bone(pb[s + 'Arm'], pb[s + 'ForeArm'], pb[s + 'Hand'], target, pole)
    # relaxed wrist: half of the v1 swing, palm toward the thigh as in v1's hanging right hand
    pb[s + 'Hand'].rotation_quaternion = Quaternion().slerp(hand_local, .5)
    bpy.context.view_layer.update()
base = snapshot()
feet = {s: (pb[s + 'Foot'].matrix.copy(), pb[s + 'Leg'].head.copy()) for s in ['Left', 'Right']}

act = bpy.data.actions['Standing']
for layer in act.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for fc in list(bag.fcurves):
                bag.fcurves.remove(fc)
rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
w = 2 * math.pi / LOOP
for f in range(N + 1):
    t = (f % N) / FPS
    restore(base)
    sway = math.sin(w * t); sway2 = math.sin(w * t + math.pi / 2)
    inhale = .5 - .5 * math.cos(2 * w * t); lag = .5 - .5 * math.cos(2 * w * t - .6)
    hips = pb['Hips']
    m = hips.matrix.copy(); m.translation.x += .014 * sway; m.translation.z -= .004 * abs(sway); hips.matrix = m
    bpy.context.view_layer.update()
    turn(hips, axis_angle((0, 1, 0), -1.2 * sway) @ axis_angle((0, 0, 1), 1.5 * sway2))
    for name, k in [('Spine02', .5), ('Spine01', .4), ('Spine', .25)]:
        turn(pb[name], axis_angle((0, 1, 0), 1.2 * k * sway) @ axis_angle((0, 0, 1), -1.5 * k * sway2))
    turn(pb['Spine01'], axis_angle((1, 0, 0), -2.8 * inhale)); turn(pb['Spine'], axis_angle((1, 0, 0), -2.0 * inhale))
    turn(pb['LeftShoulder'], axis_angle((0, 1, 0), -4.0 * inhale)); turn(pb['RightShoulder'], axis_angle((0, 1, 0), 4.0 * inhale))
    turn(pb['neck'], axis_angle((1, 0, 0), 2.6 * inhale) @ axis_angle((0, 0, 1), 2.0 * math.sin(w * t + .6)))
    turn(pb['Head'], axis_angle((0, 0, 1), 2.5 * math.sin(w * t + .9)) @ axis_angle((1, 0, 0), 1.2 * math.sin(2 * w * t + 1.0)))
    for s, x, ph in [('Left', 1, 0), ('Right', -1, .5)]:
        swing = 1.6 * math.sin(w * t + ph + .8)
        turn(pb[s + 'Arm'], axis_angle((1, 0, 0), swing) @ axis_angle((0, 1, 0), -x * 1.2 * lag))
        turn(pb[s + 'ForeArm'], axis_angle((1, 0, 0), -3.0 * lag))
    for s in ['Left', 'Right']:
        foot_m, knee = feet[s]
        knee = knee + Vector((.014 * sway, 0, 0)) * .5
        two_bone(pb[s + 'UpLeg'], pb[s + 'Leg'], pb[s + 'Foot'], foot_m.translation.copy(), knee + Vector((0, -.3, 0)))
        pb[s + 'Foot'].matrix = foot_m; bpy.context.view_layer.update()
    for b in pb:
        for prop in ['location', 'rotation_quaternion', 'scale']:
            b.keyframe_insert(prop, frame=f)
# quaternion sign continuity and linear keys
for layer in act.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for b in pb:
                curves = [bag.fcurves.find('pose.bones[' + json.dumps(b.name) + '].rotation_quaternion', index=i) for i in range(4)]
                if any(c is None for c in curves):
                    continue
                prev = None
                for k in range(len(curves[0].keyframe_points)):
                    q = [c.keyframe_points[k].co.y for c in curves]
                    if prev is not None and sum(x * y for x, y in zip(prev, q)) < 0:
                        for c in curves:
                            c.keyframe_points[k].co.y *= -1
                        q = [-x for x in q]
                    prev = q
            for fc in bag.fcurves:
                for key in fc.keyframe_points:
                    key.interpolation = 'LINEAR'
strip = next(t for t in rig.animation_data.nla_tracks if t.name == 'Standing').strips[0]
strip.action_frame_start = 0; strip.action_frame_end = N; strip.frame_end = N

# Carry the arm correction into the one-shots that ease from/to the v1 standing pose.
correction = {n: base[n][1] @ v1_base[n][1].inverted() for n in ARM_BONES}
report = {}
for name in ['Hit', 'Fidget', 'Death']:
    if name + '_v1' not in bpy.data.actions:
        keep = bpy.data.actions[name].copy(); keep.name = name + '_v1'; keep.use_fake_user = True
    a = bpy.data.actions[name]; src = bpy.data.actions[name + '_v1']; end = int(src.frame_range[1]); poses = []
    for frame in range(end + 1):
        activate(src, frame); poses.append(snapshot())
    held = {n: max(math.degrees(p[n][1].rotation_difference(v1_base[n][1]).angle) for p in poses) < 1.0 for n in ARM_BONES}
    report[name] = {n: 'full' if held[n] else 'ease' for n in ARM_BONES}
    rig.animation_data.action = a; rig.animation_data.action_slot = a.slots[0]
    for frame in range(end + 1):
        phase = min(1, frame / 3)
        if name != 'Death':
            phase = min(phase, (end - frame) / 4)
        phase = phase * phase * (3 - 2 * phase)
        for n in ARM_BONES:
            k = 1.0 if held[n] else 1 - phase
            q = Quaternion().slerp(correction[n], k) @ poses[frame][n][1]
            pb[n].rotation_quaternion = q; pb[n].keyframe_insert('rotation_quaternion', frame=frame)
activate(act, 0)
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'master_motion.blend'))
print('STANDING_V2', json.dumps({'frames': N, 'seconds': LOOP, 'carry': report}), flush=True)
