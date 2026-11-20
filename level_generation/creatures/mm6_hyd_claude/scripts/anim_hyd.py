"""Procedural hydra clips (24 fps) on work/rig_v1.blend -> work/anim_v1.blend.

Every frame defines the joint positions of each chain and fits the bones to them (minimal rotation from each bone's
rest direction to its posed direction, translation = posed head; bones are disconnected, so nothing stretches):
  - body: Body_Root fixed; each tail segment's rest direction turned about Z by an accumulated heading change (a wave
    travelling to the tip, amplitude growing outward), staying on the ground,
  - necks: each segment's rest direction pitched about X (+ forward and down) and yawed about Z by cumulative
    profiles, per-neck phase offsets so the five heads never move in unison; Head<k> gets extra pitch/yaw,
  - floor rule: every neck joint stays at least its radius above the ground, or its rest height where the outer
    necks already run along the ground (directions flatten instead).
Native timings (manifest): stand/walk/attack/hit/fidget 0.75 s, death 0.625 s.
  Standing 3.0 s loop  necks sway in different phases, heads look around, tail drifts
  Walk     0.75 s loop tail S wave; every neck sways with a wave travelling up it and bobs in turn
  Attack   0.75 s      the middle three necks arch far back, then lash forward in ~0.07 s (bend travels base to head)
  Hit      0.75 s      all necks recoil back, heads shake
  Death    0.625 s     necks topple forward onto the ground in turn; Dead = last pose held 1 s
  Fidget   0.75 s      all necks sway, bob and turn their heads on their own beats; the outer heads look outward
Prints per clip the lowest neck joint above its floor and the smallest gap between the necks' upper halves."""
import bpy, json, math, os
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 24
D = json.load(open(os.environ.get('HYD_RIG_JSON', os.path.join(HERE, 'work', 'rig.json'))))
CHAINS = [{'names': c['names'], 'J': np.array(c['joints']), 'R': np.array(c['radius']), 'parent': c['parent']}
          for c in D['chains']]
BODY, NECKS = CHAINS[0], CHAINS[1:]
rig = bpy.data.objects['Hydra_Rig']
REST_M = {pb.name: pb.bone.matrix_local.copy() for pb in rig.pose.bones}
for c in CHAINS:
    c['L'] = np.linalg.norm(np.diff(c['J'], axis=0), axis=1)
    c['dir'] = [Vector(c['J'][i + 1] - c['J'][i]).normalized() for i in range(len(c['names']))]
    c['F'] = np.minimum(c['R'], c['J'][:, 2])     # floor per joint: its radius, or lower where the rest pose lies lower
PHASE = [0.0, 1.9, 0.7, 3.3, 5.1]
HEAD_SLACK = -0.015    # m: heads stay this much further apart than at rest (fins and horns swing with head turns)


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def lift(k):
    """Per segment of neck k: 0 where it lies on the ground (the outer necks' run into the root), 1 once raised."""
    J = NECKS[k]['J']
    return np.clip(((J[:-1, 2] + J[1:, 2]) / 2 - 0.12) / 0.25, 0, 1)


def profile(k, total, power=1.0):
    """Cumulative bend over neck k's segments (upper segments carry more, segments on the ground none); the head
    takes the full value."""
    n = len(NECKS[k]['names']); m = n - 1; w = lift(k)
    return np.array([total * ((i + 1) / m) ** power * w[i] for i in range(m)] + [total])


def whip(k, fn, lag, power=1.0):
    """Like profile, but segment i follows fn(t - lag * i / m): a bend that travels from the neck base to the head
    (a lash). fn(dt) -> total; returns a function of t."""
    n = len(NECKS[k]['names']); m = n - 1; w = lift(k)
    def at(t):
        return np.array([fn(t - lag * i / m) * ((i + 1) / m) ** power * w[i] for i in range(m)] + [fn(t - lag)])
    return at


def body_pose(t, amp=0.0, speed=1.0, curl=0.0):
    J = BODY['J'].copy(); n = len(BODY['names'])
    heading = 0.0
    for i in range(n):
        u = (i + 1) / n
        heading += (amp * math.sin(2 * math.pi * (speed * t) - 4.0 * u) * u + curl * u) * BODY['L'][i] * 4.0
        d = Matrix.Rotation(heading, 3, 'Z') @ BODY['dir'][i]
        J[i + 1] = J[i] + BODY['L'][i] * np.array(d)
        J[i + 1][2] = BODY['J'][i + 1][2]                       # stays on the ground
    return J


def neck_pose(k, base, pitch, yaw, head_pitch=0.0, head_yaw=0.0):
    c = NECKS[k]; n = len(c['names']); J = c['J'].copy(); J[0] = base
    for i in range(n):
        hp, hy = (head_pitch, head_yaw) if i == n - 1 else (0.0, 0.0)
        # +pitch about X turns an upward segment toward -Y (forward) and a forward one down
        d = Matrix.Rotation(yaw[i] + hy, 3, 'Z') @ Matrix.Rotation(pitch[i] + hp, 3, 'X') @ c['dir'][i]
        nxt = J[i] + c['L'][i] * np.array(d)
        floor = c['F'][i + 1]
        if nxt[2] < floor:
            h = np.array([d[0], d[1], 0.0]); hn = np.linalg.norm(h)
            h = h / hn if hn > 1e-6 else np.array([0, -1.0, 0])
            dz = floor - J[i][2]
            nxt = J[i] + h * math.sqrt(max(c['L'][i] ** 2 - dz * dz, 1e-6)) + np.array([0, 0, dz])
        J[i + 1] = nxt
    return J


def apply(posed):
    """posed: list of joint arrays per chain (same order as CHAINS)."""
    world = {}
    for c, J in zip(CHAINS, posed):
        for i, nm in enumerate(c['names']):
            q = c['dir'][i].rotation_difference(Vector(J[i + 1] - J[i]).normalized())
            m = (q.to_matrix() @ REST_M[nm].to_3x3()).to_4x4(); m.translation = Vector(J[i]); world[nm] = m
    for pb in rig.pose.bones:
        rest = REST_M[pb.name]
        if pb.parent is None:
            pb.matrix_basis = rest.inverted() @ world[pb.name]
        else:
            prest = REST_M[pb.parent.name]
            pb.matrix_basis = (prest.inverted() @ rest).inverted() @ world[pb.parent.name].inverted() @ world[pb.name]


def base_of(k, body):
    """A neck's base moves with its parent body joint."""
    c = NECKS[k]; idx = BODY['names'].index(c['parent'])
    return c['J'][0] + (body[idx] - BODY['J'][idx])


def seg_dist(a0, a1, b0, b1):
    """Closest distance between segments a0-a1 and b0-b1 (sampled; the head capsules are short)."""
    ta = np.linspace(0, 1, 7)[:, None]
    A = a0 + ta * (a1 - a0); B = b0 + ta * (b1 - b0)
    return float(np.linalg.norm(A[:, None] - B[None], axis=2).min())


def head_capsule(J):
    """The head of a posed neck: from 1.5 head bones behind the tip (the grafted skulls are longer than the bone) to
    the tip."""
    return J[-2] + 0.5 * (J[-2] - J[-1]), J[-1]


REST_HEAD = {(a, b): seg_dist(*head_capsule(NECKS[a]['J']), *head_capsule(NECKS[b]['J']))
             for a in range(len(NECKS)) for b in range(a + 1, len(NECKS))}


def pose(t, body_args, neck_fn):
    """Posed chains; then no two heads closer than at rest (minus HEAD_SLACK): offending pairs turn apart by a yaw
    on both necks (the left one of the pair further left), iterated. The grafted heads are wide, and sway or strikes
    toward a neighbour pushed fins and spikes into it."""
    body = body_pose(t, **body_args)
    args = [neck_fn(k, len(c['names']), t) for k, c in enumerate(NECKS)]
    extra = np.zeros(len(NECKS))
    for _ in range(12):
        necks = [neck_pose(k, base_of(k, body), p, y + profile(k, extra[k], 1.0), hp, hy)
                 for k, (p, y, hp, hy) in enumerate(args)]
        worst = 0.0
        for (a, b), rest in REST_HEAD.items():
            gap = rest - HEAD_SLACK - seg_dist(*head_capsule(necks[a]), *head_capsule(necks[b]))
            if gap > 0:
                # neck a is left of b (x ascending): a turns left (negative yaw), b right
                extra[a] -= 1.5 * gap; extra[b] += 1.5 * gap; worst = max(worst, gap)
        if worst < 1e-3:
            break
    return [body] + necks


def standing(t):
    def neck(k, n, t):
        ph = 2 * math.pi * t / 3.0 + PHASE[k]
        return (profile(k, 0.06 * math.sin(ph), 1.3), profile(k, 0.10 * math.sin(ph * 0.5 + k), 1.5),
                -0.10 * math.sin(ph + 1.0), 0.25 * math.sin(ph * 0.5 + 2.0 * k))
    return pose(t, dict(amp=0.12, speed=1 / 3.0), neck)


def walk(t):
    # every neck sways side to side with the wave travelling up it, and bobs forward in turn; the tail swims
    def neck(k, n, t):
        ph = 2 * math.pi * t / 0.75 + PHASE[k]
        sway = whip(k, lambda u: 0.22 * math.sin(2 * math.pi * u / 0.75 + PHASE[k]), 0.2, 1.1)(t)
        return profile(k, 0.12 + 0.12 * math.sin(ph), 1.2), sway, -0.12 + 0.08 * math.sin(ph + 1.2), \
            -0.15 * math.sin(ph - 0.8)
    return pose(t, dict(amp=0.6, speed=1 / 0.75), neck)


def lash(t0):
    """Neck pitch total for one strike starting at t0: deep wind-up (arched back), a short hold, a ~0.07 s lash
    forward with a little overshoot, then recovery by the clip end."""
    def at(u):
        u -= t0
        wind = -1.1 * ss(u / 0.26)
        strike = 2.1 * ss((u - 0.30) / 0.07)                    # from -1.1 to +1.0
        settle = -1.0 * ss((u - 0.44) / (0.73 - t0 - 0.44))
        return wind + strike + settle
    return at


def attack(t):
    def neck(k, n, t):
        if k in (1, 2, 3):
            t0 = 0.035 * (k - 1)
            f = lash(t0)
            u = t - t0
            head = -0.6 * ss(u / 0.26) + 1.15 * ss((u - 0.31) / 0.06) - 0.55 * ss((u - 0.45) / (0.72 - t0 - 0.45))
            return whip(k, f, 0.06, 1.3)(t), profile(k, 0.0), head, 0.0
        # the outer necks rear back with the wind-up and jerk forward with the strike, less
        f = lash(0.03)
        return whip(k, lambda u: 0.3 * f(u), 0.06, 1.3)(t), profile(k, 0.0), 0.0, 0.0
    return pose(t, dict(amp=0.12, speed=1 / 0.75), neck)


def hit(t):
    r = ss(t / 0.1) * (1 - ss((t - 0.25) / 0.45))
    def neck(k, n, t):
        return (profile(k, -0.4 * r, 1.2), profile(k, 0.2 * r * (1 if k % 2 else -1), 1.3), -0.3 * r,
                0.35 * math.sin(2 * math.pi * t / 0.25 + k) * r)
    return pose(t, dict(amp=0.25 * r, speed=1 / 0.75), neck)


def death(t):
    def neck(k, n, t):
        f = ss((t - 0.06 * PHASE.index(PHASE[k])) / 0.45)
        side = (k - 2) * 0.25
        return profile(k, 1.5 * f, 0.6), profile(k, side * f, 1.0), 0.5 * f, 0.0
    return pose(t, dict(amp=0.0, curl=0.05 * ss(t / 0.6)), neck)


def fidget(t):
    # all five necks shift: each sways, bobs and turns its head on its own beat; the two outer heads look around,
    # outward (an inward look swung horns and fins into the packed neighbours)
    env = ss(t / 0.12) * (1 - ss((t - 0.55) / 0.2))
    look = ss((t - 0.05) / 0.15) * (1 - ss((t - 0.5) / 0.2))
    def neck(k, n, t):
        ph = 2 * math.pi * t / 0.75 + PHASE[k]
        sway = whip(k, lambda u: 0.18 * env * math.sin(2 * math.pi * u / 0.75 + PHASE[k]), 0.15, 1.2)(t)
        bob = profile(k, env * (0.1 * math.sin(ph + 0.5) - 0.04), 1.2)
        hy = 0.2 * env * math.sin(ph * 1.5 + k)
        if k in (0, 4):
            s = -1 if k == 0 else 1                     # yaw: negative turns toward -x (screen left)
            sway = sway + profile(k, 0.15 * s * look, 1.5); hy = 0.55 * s * look
        return bob, sway, -0.15 * env * math.sin(ph + 2.0), hy
    return pose(t, dict(amp=0.15, speed=1 / 0.75), neck)


def neck_clearance(necks):
    """Smallest gap (cm-scale, minus both radii) between the raised upper halves of different necks, sampled at
    joints and segment midpoints; negative means the surfaces interpenetrate."""
    pts = []
    for c, J in zip(NECKS, necks):
        upper = np.nonzero(np.arange(len(J)) >= len(J) // 2)[0]
        P = np.concatenate([J[upper], (J[upper[:-1]] + J[upper[1:]]) / 2]); R = np.concatenate([c['R'][upper], (c['R'][upper[:-1]] + c['R'][upper[1:]]) / 2])
        pts.append((P, R))
    best = 9.0
    for a in range(len(pts)):
        for b in range(a + 1, len(pts)):
            (Pa, Ra), (Pb, Rb) = pts[a], pts[b]
            d = np.linalg.norm(Pa[:, None] - Pb[None], axis=2) - Ra[:, None] - Rb[None]
            best = min(best, float(d.min()))
    return best


REST_CLEARANCE = neck_clearance([c['J'] for c in NECKS])


def capture():
    return {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones}


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    n = int(round(seconds * FPS)); poses = []; lowest = 9.0; clearance = 9.0
    for f in range(n + 1):
        posed = fn(((f % n) if loop else f) / FPS)
        apply(posed); bpy.context.view_layer.update(); poses.append(capture())
        for c, J in zip(NECKS, posed[1:]):
            lowest = min(lowest, float((J[1:, 2] - c['F'][1:]).min()))
        clearance = min(clearance, neck_clearance(posed[1:]))
    act = bpy.data.actions.new(name); act.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = act
    prev = {}
    for f, pose_ in enumerate(poses):
        for k, (q, l) in pose_.items():
            if k in prev and prev[k].dot(q) < 0:
                q = -q
            prev[k] = q
            pb = rig.pose.bones[k]; pb.rotation_quaternion = q; pb.location = l
            pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
    rig.animation_data.action = None
    print(f'CLIP {name} {seconds}s lowest neck joint above its floor {lowest * 100:.1f} cm; '
          f'neck clearance {clearance * 100:.1f} cm (rest {REST_CLEARANCE * 100:.1f})')


for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'


def main():
    clips = {'Standing': (3.0, True, standing), 'Walk': (0.75, True, walk), 'Attack': (0.75, False, attack),
             'Hit': (0.75, False, hit), 'Death': (0.625, False, death), 'Dead': (1.0, False, lambda t: death(0.625)),
             'Fidget': (0.75, False, fidget)}
    for name, (sec, loop, fn) in clips.items():
        key_action(name, sec, loop, fn)
    rig.animation_data.action = bpy.data.actions['Standing']
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
    print('SAVED')


if __name__ == '__main__':
    main()
