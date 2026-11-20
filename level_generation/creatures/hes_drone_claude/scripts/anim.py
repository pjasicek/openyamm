"""Procedural clips for the drone (24 fps) on work/gear_v1.blend -> work/anim_v1.blend.
Forward -Y, up +Z, left +X. Rigid body bones; the tendons are 3-bone chains with lagging secondary motion.
  Standing  2.0 s loop  hover bob 1.5 cm, slow tilt and drift, tendons sway with a lag, thrust pulse 3 Hz
  Walking   1.0 s loop  flying forward: nose down 8 deg, tendons trail back, thrust pulse 5 Hz, a little stronger
  Running   0.75 s loop nose down 15 deg, tendons trail far back, thrust 8 Hz, strongest
  Attack    0.75 s      aim (nose up a little), the shot at IMPACT: recoil kick back and up, the lens dome punches
                        in, tendons whip; recover
  Hit       0.5 s       knocked back, yaw and roll, damped wobble, tendons flail
  Death     1.5 s       shudder, the thrust cuts out and the lens iris closes (dome scaled down), drops nose first,
                        hits the floor at 0.875 s, a small bounce, comes to rest tilted on the floor, tendons lie on
                        the floor (floor rule per segment); Dead = the last frame held
  Fidget    1.5 s       scan turn: yaws 28 deg left, then right, back; tendons lag the turn
Floor rule for fliers (claude_shared/floor/README.md, as mm6_bh_claude): the lowest visible point over every living
clip meets the floor. The cables are short and trail back above the vent drum's bottom, so that point is the thrust
glow's tip under the vents (counted like every visible mesh by floor_audit) at its longest pulse: the casing and vents,
the lowest solid parts, float clearly above the floor. The hover offset is measured over all living frames and baked
into the Body; the death eases it out so the corpse rests on the floor (casing on the floor, cables lying flat on it,
never below)."""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'gear_v1.blend'))
rig = bpy.data.objects['HDR_Rig']; mesh = bpy.data.objects['HDR']; thrust_obj = bpy.data.objects['HDR_Thrust']
FPS = 24
IMPACT = 7 / FPS
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
P.reset(rig)
pa = np.zeros(len(mesh.data.polygons), int); mesh.data.attributes['part'].data.foreach_get('value', pa)
vpart = np.zeros(len(mesh.data.vertices), int)
for p in mesh.data.polygons:
    for v in p.vertices:
        vpart[v] = pa[p.index]
LIVE = vpart <= 4                    # body, tendons, lens (the gear never hangs lowest)
BODY = (vpart == 0) | (vpart == 4)
TENDONS = [[f'Tendon{k}_{j}' for j in (1, 2, 3)] for k in (1, 2, 3)]
TENDON_R = 0.014
HOVER = 0.0


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def pose(lift=0.0, forward=0.0, side=0.0, pitch=0.0, yaw=0.0, roll=0.0, recoil=0.0, iris=1.0, thrust=(1.0, 1.0),
         trail=0.0, sway=None, hover=None):
    """pitch + = nose down, yaw + = turn to its left, roll + = left side down (degrees); trail + = tendons swing
    back (deg); sway: per tendon list of per-segment (pitch, side) degrees; thrust = (radial, length) scale."""
    P.reset(rig)
    root = rig.pose.bones['Body']
    h = HOVER if hover is None else hover
    root.matrix = Matrix.Translation(Vector((side, -forward, lift + h))) @ root.matrix
    bpy.context.view_layer.update()
    if yaw:
        P.rotate_world(rig, 'Body', Z, yaw)
    if pitch:
        P.rotate_world(rig, 'Body', X, -pitch)
    if roll:
        P.rotate_world(rig, 'Body', Y, -roll)
    lens = rig.pose.bones['Lens']
    lens.location = (0, -recoil, 0)          # bone Y points forward (base -> apex): -recoil pushes the dome in
    lens.scale = (iris, 1.0, iris)
    th = rig.pose.bones['Thrust']
    th.scale = (thrust[0], thrust[1], thrust[0])
    bpy.context.view_layer.update()
    # tendons: hang against the body's tilt (gravity), trail with motion, sway with a lag along the chain
    for k, chain in enumerate(TENDONS):
        for j, name in enumerate(chain):
            dp, ds = (sway[k][j] if sway else (0.0, 0.0))
            ax = (pitch * 0.55 if j == 0 else 0.0) + trail * (0.5 if j == 0 else 0.3) + dp
            ay = (-roll * 0.55 if j == 0 else 0.0) + ds
            if ax:
                P.rotate_world(rig, name, X, ax)
            if ay:
                P.rotate_world(rig, name, Y, ay)


_dg = bpy.context.evaluated_depsgraph_get()


def verts():
    ev = mesh.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3)


def thrust_low():
    ev = thrust_obj.evaluated_get(_dg); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3) @ np.array(thrust_obj.matrix_world)[:3, :3].T + np.array(thrust_obj.matrix_world)[:3, 3]
    return float(co[:, 2].min())


def sway_set(t, period, amp, lag=0.9, side_amp=None, cycles=1):
    w = 2 * math.pi * cycles * t / period
    side_amp = amp * 0.6 if side_amp is None else side_amp
    out = []
    for k in range(3):
        ph = k * 2.1
        out.append([(amp * (0.5 + 0.35 * j) * math.sin(w - j * lag + ph),
                     side_amp * (0.5 + 0.35 * j) * math.sin(w * 0.5 + ph * 0.7 - j * lag)) for j in range(3)])
    return out


def pulse(t, hz, amp_r, amp_l):
    s = math.sin(2 * math.pi * hz * t)
    return (1.0 + amp_r * s, 1.0 + amp_l * s)


def hover(t, period, lean, bob, trail, sway_amp, hz, amp_r, amp_l):
    u = t / period; w = 2 * math.pi * u
    pose(lift=bob * math.sin(w), pitch=lean + 2.0 * math.sin(w + 0.6), roll=2.0 * math.sin(w * 0.5 + 0.3),
         yaw=1.5 * math.sin(w * 0.5 + 1.0), trail=trail, sway=sway_set(t, period, sway_amp),
         thrust=pulse(t, hz, amp_r, amp_l))


def keyed(keys, t):
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6))
            return {k: a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * u for k in set(a) | set(b)}
    return dict(keys[-1][1])


ATTACK = [
    (0.00, {}),
    (0.18, {'pitch': -4, 'lift': 0.01, 'forward': 0.01, 'trail': 3}),
    (IMPACT, {'pitch': -3, 'lift': 0.01, 'forward': 0.012, 'trail': 2}),
    (IMPACT + 2 / FPS, {'pitch': -13, 'lift': 0.03, 'forward': -0.07, 'recoil': 0.012, 'trail': -14}),
    (0.48, {'pitch': -5, 'lift': 0.012, 'forward': -0.03, 'recoil': 0.003, 'trail': 8}),
    (0.75, {}),
]
HIT = [
    (0.00, {}),
    (0.08, {'forward': -0.09, 'lift': 0.03, 'pitch': -14, 'yaw': 16, 'roll': -18, 'trail': -20}),
    (0.20, {'forward': -0.07, 'lift': 0.02, 'pitch': 6, 'yaw': -7, 'roll': 9, 'trail': 14}),
    (0.32, {'forward': -0.04, 'lift': 0.01, 'pitch': -3, 'yaw': 3, 'roll': -4, 'trail': -5}),
    (0.5, {}),
]


def attack(t):
    k = keyed(ATTACK, t)
    k['sway'] = sway_set(t, 0.75, 4.0)
    k['thrust'] = pulse(t, 4, 0.04, 0.10)
    pose(**k)


def hit(t):
    k = keyed(HIT, t)
    k['sway'] = sway_set(t, 0.5, 14.0 * (1 - t / 0.5), cycles=2)
    k['thrust'] = pulse(t, 6, 0.08, 0.2)
    pose(**k)


def fidget(t):
    u = t / 1.5
    look = math.sin(2 * math.pi * u) * ss(u * 4) * ss((1 - u) * 4)
    turn = 28 * look
    pose(yaw=turn, roll=-4 * look, pitch=3 * math.sin(math.pi * u), lift=0.008 * math.sin(2 * math.pi * u),
         sway=[[(0.0, -0.45 * turn * (0.4 + 0.3 * j) * math.cos(0.4 * j)) for j in range(3)] for _ in range(3)],
         thrust=pulse(t, 2, 0.03, 0.08))


def tendon_floor():
    """Each tendon segment whose end dips under a clearance above the floor is turned up about its head (keeping its
    horizontal heading), from the root down, so the cables lie on the floor. The clearance starts at the cable radius
    and grows by the chain's measured dip (the claw hooks below the bone line) until no vertex is under the floor."""
    snap = {b.name: b.matrix.copy() for b in rig.pose.bones}
    for k, chain in enumerate(TENDONS):
        clear = TENDON_R
        for it in range(6):
            for name in chain:
                rig.pose.bones[name].matrix = snap[name]
                bpy.context.view_layer.update()
            _floor_chain(chain, clear)
            dip = verts()[vpart == k + 1, 2].min()
            if dip >= -1e-4:
                break
            clear += -dip + 0.001
        for name in chain:
            snap[name] = rig.pose.bones[name].matrix.copy()


def _floor_chain(chain, clear):
    TENDON_R_ = clear
    if True:
        for name in chain:
            b = rig.pose.bones[name]
            head = rig.matrix_world @ b.head; tail = rig.matrix_world @ b.tail
            L = (tail - head).length
            if tail.z >= TENDON_R_ - 1e-4:
                continue
            d = tail - head
            hor = Vector((d.x, d.y, 0))
            if hor.length < 1e-4:
                hor = Vector((0, 1, 0))
            hor.normalize()
            dz = max(-1.0, min(1.0, (TENDON_R_ - head.z) / L))
            target = head + (hor * math.sqrt(max(0.0, 1 - dz * dz)) + Vector((0, 0, dz))) * L
            P.aim_bone(rig, name, target)


DEATH_KEYS = [
    (0.00, {}),
    (0.08, {'yaw': 9, 'roll': 8, 'pitch': -8, 'lift': 0.02, 'forward': -0.03, 'trail': -10}),
    (0.16, {'yaw': -8, 'roll': -9, 'pitch': -4, 'lift': 0.025, 'forward': -0.02, 'trail': 8}),
    (0.26, {'yaw': 5, 'roll': 6, 'pitch': -6, 'lift': 0.02, 'trail': -6}),
    (0.875, {'yaw': 12, 'roll': 22, 'pitch': 16, 'forward': 0.06, 'trail': -55}),
    (1.05, {'yaw': 13, 'roll': 17, 'pitch': 10, 'forward': 0.07, 'trail': -40}),
    (1.5, {'yaw': 14, 'roll': 18, 'pitch': 9, 'forward': 0.075, 'trail': -30}),
]
LAND, BOUNCE = 0.875, 0.035


def death(t):
    k = keyed(DEATH_KEYS, t)
    k['iris'] = 1.0 - 0.7 * ss((t - 0.12) / 0.3)
    flick = (t < 0.3) and (int(t * FPS) % 3 == 1)
    k['thrust'] = (0.001, 0.001) if (t >= 0.3 or flick) else pulse(t, 8, 0.1, 0.3)
    k['sway'] = sway_set(t, 0.5, 10.0 * max(0.0, 1 - t / 0.9), cycles=2)
    # fall: the hover offset and the body's height above the floor go to zero together
    fall = 0.0 if t < 0.28 else min(1.0, ((t - 0.28) / (LAND - 0.28)) ** 2)
    bounce = 0.0
    if t > LAND:
        bounce = BOUNCE * math.sin(math.pi * min(1.0, (t - LAND) / 0.2)) * (t - LAND < 0.2)
    lift = k.pop('lift', 0.0)
    pose(lift=lift * (1 - fall), hover=HOVER, **k)
    co = verts()
    low = co[BODY, 2].min()
    root = rig.pose.bones['Body']
    root.matrix = Matrix.Translation(Vector((0, 0, -low * fall + bounce * (1 if fall >= 1 else 0)))) @ root.matrix
    bpy.context.view_layer.update()
    tendon_floor()


LIVING = {
    'Standing': (2.0, True, lambda t: hover(t, 2.0, 0.0, 0.015, 0.0, 7.0, 3.0, 0.05, 0.12)),
    'Walking': (1.0, True, lambda t: hover(t, 1.0, 8.0, 0.012, 22.0, 9.0, 5.0, 0.06, 0.18)),
    'Running': (0.75, True, lambda t: hover(t, 0.75, 15.0, 0.012, 38.0, 10.0, 8.0, 0.08, 0.25)),
    'Attack': (0.75, False, attack),
    'Hit': (0.5, False, hit),
    'Fidget': (1.5, False, fidget),
}

# ---- hover offset: lowest point over every living frame on the floor
low = 1e9
for name, (sec, loop, fn) in LIVING.items():
    n = int(round(sec * FPS))
    for f in range(n + 1):
        fn(f / FPS); co = verts()
        low = min(low, co[LIVE, 2].min(), thrust_low())
HOVER = -low
print('HOVER offset', round(HOVER, 4))


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None:
        rig.animation_data_create()
    n = int(round(seconds * FPS))
    rig.animation_data.action = None
    poses, lows = [], []
    for f in range(n + 1):
        fn((f % n) / FPS if loop else f / FPS)
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy()) for b in rig.pose.bones})
        co = verts()
        lows.append((float(co[LIVE, 2].min()), float(co[BODY, 2].min()), float(min(co[vpart == k, 2].min() for k in (1, 2, 3))),
                     thrust_low()))
    rig.animation_data.action = act
    prev = {}
    for f, frame in enumerate(poses):
        for b in rig.pose.bones:
            q, loc, sc = frame[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0:
                q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc; b.scale = sc
            b.keyframe_insert('rotation_quaternion', frame=f + 1)
            b.keyframe_insert('location', frame=f + 1)
            b.keyframe_insert('scale', frame=f + 1)
    rig.animation_data.action = None
    return act, lows


report = {}
for name, (sec, loop, fn) in LIVING.items():
    _, lows = key_action(name, sec, loop, fn)
    L = np.array(lows)
    report[name] = {'seconds': sec, 'min_z_cm': round(L[:, [0, 3]].min() * 100, 2),
                    'casing_low_cm': [round(L[:, 1].min() * 100, 2), round(L[:, 1].max() * 100, 2)],
                    'cable_low_cm': round(L[:, 2].min() * 100, 2), 'thrust_tip_cm': round(L[:, 3].min() * 100, 2)}
    print('CLIP', name, report[name], flush=True)
_, lows = key_action('Death', 1.5, False, death)
report['Death'] = {'seconds': 1.5, 'min_z_cm': round(min(l[0] for l in lows) * 100, 2), 'end_low_cm': round(lows[-1][0] * 100, 2)}
print('CLIP Death', report['Death'])
_, lows = key_action('Dead', 1.0, False, lambda t: death(1.5))
report['Dead'] = {'seconds': 1.0, 'min_z_cm': round(min(l[0] for l in lows) * 100, 2)}
print('CLIP Dead', report['Dead'])
co = verts(); print('DEAD body low cm', round(co[BODY, 2].min() * 100, 2), 'all low', round(co[LIVE, 2].min() * 100, 2))
json.dump({'fps': FPS, 'hover_m': HOVER, 'impact_s': IMPACT, 'clips': report},
          open(os.path.join(HERE, 'work', 'anim_info.json'), 'w'), indent=1)
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
print('SAVED anim_v1.blend')
