"""Procedural clips for the MM6 Reactor (24 fps), choreographed from the native rea frames (manifest timings).

Every part is rigid; each frame turns a parameter set into one world transform per bone (no IK, no weights).
Parts switch on and off by bone scale (STEP-interpolated after export by fix_gltf.py), because skinned materials
cannot animate in the engine.
  Standing 1.125 s loop  arc flicker, scrolling screens, lamps as the native reasta frames (fidget/walk use it)
  Attack   2.4 s         arms emerge, spread wide, swing in, charge star, discharge flash at 1.90 s (impact marker:
                         the missile leaves Socket_Arc there; native action 2.0 s), arms retract
  Hit      1.125 s       power cut (glows, screens, arc out), chamber swings on its mount, base jolts, power back
  Death    1.75 s        overload flash, glass bursts, bowl tears, dome top bursts with debris, liquid drains as a
                         stream onto the dome, the puddle shrinks; Dead holds the wreck (native reade07)
Reads work/model_v1.blend, writes work/anim_v1.blend."""
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import reactor_blender as RB  # noqa: E402
import reactor_geometry as G  # noqa: E402
import reactor_layout as L  # noqa: E402

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'model_v1.blend'))
rig = bpy.data.objects['Reactor_Rig']
FPS = 24
REST = {b.name: b.bone.matrix_local.copy() for b in rig.pose.bones}
HEAD = {name: m.translation.copy() for name, m in REST.items()}
PARENT = {b.name: (b.parent.name if b.parent else None) for b in rig.pose.bones}
DEPTH = {}
for name in PARENT:
    d, p = 0, PARENT[name]
    while p: d += 1; p = PARENT[p]
    DEPTH[name] = d
ORDER = sorted(PARENT, key=lambda n: DEPTH[n])
for b in rig.pose.bones:
    b.rotation_mode = 'QUATERNION'
TOGGLES = set(RB.TOGGLES)
rng = random.Random(13)


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def lerp(a, b, t): return a + (b - a) * t


def keyed(keys, t):
    """Smoothstep between parameter dicts (or angle lists) at key times."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            u = ss((t - t0) / max(t1 - t0, 1e-6))
            if isinstance(a, dict):
                return {k: a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * u for k in set(a) | set(b)}
            return [x + (y - x) * u for x, y in zip(a, b)]
    return keys[-1][1]


def about(pivot, axis, degrees):
    return Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(degrees), 4, axis) @ Matrix.Translation(-pivot)


def scaled(pivot, s):
    return Matrix.Translation(pivot) @ Matrix.Scale(max(s, 0.0), 4) @ Matrix.Translation(-pivot)


Y = Vector((0, 1, 0)); X = Vector((1, 0, 0)); Z = Vector((0, 0, 1))
POSES = G.POSES


def arm_world(prefix, side, angles, parent_delta, s):
    """World deltas for one arm chain: FK in the XZ plane from absolute segment angles, emerging by scale s."""
    upper = prefix == 'UArm'
    sh = L.UPPER_SHOULDER if upper else L.LOWER_SHOULDER
    lengths = L.UPPER_LENGTHS if upper else L.LOWER_LENGTHS
    sx = -abs(sh[0]) if side == 'L' else abs(sh[0])
    joints = G.arm_joints((sx, sh[1]), lengths, angles)
    rest = G.rest_arm(side, upper)
    a0 = 180.0 if side == 'L' else 0.0
    shoulder = Vector((sx, 0, sh[1]))
    out = {}
    for k, seg in enumerate(('Up', 'Fore', 'Tool')):
        jr = Vector((rest[k][0], 0, rest[k][1])); jn = Vector((joints[k][0], 0, joints[k][1]))
        local = Matrix.Translation(jn) @ Matrix.Rotation(math.radians(a0 - angles[k]), 4, Y) @ Matrix.Translation(-jr)
        out[f'{prefix}{side}_{seg}'] = parent_delta @ scaled(shoulder, s) @ local
    return out


def pose(p):
    """p keys: on (set of toggle bones shown), sc (bone -> scale for continuous toggles), chamber_roll/pitch (deg),
    chamber_dz, body_dz, body_roll, arms ({'LArm'/'UArm': (left angles, right angles, scale)}),
    fly ({bone: Matrix delta about its own head}), nozzle (Matrix)."""
    g = lambda k: p.get(k, 0.0)
    D = {}
    D['Root'] = Matrix.Identity(4)
    D['Base'] = Matrix.Identity(4)
    body_pivot = HEAD['Body']
    D['Body'] = Matrix.Translation(Vector((0, 0, g('body_dz')))) @ about(body_pivot, Y, g('body_roll'))
    cp = HEAD['Chamber']
    D['Chamber'] = (Matrix.Translation(Vector((0, 0, g('chamber_dz')))) @ about(cp, Y, -g('chamber_roll'))
                    @ about(cp, X, g('chamber_pitch')))
    on = p.get('on', RB.IDLE_ON); sc = p.get('sc', {}); fly = p.get('fly', {})
    arms = p.get('arms', {})
    for name in ORDER:
        if name in D:
            continue
        parent = PARENT[name]
        base = D[parent] if parent else Matrix.Identity(4)
        if name.startswith(('LArm', 'UArm')):
            prefix, rest_name = name[:4], name[4:]
            side = rest_name[0]
            if f'{prefix}{side}_Up' not in D:
                fold = POSES['lower_fold' if prefix == 'LArm' else 'upper_fold']
                left, right, s = arms.get(prefix, (fold[0], fold[1], 0.0))
                parent_delta = D['Body'] if prefix == 'LArm' else D['Chamber']
                D.update(arm_world(prefix, side, left if side == 'L' else right, parent_delta, s))
            continue
        local = fly.get(name, Matrix.Identity(4))
        s = 1.0
        if 'Wave' in name:
            # an inactive wave drops 38 mm toward the axis (+Y at the front), inside the shell behind the dark window;
            # the active one sits 8 mm proud of it (both clear of depth-precision fighting at room distance)
            local = local @ Matrix.Translation(Vector((0, 0.0 if name in on else 0.038, 0)))
            D[name] = base @ local
            continue
        if name in TOGGLES:
            s = sc.get(name, 1.0 if name in on else 0.0)
        D[name] = base @ local @ scaled(HEAD[name], s)
    for name in ORDER:
        rig.pose.bones[name].matrix = D[name] @ REST[name]
        bpy.context.view_layer.update()


def idle_parts(t, rate=1.0):
    """Arc variant, screen waveforms and lamps over the 1.125 s standing loop (lamps follow native reasta00-05)."""
    on = set(RB.IDLE_ON) - {'Arc1', 'BandWave1', 'LidWave1', 'LampRed', 'LampG1', 'LampG2'}
    seq = [1, 3, 2, 4, 1, 2, 4, 3, 2]
    on.add(f'Arc{seq[int(t * rate / 0.125 + 1e-6) % 9]}')
    w = int(t / 0.375 + 1e-6) % 3
    on.add(f'BandWave{w + 1}'); on.add(f'LidWave{(w + 1) % 3 + 1}')
    slot = int(t / 0.1875 + 1e-6) % 6
    if [1, 1, 0, 0, 0, 1][slot]: on.add('LampRed')
    if [0, 1, 1, 1, 1, 1][slot]: on |= {'LampG1', 'LampG2'}
    return on


def hum(t, p):
    """Powered-machine life over the 1.125 s loop: the liquid churns (a slow bob and twist of its lumpy surface)
    and the glows breathe; both close seamlessly on the loop."""
    w = 2 * math.pi * t / 1.125
    liq = Matrix.Translation(Vector((0, 0, 0.012 * math.sin(w)))) @ about(HEAD['Liq100'], Z, 5.0 * math.sin(w + 1.1))
    fly = p.setdefault('fly', {})
    for name in ('Liq100', 'Liq60', 'Liq25'):
        fly.setdefault(name, liq)
    sc = p.setdefault('sc', {})
    on = p.get('on', RB.IDLE_ON)
    for name, phase in (('CapGlow', 0.0), ('BowlGlow', 1.7)):
        if name in on:
            sc.setdefault(name, 1.0 + 0.012 * (0.5 + 0.5 * math.sin(2 * w + phase)))   # outward only
    return p


def standing(t):
    pose(hum(t, {'on': idle_parts(t)}))


def attack(t):
    p = {}
    on = idle_parts(t)
    # arms: emerge, spread, hold, swing in, discharge recoil, retract
    s = ss(t / 0.18) * (1.0 - ss((t - 2.18) / 0.2))
    for prefix, low in (('LArm', 'lower'), ('UArm', 'upper')):
        keys = [(0.0, POSES[f'{low}_fold']), (0.18, POSES[f'{low}_fold']), (0.60, POSES[f'{low}_wide']),
                (0.90, POSES[f'{low}_wide']), (1.40, POSES[f'{low}_converged']), (1.86, POSES[f'{low}_converged']),
                (1.98, ([a + 7 for a in POSES[f'{low}_converged'][0]], [a - 7 for a in POSES[f'{low}_converged'][1]])),
                (2.22, POSES[f'{low}_fold']), (2.4, POSES[f'{low}_fold'])]
        left = keyed([(k, v[0]) for k, v in keys], t)
        right = keyed([(k, v[1]) for k, v in keys], t)
        if 0.6 < t < 0.9:   # restless tool tips while spread
            j = 4.0 * math.sin(t * 31.0)
            left = [left[0], left[1] + j, left[2] - j]; right = [right[0], right[1] - j, right[2] + j]
        p.setdefault('arms', {})[prefix] = (left, right, s)
    if t >= 1.40:
        on -= {f'Arc{k}' for k in range(1, 5)}
        if t < 2.0:
            on.add(f'ArcBig{int(t * 12 + 1e-6) % 3 + 1}')
        elif t < 2.1:
            on.add('Arc1')
        else:
            on.add(f'Arc{[1, 3, 2, 4][int(t * 8) % 4]}')
    elif t >= 1.0:   # faster idle flicker while the arms swing in
        on -= {f'Arc{k}' for k in range(1, 5)}
        on.add(f'Arc{[1, 3, 2, 4][int(t * 12 + 1e-6) % 4]}')
    if 1.80 <= t < 1.98:
        on.add('Flash')
    # lamps: red blinks while charging
    if 1.40 <= t < 1.98:
        on.discard('LampRed')
        if int(t * 8) % 2 == 0: on.add('LampRed')
    p['on'] = on
    p['chamber_dz'] = 0.02 * math.exp(-((t - 1.92) / 0.06) ** 2)
    p['chamber_roll'] = 1.2 * math.sin(t * 40) * math.exp(-((t - 1.95) / 0.12) ** 2)
    pose(hum(t, p))


def hit(t):
    on = set(RB.IDLE_ON) - {'CapGlow', 'BowlGlow', 'Arc1', 'BandWave1', 'LidWave1', 'LampRed', 'LampG1', 'LampG2'}
    # power cut until 0.86 s, with a flicker as it returns
    powered = t >= 0.98 or (0.86 <= t < 0.90)
    if powered:
        on |= {'CapGlow', 'BowlGlow', 'Arc1', 'BandWave1', 'LidWave1'}
    slot = min(int(t / 0.1875 + 1e-6), 5)          # native reawi01-06 lamp states
    if [1, 0, 0, 0, 1, 1][slot]: on.add('LampRed')
    if [1, 1, 1, 1, 0, 0][slot]: on |= {'LampG1', 'LampG2'}
    roll = keyed([(0.0, {'r': 0}), (0.10, {'r': 9.0}), (0.32, {'r': -6.0}), (0.54, {'r': 3.5}), (0.76, {'r': -1.6}),
                  (0.96, {'r': 0.5}), (1.125, {'r': 0.0})], t)['r']
    body = keyed([(0.0, {'z': 0}), (0.05, {'z': 0.045}), (0.16, {'z': -0.006}), (0.26, {'z': 0.012}),
                  (0.40, {'z': 0.0})], t)['z']
    pose({'on': on, 'chamber_roll': roll, 'chamber_pitch': 0.25 * roll, 'body_dz': body,
          'body_roll': 0.25 * math.sin(t * 50) * math.exp(-t / 0.15)})


# Death: precomputed flying pieces (shards from the glass, debris from the dome top and the bowl).
SHARDS = {}
for k in range(1, 9):
    h = HEAD[f'Shard{k}']
    out = Vector((h.x, h.y, 0)).normalized()
    SHARDS[f'Shard{k}'] = (out * rng.uniform(1.0, 1.8) + Vector((0, 0, rng.uniform(0.3, 0.9))),
                           Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized(),
                           rng.uniform(500, 900))
DEBRIS = {}
for k in range(1, 9):
    h = HEAD[f'Debris{k}']
    out = Vector((h.x, h.y, 0)).normalized() if Vector((h.x, h.y, 0)).length > 1e-3 else Vector((1, 0, 0))
    v = out * rng.uniform(0.8, 1.5) + Vector((0, 0, rng.uniform(1.6, 2.6) if k <= 5 else rng.uniform(-0.3, 0.4)))
    DEBRIS[f'Debris{k}'] = (v, Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized(),
                            rng.uniform(300, 700))
GRAV = 7.0
BURST = 0.22


def flight(name, table, t, life):
    v, axis, spin = table[name]
    u = max(0.0, t - BURST)
    pos = v * u + Vector((0, 0, -0.5 * GRAV * u * u))
    h = HEAD[name]
    if h.z + pos.z < 0.06:            # floor rule: pieces stop on the floor
        pos.z = 0.06 - h.z
    m = Matrix.Translation(pos) @ about(h, axis, spin * u)
    s = 1.0 - ss((u - life * 0.7) / (life * 0.3))
    return m, s


def death(t):
    on = set()
    sc = {}
    fly = {}
    p = {'on': on, 'sc': sc, 'fly': fly}
    burst = t >= BURST
    if not burst:
        on |= {'Glass', 'CapGlow', 'BowlGlow', 'DomeTop', 'Spire', 'BowlLower', 'Nozzle', 'Liq100',
               'BandWave1', 'LidWave1', f'ArcBig{int(t * 16) % 3 + 1}'}
        if t >= 0.04: on.add('Flash')
        p['chamber_roll'] = 1.5 * math.sin(t * 70) * (t / BURST)
        p['body_roll'] = 0.6 * math.sin(t * 90) * (t / BURST)
    else:
        on |= {'GlassBroken', 'Crown', 'BowlTorn'}
        if t < 0.32: on.add('Flash')
        on.add('Liq100' if t < 0.40 else 'Liq60' if t < 0.62 else 'Liq25' if t < 0.85 else '')
        if 0.75 <= t < 1.3 and int(t * 6) % 2 == 0:   # native reade04-06: green lamps flicker on the dying panel
            on |= {'LampG1', 'LampG2'}
        u = t - BURST
        p['chamber_roll'] = lerp(4.0 * math.exp(-u * 3) * math.sin(u * 18), 2.2, ss(u / 1.2))
        p['chamber_dz'] = -0.03 * ss(u / 0.4)
        p['body_dz'] = -0.012 * ss(u / 0.2)
        for name in SHARDS:
            m, s = flight(name, SHARDS, t, 0.8)
            fly[name] = m; sc[name] = s
        for name in DEBRIS:
            m, s = flight(name, DEBRIS, t, 1.05)
            fly[name] = m; sc[name] = s
        # nozzle drops and shrinks
        nu = ss(u / 0.5)
        fly['Nozzle'] = Matrix.Translation(Vector((0.05 * nu, 0, -0.45 * nu * nu))) @ about(HEAD['Nozzle'], Y, 40 * nu)
        sc['Nozzle'] = 1.0 - ss((u - 0.2) / 0.3)
        # stream: grows down from the bowl, ends by retracting upward
        sc['GooStream'] = ss((t - 0.24) / 0.16) * (1.0 - ss((t - 0.95) / 0.15))
        sc['GooBlob'] = (0.2 + 0.8 * ss((t - 0.38) / 0.47)) * (1.0 - ss((t - 1.2) / 0.45)) if t >= 0.38 else 0.0
    on.discard('')
    pose(p)


def dead(t):
    death(1.75)


def key_action(name, seconds, fn, loop):
    """Pose every frame with no action assigned, then key the stored bases (quaternion signs kept continuous)."""
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    if rig.animation_data is None: rig.animation_data_create()
    rig.animation_data.action = None
    act = bpy.data.actions.new(name); act.use_fake_user = True
    n = int(round(seconds * FPS))
    poses = []
    for f in range(n + 1):
        fn((f % n) / FPS if loop else f / FPS)
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy()) for b in rig.pose.bones})
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
    print('CLIP', name, n, 'frames', flush=True)


CLIPS = [('Standing', 1.125, standing, True), ('Attack', 2.4, attack, False), ('Hit', 1.125, hit, False),
         ('Death', 1.75, death, False), ('Dead', 1.0, dead, False)]
only = os.environ.get('REA_CLIPS')
for name, seconds, fn, loop in CLIPS:
    if only and name not in only.split(','):
        continue
    key_action(name, seconds, fn, loop)
rig.animation_data.action = bpy.data.actions['Standing'] if bpy.data.actions.get('Standing') else None
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
print('SAVED anim_v1.blend')
