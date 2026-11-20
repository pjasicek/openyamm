"""Sprint for the MM8 wererat rat form (2026-10-31 sprint pass), keyed on work/rat_gait2.blend.

The engine picks an optional third locomotion clip (actors.yml `animation.sprint`) when the actor moves much faster
than its run: MAW's fast melee monsters chase at 2.83-4.14 model units/s here, while Run2 is authored for 2.34
(gait_gate.py: sprint target 3.23, fitting 2.76-3.77).
  Sprint  full bound, 34 frames at 96 fps (0.3542 s), stride 1.17 m (3.30 m/s, 1.5x Run2's stride at 0.94x its cadence). Same
          footfall phases as Run2 (HL 0, HR 0.06, FL 0.44, FR 0.52), because the engine shares one gait phase across
          walk, run and sprint, but a lower duty (hind 0.22, front 0.19): a longer extended flight (0.28-0.44) and a
          long gathered flight (0.71-1.0). The spine arches hard at hind touchdown (hind feet planted far forward under
          the belly) and stretches in the extended flight (front feet reaching). The rat's legs are short (front
          chain 0.147 m), so the extra stride comes from the body itself: it slides back over the planted feet in
          both stances (hips over the hind feet, chest over the front feet) and surges forward in both flights.
          The chest also drops into the front stance for reach. The front paws kick back and tuck under the chest
          after lift-off and sweep forward late; the hind paws trail through the extended flight, then swing forward
          under the belly.
Feet are IK footholds moving backward at exactly the clip's ground speed through stance (planted, paws flat). Floor
rules each frame: the tail clamp of anim_gait2.py, and a swinging paw curls its toes down only as far as its lift
clears (floor_pitch); the report gives the lowest point and the IK reach of every planted
foot (work/sprint_report.json). Saves work/rat_sprint.blend and the donor export work/sprint_donor.glb, whose Sprint
add_clips.py appends to the installed export. With SPRINT_DRY=1 it only prints the per-frame diagnostics.
"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = os.environ.get('SPRINT_DRY') == '1'
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work/rat_gait2.blend'))
rig = bpy.data.objects['Rat_Rig']; mesh = bpy.data.objects['Rat']; sc = bpy.context.scene
# Keyed at 96 fps (twice the other clips): the body moves 3.4 cm per key, so the planted legs' linear in-between
# rotations keep the paws near the floor (6 mm under it at 48 fps). rat_sprint.blend is saved at this rate.
FPS = 96
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
P.reset(rig)
REST = {b.name: (rig.matrix_world @ b.matrix).copy() for b in rig.pose.bones}
WRIST = {s: REST[f'FrontPaw_{s}'].translation.copy() for s in 'LR'}
ANKLE = {s: REST[f'HindPaw_{s}'].translation.copy() for s in 'LR'}
SIDE = {'L': 1.0, 'R': -1.0}
CHAIN = {('front', s): (rig.pose.bones[f'UpperArm_{s}'].length + rig.pose.bones[f'ForeArm_{s}'].length) for s in 'LR'}
CHAIN.update({('hind', s): (rig.pose.bones[f'Thigh_{s}'].length + rig.pose.bones[f'Shin_{s}'].length) for s in 'LR'})
UPPER = {'front': 'UpperArm_{}', 'hind': 'Thigh_{}'}


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def loop(keys, p):
    """Periodic C1 cubic through (phase, value) keys (phases in [0, 1), sorted), tangents from the neighbours."""
    n = len(keys)
    p %= 1.0
    i = max(k for k in range(n) if keys[k][0] <= p) if p >= keys[0][0] else -1

    def key(k):
        t, v = keys[k % n]
        return t + math.floor(k / n), v
    (t0, v0), (t1, v1), (t2, v2), (t3, v3) = key(i - 1), key(i), key(i + 1), key(i + 2)
    m1 = (v2 - v0) / (t2 - t0) * (t2 - t1); m2 = (v3 - v1) / (t3 - t1) * (t2 - t1)
    s = (p - t1) / (t2 - t1)
    return ((2 * s ** 3 - 3 * s ** 2 + 1) * v1 + (s ** 3 - 2 * s ** 2 + s) * m1 + (-2 * s ** 3 + 3 * s ** 2) * v2
            + (s ** 3 - s ** 2) * m2)


def rot(name, axis, deg, pivot=None):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg, pivot)


def set_world_rot(name, q):
    b = rig.pose.bones[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, Vector((1, 1, 1))); bpy.context.view_layer.update()


REACH = []
TRACE = []


def place_leg(kind, side, target, pitch=0.0, planted=False):
    """As anim_gait2.place_leg: target = wrist/ankle world point; pitch tilts the paw (+ = toes down)."""
    shoulder = rig.matrix_world @ rig.pose.bones[UPPER[kind].format(side)].head
    if planted:
        REACH.append(((target - shoulder).length / CHAIN[(kind, side)], kind + side, round(target.y - shoulder.y, 3)))
    TRACE.append((kind + side, planted, round((target - shoulder).length / CHAIN[(kind, side)], 3),
                  round(target.y - shoulder.y, 3), round(shoulder.z, 3)))
    if kind == 'front':
        pole = target + Vector((SIDE[side] * 0.05, 0.25, 0.05))
        P.two_bone_ik(rig, f'UpperArm_{side}', f'ForeArm_{side}', target, pole)
        paw, rest = f'FrontPaw_{side}', REST[f'FrontPaw_{side}']
    else:
        pole = target + Vector((SIDE[side] * 0.04, -0.25, 0.10))
        P.two_bone_ik(rig, f'Thigh_{side}', f'Shin_{side}', target, pole)
        paw, rest = f'HindPaw_{side}', REST[f'HindPaw_{side}']
    set_world_rot(paw, Quaternion(X, math.radians(pitch)) @ rest.to_quaternion())


def tail_wave(amp_yaw, amp_pitch, phase, lift=0.0):
    for i in range(1, 7):
        k = i / 6.0
        rot(f'Tail{i}', Z, amp_yaw * k * math.sin(2 * math.pi * (phase - 0.09 * i)))
        rot(f'Tail{i}', X, (lift if i == 1 else lift * 0.15) + amp_pitch * math.sin(2 * math.pi * (phase - 0.09 * i)))


def body(hips_d, hips_pitch, hips_roll, spine_pitch, spine_yaw, head_pitch, split=(0.35, 0.65)):
    """As anim_gait2.body, with the spine flexion shared unevenly (more in the chest than over the hips)."""
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(hips_d) @ root.matrix; bpy.context.view_layer.update()
    rot('Spine1', Y, hips_roll); rot('Spine1', X, hips_pitch)
    for n, s in zip(('Spine2', 'Spine3'), split):
        rot(n, X, spine_pitch * s); rot(n, Z, spine_yaw * s)
    rot('Neck1', X, head_pitch * 0.4); rot('Head', X, head_pitch * 0.6)


_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
CORE = np.array([n.startswith(('Spine', 'Neck', 'Head', 'Jaw')) for n in _dom])
_dg = bpy.context.evaluated_depsgraph_get()


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)


def clamp_tail():
    for i in range(1, 7):
        b = rig.pose.bones[f'Tail{i}']
        t = rig.matrix_world @ b.tail
        if t.z < 0.012:
            h = rig.matrix_world @ b.head
            d = t - h; L = d.length
            flat = Vector((d.x, d.y, 0)).normalized()
            dz = 0.012 - h.z
            target = h + flat * math.sqrt(max(L * L - dz * dz, 1e-6)) + Vector((0, 0, dz)) if abs(dz) < L else h + flat * L
            P.aim_bone(rig, b.name, target)


def foot(q, duty, travel, centre, lift, curl, sweep, peak, trail):
    """Foothold offset (dy, dz) and paw pitch for cycle position q (0 = touchdown). Stance moves the foot back by
    `travel` at constant speed; swing brings it forward between swing positions sweep[0] and sweep[1] (so the paw can
    stay back while it lifts and tucks), with the lift peaking near swing position `peak`. After lift-off the paw
    first kicks a further `trail` backwards, which it takes back as it swings forward."""
    if q < duty:
        return Vector((0, centre - travel / 2 + travel * (q / duty), 0)), 0.0, True
    u = (q - duty) / (1 - duty)
    w = ss((u - sweep[0]) / (sweep[1] - sweep[0]))
    k = math.log(0.5) / math.log(peak)
    z = lift * math.sin(math.pi * u ** k)
    back = trail * ss(u / sweep[0]) * (1 - w)
    return Vector((0, centre + travel / 2 - travel * w + back, z)), curl * math.sin(math.pi * u), False


def paw_slope(kind, side):
    """Rest length and downward slope (radians) of the paw bone (wrist/ankle to toe)."""
    rest = REST[f"{'FrontPaw' if kind == 'front' else 'HindPaw'}_{side}"]
    bone = rig.pose.bones[f"{'FrontPaw' if kind == 'front' else 'HindPaw'}_{side}"]
    d = rest.to_3x3() @ Vector((0, bone.length, 0))
    return bone.length, math.asin(max(0.0, -d.z) / bone.length)


def floor_pitch(kind, side, pitch, z):
    """Floor rule for a swinging paw: toes down by at most what the foothold's lift `z` clears (3 mm margin for the
    toe pad below the bone)."""
    length, slope = paw_slope(kind, side)
    room = math.sin(slope) + max(0.0, z - 0.003) / length
    return min(pitch, max(0.0, math.degrees(math.asin(min(1.0, room)) - slope)))


# ---------------------------------------------------------------- Sprint: full bound
S_N = 34
S_T, S_STRIDE = S_N / FPS, 1.17
# leg, side, touchdown phase (as Run2), duty
S_LEGS = (('hind', 'L', 0.00, 0.22), ('hind', 'R', 0.06, 0.22), ('front', 'L', 0.44, 0.19), ('front', 'R', 0.52, 0.19))
S_CENTRE = {'front': -0.013, 'hind': -0.062}    # stance centre relative to the rest foothold (+ = backward)
S_LIFT = {'front': 0.085, 'hind': 0.055}
S_SWEEP = {'front': (0.30, 0.88), 'hind': (0.15, 0.85)}
S_PEAK = {'front': 0.33, 'hind': 0.5}
S_TRAIL = {'front': 0.030, 'hind': 0.040}
# +1 arched (gathered: hind touchdown), -1 stretched (extended flight)
FLEX = [(0.00, 0.80), (0.14, 0.15), (0.30, -0.85), (0.38, -1.00), (0.48, -0.55), (0.62, 0.25), (0.78, 0.85),
        (0.92, 1.00)]
# body slide (+ = backward): back over the planted feet in both stances, forward in both flights
SLIDE = [(0.00, -0.030), (0.26, 0.020), (0.44, -0.012), (0.68, 0.036)]
# body height: low in the stances, high in the flights; the chest drops into the front stance
LIFT = [(0.00, -0.010), (0.12, -0.022), (0.35, 0.018), (0.47, -0.010), (0.58, -0.024), (0.76, 0.012), (0.87, 0.030)]


def sprint(t):
    p = (t / S_T) % 1.0
    P.reset(rig)
    flex = loop(FLEX, p)
    hips_pitch = -12.0 * flex
    spine_pitch = 6.0 + 22.0 * flex
    body(hips_d=Vector((0, loop(SLIDE, p), loop(LIFT, p))), hips_pitch=hips_pitch,
         hips_roll=1.0 * math.sin(2 * math.pi * p), spine_pitch=spine_pitch, spine_yaw=1.5 * math.sin(2 * math.pi * p),
         head_pitch=-0.8 * (hips_pitch + spine_pitch) - 2.0)
    tail_wave(5, 10, p + 0.2, lift=3 - 10 * flex)
    for kind, side, ph, duty in S_LEGS:
        off, pitch, planted = foot((p - ph) % 1.0, duty, S_STRIDE * duty, S_CENTRE[kind], S_LIFT[kind], 60,
                                   S_SWEEP[kind], S_PEAK[kind], S_TRAIL[kind])
        place_leg(kind, side, (WRIST if kind == 'front' else ANKLE)[side] + off, floor_pitch(kind, side, pitch, off.z),
                  planted)
    clamp_tail()


CLIPS = {'Sprint': (S_N, sprint)}
STRIDES = {'Sprint': S_STRIDE}


def key_action(name, n, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; act['loop'] = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows = [], []
    REACH.clear()
    for f in range(n + 1):
        TRACE.clear()
        fn((f % n) / FPS)
        co = mesh_co()
        lows.append((float(co[:, 2].min()), float(co[CORE, 2].min())))
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
        if f < n:
            print(f'F{f:02d} p={f / n:.3f} low {lows[-1][0] * 1000:+.1f} mm {_dom[int(co[:, 2].argmin())]:10} ' +
                  '  '.join(f"{leg}{'*' if pl else ' '}{r:.2f}/{dy:+.3f}/z{z:.3f}" for leg, pl, r, dy, z in TRACE),
                  flush=True)
    if DRY:
        return {'planted_reach_max': max(r for r, _, _ in REACH)}
    rig.animation_data.action = act
    prev = {}
    for f, pose in enumerate(poses):
        for b in rig.pose.bones:
            q, loc = pose[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc
            b.keyframe_insert('rotation_quaternion', frame=f + 1)
            b.keyframe_insert('location', frame=f + 1)
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'LINEAR'
    assert all(abs(abs(poses[0][k][0].dot(poses[-1][k][0])) - 1) < 1e-5 and
               (poses[0][k][1] - poses[-1][k][1]).length < 1e-5 for k in poses[0])
    rig.animation_data.action = None
    return {'frames': n, 'seconds': n / FPS, 'stride_m': STRIDES[name], 'speed': STRIDES[name] / (n / FPS),
            'lowest_m': min(l for l, _ in lows), 'core_lowest_m': min(c for _, c in lows),
            'planted_reach_max': max(r for r, _, _ in REACH),
            'reach_by_leg': {leg: [round(min(r for r, l, _ in REACH if l == leg), 3),
                                   round(max(r for r, l, _ in REACH if l == leg), 3),
                                   min(d for _, l, d in REACH if l == leg), max(d for _, l, d in REACH if l == leg)]
                             for leg in sorted({l for _, l, _ in REACH})}}


report = {}
for name, (n, fn) in CLIPS.items():
    report[name] = key_action(name, n, fn)
    print('CLIP', name, json.dumps(report[name]), flush=True)
if not DRY:
    json.dump(report, open(os.path.join(HERE, 'work/sprint_report.json'), 'w'), indent=2)
    sc.render.fps = FPS
    rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work/rat_sprint.blend'))
    for obj in bpy.data.objects:
        obj.select_set(obj in (mesh, rig))
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work/sprint_donor.glb'), use_selection=True,
        export_format='GLB', export_yup=True, export_animations=True, export_animation_mode='ACTIONS',
        export_force_sampling=True, export_frame_step=1, export_skins=True, export_all_influences=False,
        export_attributes=False, export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
        export_anim_slide_to_zero=True)
    print('SAVED rat_sprint.blend sprint_donor.glb')
