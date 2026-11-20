"""Procedural cobra clips (24 fps) on work/rig_v1.blend -> work/anim_v1.blend.

Every frame defines the centreline directly and fits the bones to it:
  - tail branch (root -> tail tip) lies on the ground: each joint at the height of its body radius, heading turned by
    a curvature profile kappa(v) (coil, travelling wave),
  - neck branch (root -> head): each segment's rest direction pitched forward (+) / back (-) about X and yawed about Z,
  - floor rule: a neck joint never goes below its body radius (the direction is flattened instead),
  - bone frames: parallel-transported up the neck; on the tail the side axis is locked to world up (belly down) -
    transport from the upright root rolled the coiled tail onto its side. Rest and pose use the same rule, so the fit
    adds no twist; bones are disconnected, so translation follows the curve exactly with no stretching.
Native timings (manifest): walk/attack/death/fidget 0.75 s, hit 0.9375 s.
  Standing 3.0 s loop  raised hood, tail coiled round the base, slow sway (the native stand)
  Walk     0.75 s loop serpentine wave travelling down the body, neck a little lower, counter-sway
  Attack   0.75 s      rear back, strike forward and down, recover
  Hit      0.9375 s    recoil back and aside, head shake, recover
  Death    0.75 s      neck topples forward onto the ground, tail uncoils; Dead = last pose held 1 s
  Fidget   0.75 s      quick head turn left/right and tilt
Prints each clip's self-contact margin (closest non-neighbour joints minus their radii) and lowest joint height."""
import bpy, json, math, os
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 24
D = json.load(open(os.path.join(HERE, 'work', 'rig.json')))
J0 = np.array(D['joints']); RAD = np.array(D['radius']); K = D['root']; NAMES = D['names']; NSEG = len(NAMES)
L = np.linalg.norm(np.diff(J0, axis=0), axis=1)
rig = bpy.data.objects['Cobra_Rig']; sc = bpy.context.scene
NECK = list(range(K, NSEG))               # segments from the root up to the head (head = NSEG-1)
TAIL = list(range(K - 1, -1, -1))         # segments from the root outward to the tail tip
REST_DIR = {i: Vector(J0[i] - J0[i + 1]).normalized() if i < K else Vector(J0[i + 1] - J0[i]).normalized()
            for i in range(NSEG)}
TAIL_LEN = float(L[:K].sum())


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def frames(P):
    """Parallel-transported (t, n, b) per segment, outward from the root."""
    def seg_dir(i):
        v = Vector(P[i] - P[i + 1]) if i < K else Vector(P[i + 1] - P[i]); return v.normalized()
    F = {}
    t = seg_dir(K); n = (Vector((1, 0, 0)) - Vector((1, 0, 0)).dot(t) * t).normalized()
    F[K] = (t, n)
    pt, pn = F[K]
    for i in NECK[1:]:                    # neck: parallel transport up the raised part
        ti = seg_dir(i)
        q = pt.rotation_difference(ti)
        ni = q @ pn; ni = (ni - ni.dot(ti) * ti).normalized()
        F[i] = (ti, ni); pt, pn = ti, ni
    for i in TAIL:                        # tail: side axis locked to world up, so the belly stays on the ground
        ti = seg_dir(i)
        side = Vector((0, 0, 1)).cross(ti)
        F[i] = (ti, side.normalized() if side.length > 1e-6 else Vector((1, 0, 0)))
    return {i: Matrix((t, n, t.cross(n))).transposed() for i, (t, n) in F.items()}


REST_F = frames(J0)
REST_M = {pb.name: pb.bone.matrix_local.copy() for pb in rig.pose.bones}


def curve(neck_pitch, neck_yaw, head_pitch=0.0, head_yaw=0.0, kappa=None, tail_heading=0.0, root_offset=(0, 0, 0),
          neck_dirs=None):
    """Joint positions. neck_pitch/neck_yaw: per neck segment (radians, cumulative profiles chosen by the caller);
    kappa: per tail segment curvature (1/m), outward; tail_heading: heading of the first tail segment (0 = +Y)."""
    P = J0.copy()
    P[K] = J0[K] + np.array(root_offset)
    for idx, i in enumerate(NECK):
        if neck_dirs is not None:
            d = neck_dirs[idx]
        else:
            pitch = neck_pitch[idx] + (head_pitch if i == NSEG - 1 else 0.0)
            yaw = neck_yaw[idx] + (head_yaw if i == NSEG - 1 else 0.0)
            d = Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(pitch, 3, 'X') @ REST_DIR[i]
        nxt = np.array(P[i]) + L[i] * np.array(d)
        floor = RAD[i + 1] if i + 1 < len(RAD) else 0.03
        if nxt[2] < floor:                                    # floor rule: flatten, keep the horizontal heading
            h = np.array([d[0], d[1], 0.0]); hn = np.linalg.norm(h)
            h = h / hn if hn > 1e-6 else np.array([0, -1.0, 0])
            dz = floor - P[i][2]
            nxt = np.array(P[i]) + h * math.sqrt(max(L[i] ** 2 - dz * dz, 1e-6)) + np.array([0, 0, dz])
        P[i + 1] = nxt
    heading = tail_heading
    for m, i in enumerate(TAIL):                              # segment i runs from joint i+1 to joint i
        if kappa is not None:
            heading += kappa[m] * L[i]
        z0, z1 = P[i + 1][2], max(RAD[i], 0.004)
        dz = z1 - z0
        hl = math.sqrt(max(L[i] ** 2 - dz * dz, 1e-6))
        P[i] = P[i + 1] + np.array([math.sin(heading) * hl, math.cos(heading) * hl, dz])
    return P


def apply(P):
    F = frames(P)
    pose = {}
    for pb in rig.pose.bones:
        i = NAMES.index(pb.name)
        rot = F[i] @ REST_F[i].transposed()
        head = P[i + 1] if i < K else P[i]
        m = (rot @ REST_M[pb.name].to_3x3()).to_4x4(); m.translation = Vector(head)
        pose[pb.name] = m
    for pb in rig.pose.bones:
        rest = REST_M[pb.name]
        if pb.parent is None:
            basis = rest.inverted() @ pose[pb.name]
        else:
            prest = REST_M[pb.parent.name]
            basis = (prest.inverted() @ rest).inverted() @ pose[pb.parent.name].inverted() @ pose[pb.name]
        pb.matrix_basis = basis


def profile(total, power=1.0):
    """Cumulative bend spread over the neck: the upper segments carry more."""
    nn = len(NECK) - 1
    return [total * ((idx + 1) / nn) ** power if idx < nn else total for idx in range(len(NECK))]


def coil(t=0.0, amount=1.0):
    """Tail coiled tightly round the base like the native stand: an inward spiral whose radius shrinks by about one
    body width per turn (curvature = 1/radius), so the turns lie side by side without crossing."""
    v = np.cumsum(L[K - 1::-1]) / TAIL_LEN
    r = np.clip(0.40 - 0.21 * v, 0.12, None) * (1.0 + 0.03 * math.sin(2 * math.pi * t / 3.0))
    return amount / r


def standing(t, base=False):
    sway = 0.10 * math.sin(2 * math.pi * t / 3.0)
    breathe = 0.03 * math.sin(2 * math.pi * t / 1.5)
    return dict(neck_pitch=profile(breathe), neck_yaw=profile(sway, 1.5), head_yaw=-0.5 * sway,
                kappa=coil(t), tail_heading=0.45)


def walk(t):
    T = 0.75; lam = 1.05; A = 3.4
    nT = len(TAIL); v = np.cumsum(L[K - 1::-1]) - L[K - 1] / 2
    k = A * np.sin(2 * math.pi * (v / lam + t / T)) * np.clip(v / 0.35, 0, 1)
    # keep the body trailing straight behind on average: cancel the mean heading
    head = np.cumsum(k * L[K - 1::-1]); h0 = -float(np.mean(head))
    sway = 0.12 * math.sin(2 * math.pi * t / T + math.pi)
    return dict(neck_pitch=profile(0.30), neck_yaw=profile(sway, 1.5), head_pitch=-0.25, head_yaw=-0.6 * sway,
                kappa=k, tail_heading=h0)


def attack(t):
    s = standing(0.0)
    back = ss(t / 0.25) * (1 - ss((t - 0.25) / 0.12))
    strike = ss((t - 0.25) / 0.13) * (1 - ss((t - 0.45) / 0.28))
    s['neck_pitch'] = profile(-0.30 * back + 0.75 * strike, 1.3)
    s['head_pitch'] = -0.25 * back + 0.35 * strike
    s['root_offset'] = (0, -0.10 * strike, 0)
    return s


def hit(t):
    s = standing(0.0)
    r = ss(t / 0.12) * (1 - ss((t - 0.3) / 0.55))
    shake = math.sin(2 * math.pi * t / 0.25) * r
    s['neck_pitch'] = profile(-0.45 * r, 1.2)
    s['neck_yaw'] = profile(0.30 * r, 1.4)
    s['head_pitch'] = -0.3 * r; s['head_yaw'] = 0.35 * shake
    s['kappa'] = coil(0.0) * (1.0 + 0.15 * r)
    return s


DEATH_END = None


def death(t):
    s = standing(0.0)
    rest = [Matrix.Rotation(y, 3, 'Z') @ Matrix.Rotation(p + (s['head_pitch'] if False else 0.0), 3, 'X') @ REST_DIR[i]
            for p, y, i in zip(s['neck_pitch'], s['neck_yaw'], NECK)]
    dirs = []
    for idx, i in enumerate(NECK):
        # topple: lower segments go first, each ending flat on the ground heading forward with a slight S
        lag = 0.08 * (len(NECK) - 1 - idx) / max(len(NECK) - 1, 1)
        f = ss((t - 0.05 - lag) / 0.45)
        yaw = 0.35 * math.sin(idx * 0.9)
        flat = Vector((math.sin(yaw), -math.cos(yaw), -0.02)).normalized()
        dirs.append(rest[idx].lerp(flat, f).normalized())
    s['neck_dirs'] = dirs
    s['kappa'] = coil(0.0) * (1.0 - 0.6 * ss((t - 0.2) / 0.5))
    return s


def capture():
    return {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones}


def key_action(name, seconds, loop, fn):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    n = int(round(seconds * FPS)); poses = []; margin = 9.0; lowest = 9.0
    for f in range(n + 1):
        P = curve(**fn(((f % n) if loop else f) / FPS))
        apply(P); bpy.context.view_layer.update(); poses.append(capture())
        for a in range(len(P)):
            for b in range(a + 4, len(P)):
                margin = min(margin, float(np.linalg.norm(P[a] - P[b]) - RAD[a] - RAD[b]))
        lowest = min(lowest, float((P[:, 2] - RAD).min()))
    act = bpy.data.actions.new(name); act.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = act
    prev = {}
    for f, pose in enumerate(poses):
        for k, (q, l) in pose.items():
            if k in prev and prev[k].dot(q) < 0:
                q = -q
            prev[k] = q
            pb = rig.pose.bones[k]; pb.rotation_quaternion = q; pb.location = l
            pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
    rig.animation_data.action = None
    print(f'CLIP {name} {seconds}s self-contact margin {margin * 100:.1f} cm lowest joint vs radius {lowest * 100:.1f} cm')


for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'


def main():
    CLIPS = {'Standing': (3.0, True, standing), 'Walk': (0.75, True, walk), 'Attack': (0.75, False, attack),
             'Hit': (0.9375, False, hit), 'Death': (0.75, False, death), 'Dead': (1.0, False, lambda t: death(0.75)),
             'Fidget': (0.75, False, lambda t: dict(standing(0.0), head_yaw=0.6 * math.sin(2 * math.pi * t / 0.75)
                                                    * ss(t / 0.1) * (1 - ss((t - 0.6) / 0.15)),
                                                    head_pitch=-0.15 * math.sin(math.pi * t / 0.75)))}
    for name, (sec, loop, fn) in CLIPS.items():
        key_action(name, sec, loop, fn)
    rig.animation_data.action = bpy.data.actions['Standing']
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
    print('SAVED')


if __name__ == '__main__':
    main()
