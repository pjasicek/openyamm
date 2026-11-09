"""Procedural sea serpent clips (24 fps) on work/rig_v1.blend (+ foam collar) -> work/anim_v1.blend.

Every frame defines the centreline from the root at the waterline up to the head and fits the bones to it
(parallel-transported frames from the root, disconnected bones: no twist, no stretching). Each segment's rest
direction is turned by pitch (about X: + leans forward / head down), side (about Y: + leans toward +X) and yaw (about
Z: turns the arched top). Floor rule: joints stay at least their body radius above the water (z 0), except when the
body sinks (`sink` lowers everything after the fit). The foam collar's bone spins slowly and pulses; it shrinks away
while the body sinks.
Native timings (manifest): every action 1.125 s.
  Standing 3.0 s loop    slow sway travelling up the column, head looks around a little
  Walk     1.125 s loop  stronger side-to-side S wave travelling up, slight forward bob
  Attack   1.125 s       rear back leaning to one side, strike forward and down across to the other, recover
  Hit      1.125 s       recoil back and aside, head shake, recover
  Death    1.125 s       topple forward onto the water, then sink; Dead = sunk (below the water), foam gone
  Fidget   1.125 s       head turns left and right
Prints per clip the lowest joint above the water and the reach of the head."""
import bpy, json, math, os
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 24
D = json.load(open(os.path.join(HERE, 'work', 'rig.json')))
J0 = np.array(D['joints']); RAD = np.array(D['radius']); NAMES = D['names']; NSEG = len(NAMES)
L = np.linalg.norm(np.diff(J0, axis=0), axis=1)
rig = bpy.data.objects['Seas_Rig']
REST_DIR = [Vector(J0[i + 1] - J0[i]).normalized() for i in range(NSEG)]
FOAM = 'FoamRoot' if 'FoamRoot' in rig.pose.bones else None


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def frames(P):
    F = []
    t = Vector(P[1] - P[0]).normalized(); n = (Vector((1, 0, 0)) - Vector((1, 0, 0)).dot(t) * t).normalized()
    for i in range(NSEG):
        ti = Vector(P[i + 1] - P[i]).normalized()
        if i:
            q = t.rotation_difference(ti); n = q @ n; n = (n - n.dot(ti) * ti).normalized()
        t = ti; F.append(Matrix((t, n, t.cross(n))).transposed())
    return F


REST_F = frames(J0)
REST_M = {pb.name: pb.bone.matrix_local.copy() for pb in rig.pose.bones}


def profile(total, power=1.0):
    """Cumulative bend spread over the segments: the upper ones carry more (head excluded)."""
    n = NSEG - 1
    return np.array([total * ((i + 1) / n) ** power for i in range(n)] + [total])


def wave(amp, phase, wavelength=0.9, grow=1.0):
    """Travelling bend up the body: per-segment angle, growing toward the top."""
    s = np.cumsum(L) - L / 2; u = s / s[-1]
    return amp * np.sin(2 * math.pi * (s / wavelength) - phase) * u ** grow


def curve(pitch, side=None, yaw=None, head_pitch=0.0, head_yaw=0.0, sink=0.0):
    side = np.zeros(NSEG) if side is None else side
    yaw = np.zeros(NSEG) if yaw is None else yaw
    P = J0.copy()
    for i in range(NSEG):
        hp = head_pitch if i == NSEG - 1 else 0.0; hy = head_yaw if i == NSEG - 1 else 0.0
        d = Matrix.Rotation(yaw[i] + hy, 3, 'Z') @ Matrix.Rotation(side[i], 3, 'Y') @ \
            Matrix.Rotation(pitch[i] + hp, 3, 'X') @ REST_DIR[i]
        nxt = P[i] + L[i] * np.array(d)
        floor = RAD[i + 1]
        if nxt[2] < floor:                                    # floor rule on the water surface
            h = np.array([d[0], d[1], 0.0]); hn = np.linalg.norm(h)
            h = h / hn if hn > 1e-6 else np.array([0, -1.0, 0])
            dz = floor - P[i][2]
            nxt = P[i] + h * math.sqrt(max(L[i] ** 2 - dz * dz, 1e-6)) + np.array([0, 0, dz])
        P[i + 1] = nxt
    P[:, 2] -= sink
    return P


def apply(P, foam_spin=0.0, foam_scale=1.0):
    F = frames(P)
    pose = {}
    for i, nm in enumerate(NAMES):
        m = (F[i] @ REST_F[i].transposed() @ REST_M[nm].to_3x3()).to_4x4(); m.translation = Vector(P[i]); pose[nm] = m
    if FOAM:
        m = (Matrix.Rotation(foam_spin, 3, 'Z') @ REST_M[FOAM].to_3x3()).to_4x4() @ Matrix.Scale(foam_scale, 4)
        m.translation = REST_M[FOAM].translation; pose[FOAM] = m
    for pb in rig.pose.bones:
        rest = REST_M[pb.name]
        if pb.parent is None:
            pb.matrix_basis = rest.inverted() @ pose[pb.name]
        else:
            prest = REST_M[pb.parent.name]
            pb.matrix_basis = (prest.inverted() @ rest).inverted() @ pose[pb.parent.name].inverted() @ pose[pb.name]


def foam(t):
    return dict(foam_spin=0.35 * t, foam_scale=1.0 + 0.06 * math.sin(2 * math.pi * t / 0.75))


def standing(t):
    ph = 2 * math.pi * t / 3.0
    return dict(pitch=profile(0.04 * math.sin(2 * ph)), side=wave(0.09, ph, 1.6), yaw=profile(0.18 * math.sin(ph), 1.5),
                head_yaw=-0.15 * math.sin(ph), **foam(t))


def walk(t):
    ph = 2 * math.pi * t / 1.125
    return dict(pitch=profile(0.10 + 0.05 * math.sin(2 * ph)), side=wave(0.24, ph, 1.1), yaw=profile(0.15 * math.sin(ph), 1.4),
                head_yaw=-0.2 * math.sin(ph), **foam(t))


def attack(t):
    # Windup coils back and leans/turns toward +X; the strike sweeps forward across to -X (user review 2026-10-14:
    # not a symmetric smash in one vertical plane). The head turns a little against the coil to keep its aim.
    back = ss(t / 0.35) * (1 - ss((t - 0.35) / 0.15))
    strike = ss((t - 0.35) / 0.15) * (1 - ss((t - 0.65) / 0.45))
    return dict(pitch=profile(-0.35 * back + 0.75 * strike, 1.4), head_pitch=-0.3 * back + 0.25 * strike,
                side=profile(0.28 * back - 0.22 * strike, 1.3), yaw=profile(0.35 * back - 0.3 * strike, 1.4),
                head_yaw=-0.2 * back + 0.1 * strike, **foam(t))


def hit(t):
    r = ss(t / 0.12) * (1 - ss((t - 0.35) / 0.7))
    return dict(pitch=profile(-0.4 * r, 1.2), side=profile(0.25 * r, 1.3),
                head_yaw=0.35 * math.sin(2 * math.pi * t / 0.3) * r, **foam(t))


def death(t):
    fall = ss(t / 0.6)
    sink = ss((t - 0.55) / 0.55) * 1.2
    return dict(pitch=profile(1.45 * fall, 0.35), side=profile(0.3 * fall, 1.5), head_pitch=0.4 * fall,
                sink=sink, foam_spin=0.35 * t, foam_scale=max(0.001, 1.0 - ss((t - 0.6) / 0.5)))


def fidget(t):
    turn = math.sin(2 * math.pi * t / 1.125) * ss(t / 0.15) * (1 - ss((t - 0.9) / 0.22))
    return dict(pitch=profile(0.02), head_yaw=0.55 * turn, yaw=profile(0.15 * turn, 1.5), **foam(t))


def capture():
    return {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    n = int(round(seconds * FPS)); poses = []; lowest = 9.0; reach = 0.0
    for f in range(n + 1):
        args = fn(((f % n) if loop else f) / FPS)
        P = curve(**{k: v for k, v in args.items() if k not in ('foam_spin', 'foam_scale')})
        apply(P, args.get('foam_spin', 0.0), args.get('foam_scale', 1.0))
        bpy.context.view_layer.update(); poses.append(capture())
        if args.get('sink', 0.0) == 0.0:
            lowest = min(lowest, float((P[1:, 2] - RAD[1:]).min()))     # the root sits at the waterline
        reach = max(reach, float(-P[-1][1]))
    act = bpy.data.actions.new(name); act.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = act
    prev = {}
    for f, pose in enumerate(poses):
        for k, (q, l, s) in pose.items():
            if k in prev and prev[k].dot(q) < 0:
                q = -q
            prev[k] = q
            pb = rig.pose.bones[k]; pb.rotation_quaternion = q; pb.location = l; pb.scale = s
            for path in ('rotation_quaternion', 'location', 'scale'):
                pb.keyframe_insert(path, frame=f)
    rig.animation_data.action = None
    print(f'CLIP {name} {seconds}s lowest joint above its radius {lowest * 100:.1f} cm, head reach {reach:.2f} m')


for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'


def main():
    clips = {'Standing': (3.0, True, standing), 'Walk': (1.125, True, walk), 'Attack': (1.125, False, attack),
             'Hit': (1.125, False, hit), 'Death': (1.125, False, death), 'Dead': (1.0, False, lambda t: death(1.125)),
             'Fidget': (1.125, False, fidget)}
    for name, (sec, loop, fn) in clips.items():
        key_action(name, sec, loop, fn)
    rig.animation_data.action = bpy.data.actions['Standing']
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
    print('SAVED')


if __name__ == '__main__':
    main()
