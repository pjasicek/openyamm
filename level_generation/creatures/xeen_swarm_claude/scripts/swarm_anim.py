"""Procedural clips of the swarm (30 fps). Each Stinger W<i> drifts on its own closed Lissajous path (whole cycles per
clip, so loops close), turns and banks with its motion and buzzes its wings (about 10 Hz, a 3-frame cycle at 30 fps, per
insect phase). The one Fly loop serves standing, walking and running (a flyer).

  Fly     2.0 s loop   the cloud drifts and buzzes
  Attack  1.0 s        the insects dart at the party one after another, abdomens down (the sting): IMPACT 0.45 s
  Hit     0.5 s        the cloud scatters outward and gathers again
  Death   1.6 s        the insects drop one by one, spin and land on their backs, wings still
  Dead    held         the insects on the floor
  Fidget  2.0 s        the cloud swirls a quarter turn about its middle and back
Flyer rule (CLAUDE_QUADRUPED_PLAYBOOK.md, Flyers): the lowest living point over every living clip meets the floor;
the offset is applied to every living clip (Death eases it out as the insects land).
Reads work/swarm_rig.blend, writes work/swarm_anim.blend and work/anim_info.json."""
import bpy, os, sys, json, math, random
import numpy as np
from mathutils import Vector, Matrix, Quaternion
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(HERE, 'work', 'swarm_anim_base.blend')
bpy.ops.wm.open_mainfile(filepath=src if os.path.exists(src) else os.path.join(HERE, 'work', 'swarm_rig.blend'))
rig = bpy.data.objects['Swarm_Rig']; meshes = [bpy.data.objects['Swarm'], bpy.data.objects['SwarmWings']]
FPS = 30
IMPACT = 0.45
pb = rig.pose.bones
for b in pb:
    b.rotation_mode = 'QUATERNION'
layout = json.load(open(os.path.join(HERE, 'work', 'swarm_layout.json')))['layout']
N = len(layout)
REST = {b.name: b.bone.matrix_local.copy() for b in pb}
rng = random.Random(7)
PH = [(rng.random(), rng.random(), rng.random(), rng.random()) for _ in range(N)]
AMP = [Vector((0.12 + 0.07 * rng.random(), 0.10 + 0.06 * rng.random(), 0.08 + 0.06 * rng.random())) for _ in range(N)]
FREQ = [(1, 2, 3), (2, 1, 2), (1, 3, 2), (3, 2, 1), (2, 3, 1), (1, 1, 2), (3, 1, 2)]
LIFT = 0.0                                  # set after the flyer measurement


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def bump(t, a, b):
    return 0.0 if t <= a or t >= b else math.sin(math.pi * (t - a) / (b - a)) ** 2


def drift(i, t, L=2.0):
    a = AMP[i]; f = FREQ[i]; p = PH[i]
    w = 2 * math.pi / L
    off = Vector((a.x * math.sin(w * f[0] * t + 6.28 * p[0]), a.y * math.sin(w * f[1] * t + 6.28 * p[1]),
                  a.z * math.sin(w * f[2] * t + 6.28 * p[2])))
    vel = Vector((a.x * f[0] * math.cos(w * f[0] * t + 6.28 * p[0]), a.y * f[1] * math.cos(w * f[1] * t + 6.28 * p[1]),
                  0)) * w
    return off, vel


def place(i, off=Vector(), yaw=0.0, pitch=0.0, roll=0.0, flap=None, t=0.0, fold=0.0):
    """Wasp i: rest pose moved by off (world), turned about its own centre; wings flap (deg amplitude) or fold."""
    name = f'W{i}'
    R = REST[name]
    c = R.translation
    rot = (Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(pitch), 4, 'X')
           @ Matrix.Rotation(math.radians(roll), 4, 'Y'))
    M = Matrix.Translation(c + off + Vector((0, 0, LIFT))) @ rot @ Matrix.Translation(-c) @ R
    pb[name].matrix = M
    bpy.context.view_layer.update()
    body = M @ R.inverted()
    for k in ('FL', 'FR', 'HL', 'HR'):
        wn = f'W{i}_{k}'; WR = REST[wn]
        side = 1 if k[1] == 'L' else -1
        if flap is not None:
            ang = flap * math.sin(2 * math.pi * 10 * t + 6.28 * PH[i][3] + (0.4 if k[0] == 'H' else 0))
        else:
            ang = 0
        ang -= fold
        h = WR.translation
        # flap about the wasp's long axis (local Y of the wasp) through the hinge; + raises the wing
        axis = (R.to_3x3() @ Vector((0, 1, 0))).normalized()
        F = Matrix.Translation(h) @ Matrix.Rotation(math.radians(ang * side), 4, axis) @ Matrix.Translation(-h)
        pb[wn].matrix = body @ F @ WR
    bpy.context.view_layer.update()


def fly(t, L=2.0):
    for i in range(N):
        off, vel = drift(i, t, L)
        yaw = max(-35, min(35, -math.degrees(math.atan2(vel.x, 1.2))))
        place(i, off, yaw=yaw, pitch=-6 * vel.y, roll=12 * vel.x, flap=40, t=t)


def attack(t):
    for i in range(N):
        off, vel = drift(i, t)
        start = 0.12 + 0.04 * i
        k = bump(t, start, start + 0.55)
        dart = Vector((0.15 * (-off.x), -0.75 * k, -0.25 * k * (layout[i][0][2] - 0.6)))
        place(i, off + dart, pitch=-35 * k, flap=45, t=t)


def hit(t):
    k = bump(t, 0.0, 0.5)
    for i in range(N):
        off, vel = drift(i, t)
        p = Vector(layout[i][0]) - Vector((0, 0, 0.75))
        place(i, off + p.normalized() * 0.22 * k, roll=25 * k * (1 if i % 2 else -1), flap=50, t=t)


GROUND = {}


def death(t):
    for i in range(N):
        off, vel = drift(i, min(t, 0.2))
        t0 = 0.05 + 0.11 * ((i * 3) % N); dur = 0.55
        k = ss((t - t0) / dur)
        p = Vector(layout[i][0])
        drop = Vector((0, 0, -(p.z + LIFT - GROUND.get(i, 0.03)) * k * k))     # the centre ends at GROUND[i]
        place(i, off * (1 - k) + drop, yaw=200 * k * (1 if i % 2 else -1),
              roll=180 * k, flap=40 * (1 - k), t=t, fold=20 * k)


def dead(t):
    death(1.6)


def fidget(t, L=2.0):
    a = math.radians(90 * bump(t, 0.0, L))
    for i in range(N):
        off, vel = drift(i, t, L)
        p = Vector(layout[i][0]); c = Vector((0, 0, p.z))
        q = Matrix.Rotation(a, 4, 'Z') @ (p - c) + c
        place(i, off + (q - p), yaw=math.degrees(a) * 0.6, flap=40, t=t)


def world_co():
    dg = bpy.context.evaluated_depsgraph_get(); out = []
    for m in meshes:
        ev = m.evaluated_get(dg); me = ev.to_mesh()
        a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', a); ev.to_mesh_clear()
        out.append(a.reshape(-1, 3) @ np.array(m.matrix_world.to_3x3()).T + np.array(m.matrix_world.translation))
    return np.concatenate(out)


def reset():
    for b in pb:
        b.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


INFO = {}
LIVING = {'Fly': (60, fly, True), 'Attack': (30, attack, False), 'Hit': (15, hit, False), 'Fidget': (60, fidget, False)}
# flyer rule: the lowest point over all living clips meets the floor
low = 1e9
for name, (n, fn, loop) in LIVING.items():
    for f in range(n + 1):
        reset(); fn(f / FPS); low = min(low, world_co()[:, 2].min())
LIFT = -low
# each insect's corpse height: its lowest point when lying on its back, measured
reset()
for i in range(N):
    GROUND[i] = 0.0
print('LIFT', round(LIFT, 4))


def key_action(name, n, fn, loop):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None: rig.animation_data_create()
    rig.animation_data.action = None
    poses, lows = [], []
    for f in range(n + 1):
        reset(); fn(f / FPS)
        lows.append(float(world_co()[:, 2].min()))
        poses.append({b.name: (b.rotation_quaternion.copy(), b.location.copy(), b.scale.copy()) for b in pb})
    if loop: poses[-1] = poses[0]
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
    prev = {}
    for f, pose in enumerate(poses):
        for b in pb:
            q, loc, sc = pose[b.name]
            if b.name in prev and prev[b.name].dot(q) < 0: q = -q
            prev[b.name] = q
            b.rotation_quaternion = q; b.location = loc; b.scale = sc
            for path in ('rotation_quaternion', 'location', 'scale'):
                b.keyframe_insert(path, frame=f)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n
    act['fps'] = FPS
    rig.animation_data.action = None
    INFO[name] = {'seconds': round(n / FPS, 4), 'lowest_cm': [round(min(lows) * 100, 2), round(max(lows) * 100, 2)]}
    print('CLIP', name, INFO[name], flush=True)


for name, (n, fn, loop) in LIVING.items():
    key_action(name, n, fn, loop)
# corpse: ground each insect on its own lowest point after the flip (measure once, then key)
reset(); death(1.6)
dg = bpy.context.evaluated_depsgraph_get()
lows_i = {i: 1e9 for i in range(N)}
for m in meshes:                                   # body and wings: each insect's lowest point when lying
    names = [g.name for g in m.vertex_groups]
    ev = m.evaluated_get(dg); me = ev.to_mesh()
    pos = np.array([tuple(m.matrix_world @ v.co) for v in me.vertices]); ev.to_mesh_clear()
    dom = [names[max(v.groups, key=lambda g: g.weight).group].split('_')[0] for v in m.data.vertices]
    for i in range(N):
        sel = np.array([d == f'W{i}' for d in dom])
        if sel.any():
            lows_i[i] = min(lows_i[i], float(pos[sel, 2].min()))
for i in range(N):
    GROUND[i] = -lows_i[i] + 0.002
key_action('Death', 48, death, False)
key_action('Dead', 30, dead, False)
json.dump({'clips': INFO, 'impact': IMPACT, 'lift': LIFT}, open(os.path.join(HERE, 'work', 'anim_info.json'), 'w'), indent=1)
reset(); rig.animation_data.action = bpy.data.actions['Fly']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'swarm_anim.blend'))
print('SAVED swarm_anim.blend')
