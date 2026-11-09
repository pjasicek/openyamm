"""Procedural clips for the Glassback (24 fps): a heavy six-legged grazer. Args: -- <in.blend> <out.blend>

Each clip is a function of time returning a pose; the legs go by two-bone IK (Upper + Lower) on footholds, the pole
taken from each leg's own rest bend (knees bow outward, front and middle elbows back, hind knees forward), the foot
keeps its rest orientation plus a toe pitch in swing.
  Standing  3.0 s loop   breathing, slow head sway, tail drift
  Walking   0.5 s loop   alternating tripod (FL MR HL / FR ML HR), duty 0.5, stride 0.875 m (1.75 m/s), low heavy steps
  Running   0.4167 s     lumbering charge: same tripod, duty 0.4, stride 1.458 m (3.5 m/s), body low, head down
  Attack    1.8 s        rears up on the hind legs, holds, slams down with beak and front feet (impact 1.083 s)
  Bite      1.2 s        the earlier lunge: draws back, crushes down with the beak (impact 0.583 s)
  Hit       0.6 s        flinch back and aside, recover
  Death     2.0 s        the legs buckle, the belly drops onto the floor, the head sinks to one side
  Dead      held         the last Death pose
  Fidget    2.5 s        lowers the head and crops at the ground twice (grazing), looks up
Floor rules every frame: the root lifts if the body, head or upper legs sink; the head lifts out of the floor; the tail
segments aim up where their ends dip; in the death, legs swing up until clear. A report per clip goes to
work/anim_report.json (IK residuals, lowest points)."""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import posing as P

src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=C.path(src))
rig = bpy.data.objects[C.RIG]; mesh = bpy.data.objects[C.MESH]
FPS = 24
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
LEGS = ('FL', 'FR', 'ML', 'MR', 'HL', 'HR')
SIDE = {'L': 1.0, 'R': -1.0}
CENTRE = Vector((0, -0.15, 0.75))
HIND_PIVOT = Vector((0, 0.30, 0.72))           # between the hind hips: the rear-up pivot
P.reset(rig)
REST = {b.name: (rig.matrix_world @ b.matrix).copy() for b in rig.pose.bones}
ANKLE = {l: REST[f'Foot_{l}'].translation.copy() for l in LEGS}
HIP = {l: REST[f'Upper_{l}'].translation.copy() for l in LEGS}
KNEE = {l: REST[f'Lower_{l}'].translation.copy() for l in LEGS}
POLE = {l: KNEE[l] + (KNEE[l] - (HIP[l] + ANKLE[l]) / 2).normalized() * 0.8 + Vector((0, 0, 0.2)) for l in LEGS}
REACH = {l: (rig.data.bones[f'Upper_{l}'].length + rig.data.bones[f'Lower_{l}'].length) for l in LEGS}
residual = []
CURRENT = [0]


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def rot(name, axis, deg, pivot=None):
    if abs(deg) > 1e-6:
        P.rotate_world(rig, name, axis, deg, pivot)


def set_world_rot(name, q):
    b = rig.pose.bones[name]
    b.matrix = Matrix.LocRotScale(b.head.copy(), q, Vector((1, 1, 1))); bpy.context.view_layer.update()


def place_leg(leg, target, pitch=0.0, fold=0.0):
    """fold 0..1 turns the knee pole outward and up (collapsing legs: knees up and out)."""
    pole = POLE[leg] + (target - ANKLE[leg]) + Vector((SIDE[leg[1]] * 0.8, 0, 0.9)) * fold
    P.two_bone_ik(rig, f'Upper_{leg}', f'Lower_{leg}', target, pole)
    end = rig.matrix_world @ rig.pose.bones[f'Lower_{leg}'].tail
    residual.append(((end - target).length, leg, CURRENT[0]))
    q = Quaternion(X, math.radians(pitch)) @ REST[f'Foot_{leg}'].to_quaternion()
    set_world_rot(f'Foot_{leg}', q)


def free_leg(leg, splay, upper, lower, foot=0.0):
    """FK for lying poses: splay outward about the body axis, swing the upper leg about X, fold the lower."""
    s = SIDE[leg[1]]
    rot(f'Upper_{leg}', Y, -splay * s); rot(f'Upper_{leg}', X, upper); rot(f'Lower_{leg}', X, lower)
    rot(f'Foot_{leg}', X, foot)


def tail_wave(yaw, pitch, phase, lift=0.0):
    for i in (1, 2, 3):
        k = i / 3.0
        rot(f'Tail{i}', Z, yaw * k * math.sin(2 * math.pi * (phase - 0.12 * i)))
        rot(f'Tail{i}', X, -(lift if i == 1 else lift * 0.3) + pitch * math.sin(2 * math.pi * (phase - 0.12 * i)))


def body(d=Vector(), pitch=0.0, roll=0.0, yaw=0.0, spine_pitch=0.0, spine_yaw=0.0, head_pitch=0.0, head_yaw=0.0,
         head_roll=0.0, pivot=0.0):
    """d moves the whole body; pitch (+ = nose down), roll (+ = toward the creature's right) and yaw about CENTRE,
    or (pivot 1) about the hind hips, so the body can rear up on its hind legs."""
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(d) @ root.matrix; bpy.context.view_layer.update()
    c = CENTRE.lerp(HIND_PIVOT, pivot) + d
    rot('Spine1', Z, yaw, c); rot('Spine1', Y, roll, c); rot('Spine1', X, pitch, c)
    for n in ('Spine2', 'Spine3'):
        rot(n, X, spine_pitch * 0.5); rot(n, Z, spine_yaw * 0.5)
    rot('Neck1', X, head_pitch * 0.45); rot('Head', X, head_pitch * 0.55)
    rot('Neck1', Z, head_yaw * 0.5); rot('Head', Z, head_yaw * 0.5)
    rot('Head', Y, head_roll)


# ---------------------------------------------------------------- floor rules
_names = [g.name for g in mesh.vertex_groups]
_dom = np.array([_names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in mesh.data.vertices])
CORE = np.array([n.startswith(('Spine', 'Neck', 'Upper')) for n in _dom])
TRUNK = np.array([n.startswith(('Spine', 'Neck')) for n in _dom])
HEADV = np.array([n in ('Head', 'Neck1') for n in _dom])
LIMB = {l: np.array([n.endswith('_' + l) for n in _dom]) for l in LEGS}
FLOOR = 0.004


def mesh_co():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mesh.evaluated_get(dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)


def lift_root(dz):
    root = rig.pose.bones['Spine1']
    root.matrix = Matrix.Translation(Vector((0, 0, dz))) @ root.matrix; bpy.context.view_layer.update()


def clamp_tail():
    for i in (1, 2, 3):
        b = rig.pose.bones[f'Tail{i}']
        t = rig.matrix_world @ b.tail
        r = 0.06 - 0.015 * i
        if t.z < r:
            h = rig.matrix_world @ b.head
            dv = t - h; L = dv.length
            flat = Vector((dv.x, dv.y, 0)).normalized()
            dz = r - h.z
            if abs(dz) < L:
                P.aim_bone(rig, b.name, h + flat * math.sqrt(L * L - dz * dz) + Vector((0, 0, dz)))


def clamp_head():
    for _ in range(20):
        low = mesh_co()[HEADV, 2].min()
        if low > 0.012:
            return
        rot('Neck1', X, -2.0); rot('Head', X, -1.0)


def clamp_limbs():
    for leg in LEGS:
        for _ in range(15):
            low = mesh_co()[LIMB[leg], 2].min()
            if low > -0.004:
                break
            P.rotate_world(rig, f'Upper_{leg}', Y, 5.0 * SIDE[leg[1]])


def floor_fit(lift=True, head=True, trunk_only=False):
    if lift:
        low = mesh_co()[TRUNK if trunk_only else CORE, 2].min()
        if low < -FLOOR:
            lift_root(-low)
    if head:
        clamp_head()
    clamp_tail()


# ---------------------------------------------------------------- clips
_plans = {}


def foothold(leg, drop, half, limit=0.975):
    """Stance centre for a sweep of +-half with the body lowered by drop: the rest ankle moved toward the hip's floor
    projection until both sweep ends stay within `limit` of the leg's reach (the rest legs are nearly straight)."""
    key = (leg, round(drop, 4), round(half, 4))
    if key not in _plans:
        hip = HIP[leg] - Vector((0, 0, drop))
        a = ANKLE[leg]
        # fore-aft first (the step centres under the hip along the body), sideways only if that is not enough
        ok = lambda c: max((hip - (c + Vector((0, e, 0)))).length for e in (-half, half)) <= limit * REACH[leg]
        toward = Vector((0, hip.y - a.y, 0))
        lam = 0.0
        while lam < 1.0 and not ok(a + toward * lam):
            lam += 0.01
        if not ok(a + toward * lam):
            a = a + toward; toward = Vector((hip.x - a.x, 0, 0)); lam = 0.0
            while lam < 1.0 and not ok(a + toward * lam):
                lam += 0.01
        _plans[key] = a + toward * lam
        moved = a + toward * lam - ANKLE[leg]
        print('FOOTHOLD', leg, 'drop', round(drop, 3), 'half', round(half, 3), 'moved y', round(moved.y, 3), 'x', round(moved.x, 3))
    return _plans[key]


GROUP = {'FL': 0.0, 'MR': 0.0, 'HL': 0.0, 'FR': 0.5, 'ML': 0.5, 'HR': 0.5}
LEAD = {'H': 0.0, 'M': 0.035, 'F': 0.07}              # a small wave from back to front inside each tripod


def gait(t, T, stride, duty, lift, drop, bob, roll, pitch=0.0, head=0.0, sway=2.0):
    p = (t / T) % 1.0
    P.reset(rig)
    w = math.cos(4 * math.pi * p)                         # twice per cycle: lowest as each tripod takes the weight
    body(d=Vector((0, 0, -drop - bob * 0.5 * (1 + w))), pitch=pitch, roll=roll * math.sin(2 * math.pi * p),
         yaw=sway * math.sin(2 * math.pi * p), spine_yaw=-sway * math.sin(2 * math.pi * p),
         head_pitch=head - 2.5 * w, head_yaw=-2.0 * math.sin(2 * math.pi * p))
    tail_wave(9, 3, p, lift=4)
    s = stride * duty
    for leg in LEGS:
        q = (p + GROUP[leg] + LEAD[leg[0]]) % 1.0
        if q < duty:
            dy = -s / 2 + s * (q / duty); dz = 0.0; toe = 0.0
        else:
            u = (q - duty) / (1 - duty)
            dy = s / 2 - s * ss(u); dz = lift * math.sin(math.pi * u) ** 0.8; toe = 22 * math.sin(math.pi * u)
        place_leg(leg, foothold(leg, drop + bob, s / 2) + Vector((0, dy, dz)), toe)


def plant_all(offsets=None, fold=0.0, pitch=0.0):
    for leg in LEGS:
        f = fold.get(leg, 0.0) if isinstance(fold, dict) else fold
        place_leg(leg, ANKLE[leg] + (offsets or {}).get(leg, Vector()), pitch, f)


def standing(t):
    P.reset(rig)
    b = math.sin(2 * math.pi * t / 3.0)
    body(d=Vector((0, 0, -0.008 + 0.008 * b)), spine_pitch=-0.8 * b, head_pitch=2 * b,
         head_yaw=6 * math.sin(2 * math.pi * t / 3.0 + 0.7))
    tail_wave(6, 2, t / 3.0, lift=4)
    plant_all()


def keyed(keys, t):
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            x = min(1.0, max(0.0, (t - t0) / max(t1 - t0, 1e-6)))
            u = x * x if b.get('_ease') == 'in' else ss(x)          # 'in': accelerate into the key (a slam)
            out = {}
            for k in (set(a) | set(b)) - {'_ease'}:
                va, vb = a.get(k, 0.0), b.get(k, 0.0)
                if isinstance(va, Vector) or isinstance(vb, Vector):
                    va = va if isinstance(va, Vector) else Vector(); vb = vb if isinstance(vb, Vector) else Vector()
                    out[k] = va.lerp(vb, u)
                else:
                    out[k] = va + (vb - va) * u
            return out
    return dict(keys[-1][1])


def generic(pr):
    P.reset(rig)
    body(d=pr.get('d', Vector()), pitch=pr.get('pitch', 0.0), roll=pr.get('roll', 0.0), yaw=pr.get('yaw', 0.0),
         spine_pitch=pr.get('spine', 0.0), spine_yaw=pr.get('spine_yaw', 0.0), head_pitch=pr.get('head', 0.0),
         head_yaw=pr.get('head_yaw', 0.0), head_roll=pr.get('head_roll', 0.0), pivot=pr.get('pivot', 0.0))
    tail_wave(pr.get('tail_sway', 4.0), 0, pr.get('tail_phase', 0.0), lift=pr.get('tail_lift', 4.0))
    offs = {leg: pr.get('o_' + leg, Vector()) + pr.get('o_' + leg[0], Vector())
            + Vector((SIDE[leg[1]] * pr.get('spread', 0.0), 0, 0)) for leg in LEGS}
    folds = {leg: pr.get('fold', 0.0) + pr.get('fold_' + leg[0], 0.0) for leg in LEGS}
    plant_all(offs, folds, pr.get('foot', 0.0))


V = Vector
ATTACK = [
    (0.00, {}),
    (0.38, {'d': V((0, 0.025, -0.035)), 'pitch': -3, 'head': -30, 'spine': -5, 'tail_lift': 10}),
    (0.50, {'d': V((0, 0.03, -0.04)), 'pitch': -3.5, 'head': -34, 'spine': -6, 'tail_lift': 12}),
    (0.583, {'d': V((0, -0.065, -0.06)), 'pitch': 8, 'head': 32, 'spine': 5, 'tail_lift': -2}),
    (0.70, {'d': V((0, -0.055, -0.06)), 'pitch': 7, 'head': 26, 'head_roll': 6, 'spine': 4}),
    (1.20, {}),
]
# User review 2026-10-22: rear up on the hind legs, hold, slam down with beak and front feet. The hind feet stay planted
# (IK on their rest footholds); the front feet rise folded in front of the chest, the middle pair lifts a little; both
# land back on their own rest footholds at the impact, so no foot slides. Impact 1.083 s (frame 26).
REAR = [
    (0.00, {}),
    (0.28, {'d': V((0, 0.02, -0.045)), 'pitch': 3, 'head': 14, 'spine': 2, 'tail_lift': 2}),
    (0.62, {'pivot': 1, 'pitch': -30, 'spine': -7, 'head': 4, 'tail_lift': -6, 'fold_F': 0.8,
            'o_F': V((0, 0.26, 0.52)), 'o_M': V((0, 0.06, 0.20)), 'fold_M': 0.3}),
    (0.88, {'pivot': 1, 'pitch': -32, 'spine': -8, 'head': -6, 'tail_lift': -6, 'head_roll': 3, 'fold_F': 0.9,
            'o_F': V((0, 0.28, 0.56)), 'o_M': V((0, 0.06, 0.22)), 'fold_M': 0.3}),
    (1.083, {'_ease': 'in', 'pivot': 1, 'pitch': 5, 'd': V((0, -0.03, -0.05)), 'spine': 4, 'head': 34, 'tail_lift': 8}),
    (1.25, {'pivot': 1, 'pitch': 2.5, 'd': V((0, -0.025, -0.02)), 'spine': 2, 'head': 22, 'tail_lift': 5}),
    (1.80, {}),
]
HIT = [
    (0.00, {}),
    (0.12, {'d': V((0.03, 0.04, -0.01)), 'roll': -4, 'pitch': -1.5, 'head': -14, 'head_yaw': 12, 'tail_lift': 12,
            'tail_sway': 10, 'tail_phase': 0.25}),
    (0.30, {'d': V((0.015, 0.02, -0.01)), 'roll': -2, 'pitch': -0.5, 'head': -6, 'head_yaw': 6, 'tail_lift': 8}),
    (0.60, {}),
]
DEATH = [
    (0.00, {}),
    (0.35, {'d': V((0, 0.04, -0.02)), 'pitch': -1.5, 'roll': 2, 'head': -24, 'head_yaw': 8, 'tail_lift': 12}),
    (0.90, {'d': V((0, 0.0, -0.30)), 'pitch': 3, 'roll': 6, 'head': 12, 'head_yaw': -10, 'spread': 0.16,
            'fold': 0.7, 'tail_lift': -2, 'o_F': V((0, -0.06, 0)), 'o_H': V((0, 0.06, 0))}),
    (1.30, {'d': V((0, 0.0, -0.45)), 'pitch': 2, 'roll': 9, 'head': 26, 'head_yaw': -24, 'head_roll': -12,
            'spread': 0.26, 'fold': 1.0, 'foot': -25, 'tail_lift': -10, 'tail_sway': 8, 'tail_phase': 0.2,
            'o_F': V((0, -0.10, 0)), 'o_H': V((0, 0.04, 0))}),
    (2.00, {'d': V((0, 0.0, -0.46)), 'pitch': 2, 'roll': 10, 'head': 30, 'head_yaw': -26, 'head_roll': -14,
            'spread': 0.27, 'fold': 1.0, 'foot': -30, 'tail_lift': -12, 'tail_sway': 8, 'tail_phase': 0.2,
            'o_F': V((0, -0.10, 0)), 'o_H': V((0, 0.04, 0))}),
]


def fidget(t):
    u = t / 2.5
    crop = 0.0
    for c0 in (0.32, 0.56):                                 # two bites at the ground
        crop += math.exp(-((u - c0) / 0.05) ** 2)
    down = ss(u / 0.22) * (1 - ss((u - 0.78) / 0.2))
    pr = {'d': V((0, -0.02 * down, -0.03 * down)), 'pitch': 5 * down, 'head': 52 * down - 10 * crop,
          'head_yaw': 10 * math.sin(2 * math.pi * u) * down + 12 * ss((u - 0.8) / 0.2) * (1 - ss((u - 0.9) / 0.1)),
          'head_roll': 4 * crop, 'tail_sway': 6, 'tail_phase': u}
    generic(pr)


WALK_STRIDE = 0.875                # authored 1.75 m/s: game rates A 1.43, B 1.14, C 0.99 at speed 250
RUN_STRIDE = 1.4583                # authored 3.5 m/s for the 500 units/s chase
CLIPS = {
    'Standing': (3.0, True, standing),
    'Walking': (12 / FPS, True, lambda t: gait(t, 12 / FPS, WALK_STRIDE, 0.5, 0.10, 0.015, 0.02, 2.0)),
    'Running': (10 / FPS, True, lambda t: gait(t, 10 / FPS, RUN_STRIDE, 0.4, 0.15, 0.035, 0.03, 3.0, pitch=3,
                                               head=10, sway=3)),
    'Attack': (1.8, False, lambda t: generic(keyed(REAR, t))),
    'Bite': (1.2, False, lambda t: generic(keyed(ATTACK, t))),           # the earlier lunge, kept as a secondary clip
    'Hit': (0.6, False, lambda t: generic(keyed(HIT, t))),
    'Death': (2.0, False, lambda t: generic(keyed(DEATH, t))),
    'Fidget': (2.5, True, fidget),
}


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    n = int(round(seconds * FPS))
    rig.animation_data.action = None
    poses = []
    residual.clear()
    lows = []
    for f in range(n + 1):
        t = (f % n) / FPS if loop else f / FPS
        CURRENT[0] = f
        fn(t)
        floor_fit(lift=name in ('Attack', 'Hit', 'Death', 'Dead', 'Fidget', 'Standing'), head=True,
                  trunk_only=name in ('Death', 'Dead'))
        if name in ('Death', 'Dead') and (name == 'Dead' or t >= 1.25):
            lift_root(-mesh_co()[:, 2].min())          # the corpse rests on the floor
        mc = mesh_co()
        lows.append(float(mc[:, 2].min()))
        if lows[-1] <= min(lows):
            worst = (f, _dom[int(np.argmin(mc[:, 2]))])
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones})
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
    rig.animation_data.action = None
    print('LOWEST', name, 'frame', worst[0], 'bone', worst[1], round(min(lows), 4))
    return {'seconds': seconds, 'frames': n, 'ik_residual_max_m': round(max(residual)[0] if residual else 0, 4), 'ik_residual_worst': list(max(residual)[1:]) if residual else [],
            'lowest_m': round(min(lows), 4), 'lowest_per_frame': [round(x, 4) for x in lows]}


for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
report = {}
for name, (sec, loop, fn) in CLIPS.items():
    report[name] = key_action(name, sec, loop, fn)
    print('CLIP', name, sec, 'ik_res', report[name]['ik_residual_max_m'], report[name]['ik_residual_worst'], 'low', report[name]['lowest_m'], flush=True)
report['Dead'] = key_action('Dead', 1.0, False, lambda t: generic(keyed(DEATH, 2.0)))
print('CLIP Dead low', report['Dead']['lowest_m'])
report['bindings'] = {'walk_stride_m': WALK_STRIDE, 'run_stride_m': RUN_STRIDE, 'attack_impact_s': 1.083, 'bite_impact_s': 0.583}
json.dump(report, open(C.path('work/anim_report.json'), 'w'), indent=1)
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=C.path(dst))
print('SAVED', dst)
