"""Procedural clips for the octopod (quadruped playbook: water creatures and segmented creatures). z 0 is the
waterline (the swimmer's origin, D-36); only what is above it is seen (outdoor water and DD-14's cistern draw opaque).
Every frame is a set of armature-space bone matrices converted to local bases:
- Root carries the death sink; Body (pivot at the head base) bobs, pitches, rolls and turns the whole creature;
  Head tilts the dome on the Body;
- each tentacle k is laid out from its hub joint J0 (moved with Body): bone i keeps its rest length and its rest
  orientation turned by D_i = Body * Rz(yaw_i) * Rn(-pitch_i), where pitch_i is its pitch change from rest (positive
  lifts it; Rn about the tentacle's own vertical plane normal) and yaw_i swings it about the vertical (positive
  toward +X from the front). The pitches come from target profiles (absolute pitch per bone in degrees):
  ARCH: the root bones dip into the water, the middle rises in a tall arch, the tip hooks over outward and down, as
  the native frames show the tentacles rising out of the lake; plus a wave travelling to the tip;
- FoamRoot (unparented) sways (a small turn back and forth) and pulses; it shrinks away on death.
Native Darkside 041 frames (front only): mon 0-7 the octopod at rest, tentacles weaving and curling; att 0-3 a purple
ink burst from under the face (att 1-2), then the head ducks under its tentacles (att 3).

  Standing  3.0 s loop   head bobbing on the water, every tentacle arching out of the water and weaving with its own
                         phase, tips curling and uncurling
  Walking   1.6 s loop   swimming on the surface: the star swept back (tentacles yawed toward the rear, lower arches
                         streaming behind), a pulse per cycle (arms draw in, then sweep back), head pitched forward
  Running   1.0 s loop   the same, swept further back, lower and faster
  Attack    1.2 s        the front tentacles (front pair and the one under the face) rear up tall and back, then lash
                         forward and down onto the party, the head lunging forward (impact), recover
  Hit       0.5 s        the head jerks back and ducks, the tentacles flinch up and curl
  Death     1.6 s        the tentacles flail up, the head tips back, the whole body sinks under the water while the
                         tentacles go limp; the foam ring shrinks away
  Dead      1.0 s        Death's last pose: sunk below the waterline (nothing above water; no corpse, as the sprite)
  Fidget    2.4 s        one side tentacle (the creature's left) rises tall and curls and uncurls its tip twice, the
                         head turning toward it
Reads work/anim_base.blend (or the given source), writes work/anim_v1.blend and work/anim_info.json.
Args: -- [<source.blend> [<output.blend>]] [clip ...]"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
BLENDS = [a for a in ARGS if a.endswith('.blend')]
ONLY = [a for a in ARGS if not a.endswith('.blend')]
SRC = BLENDS[0] if BLENDS else None
OUT = BLENDS[1] if len(BLENDS) > 1 else 'anim_v1.blend'
src = SRC or ('anim_v1.blend' if ONLY and os.path.exists(os.path.join(WORK, 'anim_v1.blend')) else 'anim_base.blend')
bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, src))
RJ = json.load(open(os.path.join(WORK, 'rig_v1.json')))
rig = bpy.data.objects['Octopod_Rig']; mesh = bpy.data.objects['Octopod']
FPS = 30
NSEG = RJ['n_seg']
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
if rig.animation_data:
    rig.animation_data.action = None
pbn = rig.pose.bones
for b in pbn:
    b.rotation_mode = 'QUATERNION'; b.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
BONES = rig.data.bones
R = {b.name: b.matrix_local.copy() for b in BONES}
RI = {k: v.inverted() for k, v in R.items()}
PARENT = {b.name: (b.parent.name if b.parent else None) for b in BONES}
ORDER = [b.name for b in BONES]
BODY_PIVOT = BONES['Body'].head_local.copy()
HEAD_PIVOT = BONES['Head'].head_local.copy()

ARMS = []
for A in RJ['arms']:
    k = A['k']; th = math.radians(A['azimuth_deg'])
    n = Vector((math.cos(th), math.sin(th), 0)); d = Vector((math.sin(th), -math.cos(th), 0))
    names = [f'Arm{k}_{i + 1}' for i in range(NSEG)]
    vecs = [BONES[nm].tail_local - BONES[nm].head_local for nm in names]
    rest_pitch = [math.degrees(math.atan2(v.z, v.dot(d))) for v in vecs]
    ARMS.append({'k': k, 'theta': A['azimuth_deg'], 'n': n, 'd': d, 'names': names, 'vecs': vecs,
                 'j0': BONES[names[0]].head_local.copy(), 'rest_pitch': rest_pitch})

# ---- per-tentacle character (height of the arch, phase, tip curl, idle yaw spread) ----------------------------------
H = [0.30, 1.00, 1.12, 0.92, 0.42, 0.98, 1.08, 0.96]
PH = [0.0, 1.3, 2.6, 0.7, 3.4, 1.9, 4.4, 5.2]
CURL = [0.0, 0.2, -0.1, 0.3, 0.0, 0.25, -0.15, 0.1]
SPREAD = [0, -6, 0, 4, 14, -4, 0, 6]                    # idle yaw: the front pair opens round the face

ARCH = [-24, -12, 30, 62, 78, 46, -14, -70]            # absolute pitch per bone (deg) of a tall arch
LOW = [-20, -14, -6, 6, 18, 14, -10, -40]              # a low arch streaming along the surface
SUNK = [-46, -30, -14, -4, -2, -4, -8, -16]           # a tentacle lying under the water (the front one; deaths)


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def bump(t, a, b):
    if t <= a or t >= b:
        return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** 2


def mix(a, b, u):
    return [x + (y - x) * u for x, y in zip(a, b)]


def rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, Vector(axis))


def follow(M, child):
    p = PARENT[child]
    return M[p] @ RI[p] @ R[child]


def arch_profile(h, curl=0.0, dip=0.0):
    """Absolute bone pitches: LOW..ARCH by height h (h > 1 rises taller), the tip curled by curl (+ lifts the tip,
    - hooks it further down), the root dipped by dip (degrees, + deeper)."""
    base = mix(LOW, ARCH, min(h, 1.0))
    if h > 1.0:
        base = [p + (h - 1.0) * w for p, w in zip(base, [0, 0, 18, 22, 10, 0, 0, 0])]
    base[6] += 30 * curl; base[7] += 55 * curl
    base[0] -= dip; base[1] -= 0.6 * dip
    return base


def wave(t, T, amp, ph, lag=0.75, grow=True):
    return [amp * ((0.35 + 0.65 * i / (NSEG - 1)) if grow else 1.0) * math.sin(2 * math.pi * t / T - lag * i + ph)
            for i in range(NSEG)]


# ---- one pose ----------------------------------------------------------------------------------------------------------
def build(spec):
    """spec: sink (m, Root down), bob (m), body_pitch/body_roll/body_yaw (deg; pitch + = nose down), body_y (m forward
    shift, - toward the front), head_pitch/head_yaw (deg), arms: list of 8 (pitch list, yaw list) absolute targets,
    foam_spin (deg), foam_scale."""
    M = {}
    sink = spec.get('sink', 0.0)
    M['Root'] = Matrix.Translation((0, 0, -sink)) @ R['Root']
    B = (Matrix.Translation((0, spec.get('body_y', 0.0), -sink + spec.get('bob', 0.0)))
         @ Matrix.Translation(BODY_PIVOT) @ rot(Z, spec.get('body_yaw', 0.0)) @ rot(X, -spec.get('body_pitch', 0.0))
         @ rot(Y, spec.get('body_roll', 0.0)) @ Matrix.Translation(-BODY_PIVOT))
    M['Body'] = B @ R['Body']
    Hm = (Matrix.Translation(HEAD_PIVOT) @ rot(Z, spec.get('head_yaw', 0.0)) @ rot(X, -spec.get('head_pitch', 0.0))
          @ Matrix.Translation(-HEAD_PIVOT))
    M['Head'] = B @ Hm @ R['Head']
    B3 = B.to_3x3()
    for A, (pitch, yaw) in zip(ARMS, spec['arms']):
        P = B @ A['j0']
        for i, name in enumerate(A['names']):
            dp = pitch[i] - A['rest_pitch'][i]
            D = B3 @ rot(Z, yaw[i]).to_3x3() @ Matrix.Rotation(math.radians(-dp), 3, A['n'])
            M[name] = Matrix.Translation(P) @ (D @ R[name].to_3x3()).to_4x4()
            P = P + D @ A['vecs'][i]
    fs = spec.get('foam_scale', 1.0)
    M['FoamRoot'] = rot(Z, spec.get('foam_spin', 0.0)) @ Matrix.Scale(fs, 4) @ R['FoamRoot']
    return M


def apply(M):
    for name in ORDER:
        m = M.get(name)
        if m is None:
            m = follow(M, name); M[name] = m
        p = PARENT[name]
        basis = RI[name] @ m if p is None else (RI[name] @ R[p]) @ (M[p].inverted() @ m)
        pbn[name].matrix_basis = basis
    bpy.context.view_layer.update()


_dg = bpy.context.evaluated_depsgraph_get()
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
FOAMV = _dom == 'FoamRoot'
HEADV = np.isin(_dom, ('Head', 'Body'))
TIPV = {k: np.array([n == f'Arm{k}_{NSEG}' for n in _dom]) for k in range(8)}


def mesh_co():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)


# ---- clips ---------------------------------------------------------------------------------------------------------------
def idle_arms(t, T, amp=7.0, yaw_amp=5.0, h_scale=1.0, curl_amp=0.35):
    arms = []
    w = 2 * math.pi * t / T
    for k in range(8):
        h = H[k] * h_scale * (1 + 0.08 * math.sin(w + PH[k]))
        curl = CURL[k] + curl_amp * math.sin(w + PH[k] + 1.2)
        pitch = [p + q for p, q in zip(arch_profile(h, curl), wave(t, T, amp, PH[k]))]
        yaw = [SPREAD[k] * (1 if i == 0 else 0.3) + y for i, y in
               enumerate(wave(t, T, yaw_amp, PH[k] + 0.8, lag=0.5))]
        if k == 0:
            pitch = [p + q for p, q in zip(mix(SUNK, arch_profile(0.55, 0.4), 0.06 + 0.05 * math.sin(w + 1.0)),
                                           wave(t, T, 5.0, 0.4))]
            yaw = [3 * math.sin(w + 0.3 + 0.5 * i) for i in range(NSEG)]
        arms.append((pitch, yaw))
    return arms


def standing(t):
    T = 3.0; w = 2 * math.pi * t / T
    return dict(bob=0.015 * math.sin(w), body_pitch=1.5 * math.sin(w + 0.6), body_roll=1.2 * math.sin(w + 2.0),
                head_pitch=1.0 * math.sin(w + 1.4), head_yaw=3.0 * math.sin(w * 0.5 * 2 + 0.3),
                arms=idle_arms(t, T), foam_spin=4 * math.sin(w), foam_scale=1.0 + 0.03 * math.sin(2 * w))


def swim(T, sweep, h_scale, amp, lean, pulse):
    """Swimming on the surface: every tentacle's azimuth compressed toward the rear by `sweep` (0..1), arches
    lowered to h_scale, a pulse per cycle (the arms draw in, then sweep back), a wave travelling to the tips."""
    def fn(t):
        w = 2 * math.pi * t / T
        p = 0.5 - 0.5 * math.cos(w)                     # 0 -> 1 -> 0: the stroke
        arms = []
        for k, A in enumerate(ARMS):
            th = A['theta'] % 360
            if k == 0:
                pitch = [x - 14 + y for x, y in zip(SUNK, wave(t, T, 4.0, 0.0))]
                arms.append((pitch, [0.0] * NSEG)); continue
            target = 180 + (th - 180) * (1 - sweep * (0.85 + 0.3 * p))
            yaw0 = target - th
            yaws = [yaw0 * (0.55 + 0.45 * min(1.0, i / 3)) + y for i, y in
                    enumerate(wave(t, T, 6.0, PH[k] * 0.3 + 0.0, lag=0.7))]
            h = H[k] * h_scale * (0.75 + 0.5 * p)
            pitch = [x + y for x, y in zip(arch_profile(h, CURL[k] + 0.3 * math.sin(w + PH[k]) - 0.2),
                                           wave(t, T, amp, PH[k] * 0.2, lag=0.9))]
            arms.append((pitch, yaws))
        return dict(bob=0.02 * math.sin(w + 0.5) - 0.01, body_pitch=lean + pulse * math.sin(w),
                    head_pitch=1.5 * math.sin(w + 1.0), arms=arms, foam_spin=6 * math.sin(w),
                    foam_scale=1.0 + 0.05 * math.sin(2 * w))
    return fn


ATTACK = [(0.00, dict(rear=0.0, lash=0.0, lunge=0.0)),
          (0.30, dict(rear=0.8, lash=0.0, lunge=-0.3)),
          (0.42, dict(rear=1.0, lash=0.0, lunge=-0.4)),
          (0.567, dict(rear=0.0, lash=1.0, lunge=1.0)),
          (0.70, dict(rear=0.0, lash=0.9, lunge=0.8)),
          (0.90, dict(rear=0.0, lash=0.35, lunge=0.3)),
          (1.20, dict(rear=0.0, lash=0.0, lunge=0.0))]


def keyed(keys, t):
    ts = [k[0] for k in keys]
    if t <= ts[0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            u = ss((t - t0) / (t1 - t0))
            return {k: a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * u for k in set(a) | set(b)}
    return keys[-1][1]


REAR = [-18, -6, 40, 75, 95, 105, 70, 10]              # reared up tall, the tip curled back over the head
LASH = [-10, -14, -20, -22, -26, -30, -34, -40]         # thrown forward and down, nearly straight
FRONT = {0: 0.0, 1: -42.0, 7: 42.0}                    # yaw that turns each striking tentacle to the front


def attack(t):
    k_ = keyed(ATTACK, t)
    rear, lash, lunge = k_['rear'], k_['lash'], k_['lunge']
    base = idle_arms(t, 3.0)
    arms = []
    for k, (pitch, yaw) in enumerate(base):
        if k in FRONT:
            calm = max(0.0, 1 - rear - lash)
            pitch = [calm * p + rear * r + lash * l for p, r, l in zip(pitch, REAR, LASH)]
            fy = FRONT[k] * (0.25 * rear + lash)
            yaw = [calm * y + fy * (0.6 + 0.4 * i / (NSEG - 1)) for i, y in enumerate(yaw)]
        else:
            # the others brace: lower, splayed a little
            pitch = [p - 8 * (rear + lash) * (i / (NSEG - 1)) for i, p in enumerate(pitch)]
        arms.append((pitch, yaw))
    return dict(bob=0.03 * rear - 0.02 * lash, body_pitch=-6 * rear + 10 * lunge, body_y=-0.06 * lunge,
                head_pitch=-4 * rear + 6 * lunge, arms=arms, foam_spin=4 * math.sin(2 * math.pi * t / 3.0),
                foam_scale=1.0 + 0.12 * bump(t, 0.45, 0.9))


HIT = [(0.00, dict(j=0.0)), (0.10, dict(j=1.0)), (0.24, dict(j=0.6)), (0.50, dict(j=0.0))]


def hit(t):
    j = keyed(HIT, t)['j']
    base = idle_arms(t, 3.0)
    arms = [([p + j * (8 + 10 * i / (NSEG - 1)) - (j * 25 if i >= NSEG - 2 else 0) for i, p in enumerate(pitch)],
             yaw) for pitch, yaw in base]
    return dict(bob=-0.05 * j, body_pitch=-12 * j, body_y=0.04 * j, body_roll=4 * j, head_pitch=-6 * j, arms=arms,
                foam_scale=1.0 + 0.1 * j)


def death(t):
    flail = bump(t, 0.0, 0.9)
    limp = ss((t - 0.5) / 0.9)
    sink = 1.15 * ss((t - 0.35) / 1.05)
    base = idle_arms(t, 0.8, amp=14.0, yaw_amp=10.0, h_scale=1.0 + 0.25 * flail)
    arms = []
    for k, (pitch, yaw) in enumerate(base):
        pitch = mix(pitch, [p - 8 for p in SUNK], limp)
        yaw = [y * (1 - limp) for y in yaw]
        arms.append((pitch, yaw))
    return dict(sink=sink, body_pitch=-14 * flail + 10 * limp, body_roll=8 * math.sin(2 * math.pi * t / 0.7) * flail,
                head_pitch=-8 * flail, arms=arms, foam_spin=30 * t,
                foam_scale=max(0.001, 1.0 - ss((t - 0.6) / 0.7)) + 0.2 * bump(t, 0.2, 0.7))


FID = [(0.00, dict(u=0.0, c=0.0)), (0.40, dict(u=1.0, c=0.0)), (0.80, dict(u=1.0, c=1.0)), (1.10, dict(u=1.0, c=-0.6)),
       (1.40, dict(u=1.0, c=1.0)), (1.75, dict(u=1.0, c=-0.4)), (2.40, dict(u=0.0, c=0.0))]
FID_ARM = 2                                            # the creature's left side tentacle (+X)
TALL = [-20, -6, 45, 80, 92, 80, 40, -20]


def fidget(t):
    k_ = keyed(FID, t)
    u, c = k_['u'], k_['c']
    arms = idle_arms(t, 2.4)
    pitch, yaw = arms[FID_ARM]
    tall = [x + (0 if i < 5 else c * (35 if i == 5 else 55)) for i, x in enumerate(TALL)]
    arms[FID_ARM] = (mix(pitch, tall, u), [y * (1 - u) - 10 * u for y in yaw])
    st = standing(t)
    st['arms'] = arms
    st['head_yaw'] = 12 * u
    return st


# ---- keying ----------------------------------------------------------------------------------------------------------------
INFO = {}


def key_action(name, n, fn, loop=False, impact_track=False):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    rig.animation_data.action = None
    poses, head_low, top, foam, tipfront = [], [], [], [], []
    for f in range(n + 1):
        t = ((f % n) / FPS) if loop else f / FPS
        apply(build(fn(t)))
        co = mesh_co()
        body = co[~FOAMV]
        head_low.append(float(co[HEADV, 2].min())); top.append(float(body[:, 2].max()))
        foam.append(float(np.abs(co[FOAMV, :2]).max()) if FOAMV.any() else 0.0)
        tipfront.append(min(float(co[TIPV[k], 1].min()) for k in (0, 1, 7)))
        poses.append({b.name: b.matrix_basis.copy() for b in pbn})
    if loop:
        poses[-1] = poses[0]
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for f, pose in enumerate(poses):
        for b in pbn:
            loc, q, sc = pose[b.name].decompose()
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc; b.scale = sc
            b.keyframe_insert('rotation_quaternion', frame=f)
            b.keyframe_insert('location', frame=f)
            b.keyframe_insert('scale', frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    rig.animation_data.action = None
    INFO[name] = {'seconds': round(n / FPS, 4), 'frames': n,
                  'head_lowest_m': [round(min(head_low), 3), round(max(head_low), 3)],
                  'top_m': [round(min(top), 3), round(max(top), 3)], 'foam_radius_m': [round(min(foam), 3), round(max(foam), 3)]}
    if impact_track:
        f_imp = int(np.argmin(tipfront)); INFO[name]['impact_frame'] = f_imp; INFO[name]['impact_s'] = round(f_imp / FPS, 3)
        INFO[name]['front_tip_y_m'] = round(min(tipfront), 3)
    print('CLIP', name, INFO[name], flush=True)


def main():
    clips = {
        'Standing': (90, standing, True, False),
        'Walking': (48, swim(1.6, 0.45, 0.65, 8.0, 5.0, 2.0), True, False),
        'Running': (30, swim(1.0, 0.62, 0.45, 10.0, 8.0, 3.0), True, False),
        'Attack': (36, attack, False, True),
        'Hit': (15, hit, False, False),
        'Fidget': (72, fidget, False, False),
        'Death': (48, death, False, False),
        'Dead': (30, lambda t: death(1.6), False, False),
    }
    for name, (n, fn, loop, imp) in clips.items():
        if ONLY and name not in ONLY:
            continue
        key_action(name, n, fn, loop=loop, impact_track=imp)
    info_path = os.path.join(WORK, 'anim_info.json')
    old = json.load(open(info_path))['clips'] if (ONLY and os.path.exists(info_path)) else {}
    old.update(INFO)
    json.dump({'clips': old}, open(info_path, 'w'), indent=1)
    for b in pbn:
        b.matrix_basis = Matrix.Identity(4)
    rig.animation_data.action = bpy.data.actions['Standing'] if 'Standing' in bpy.data.actions else None
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, OUT))
    print('SAVED', OUT)


main()
