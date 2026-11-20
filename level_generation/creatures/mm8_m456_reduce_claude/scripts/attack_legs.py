#!/usr/bin/env python3
"""Attack v2 for the Dragon Hunter: the legs and hips take part in the sword cut (user review: "dragon hunter attack
anim - use legs also").

The production Attack (SwordAttackL2 on a planted stance, 0.8 s, impact 0.385417 s) animates only the spine, neck and
arms; pelvis, thighs, calves and feet are two constant keys. Here, per 120 Hz key of the existing clip:

- the pelvis follows PELVIS (offset in metres and yaw about the vertical, degrees): weight back and down onto the rear
  (right) foot with the hips turned into the wind-up, then a drive forward and down through the cut with the hips
  turning through it, deepest just after the impact, and a recovery to the guard;
- the lead (left) foot steps out (lift, travel, plant before the impact), stays planted through the cut and steps back
  to its place; the rear foot stays planted; both feet keep their planted orientation, so planted feet do not slide;
- thighs and calves are solved by two-bone IK in the leg's own bending plane (knee pole from the guard pose, turned
  with KNEE_FOLLOW of the hip yaw); bone lengths are those of the rig;
- B_Spine keeps its world rotation from the source clip, so chest, arms and sword turn exactly as authored and only
  move with the pelvis offset (hips counter-rotate under the chest).

Offsets are zero at both ends, with zero velocity, so the clip still starts and ends on the Standing pose. Duration
and impact time are unchanged. Usage: attack_legs.py <in.glb> <out.glb>"""
import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import CubicHermiteSpline, PchipInterpolator
from scipy.spatial.transform import Rotation as R

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

# time: (dx, dy, dz, yaw); +z is forward, +x the character's left, yaw > 0 turns the hips to the left
PELVIS = [(0.00, 0, 0, 0, 0), (0.18, -0.02, -0.025, -0.05, -14), (0.26, -0.01, -0.03, -0.01, -10),
          (0.34, 0.02, -0.07, 0.12, 6), (0.40, 0.03, -0.085, 0.16, 14), (0.50, 0.025, -0.075, 0.14, 16),
          (0.62, 0.01, -0.04, 0.06, 8), (0.72, 0.0, -0.012, 0.01, 2), (0.80, 0, 0, 0, 0)]
STEP_OUT, STEP_BACK = (0.20, 0.34), (0.52, 0.70)    # lead-foot swing phases (s)
LEAD = np.array([0.02, 0.0, 0.24])                   # planted lunge offset of the lead ankle (m)
LIFT = 0.06                                          # swing height (m)
KNEE_FOLLOW = 0.6
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src); binary = bytearray(binary)
N = doc['nodes']; idx = {n.get('name'): i for i, n in enumerate(N)}
NC = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}


def read(i):
    a = doc['accessors'][i]
    return np.frombuffer(accessor_bytes(doc, binary, i), np.float32).reshape(a['count'], NC[a['type']]).astype(np.float64)


anim = next(a for a in doc['animations'] if a['name'] == 'Attack')
chan = {(N[c['target']['node']]['name'], c['target']['path']): c for c in anim['channels']}
spine = anim['samplers'][chan[('B_Spine', 'rotation')]['sampler']]
times_acc = spine['input']; T = read(times_acc)[:, 0]


def value(name, path):
    """constant channels (2 keys) -> their first value; the legs and pelvis are constant in the source"""
    s = anim['samplers'][chan[(name, path)]['sampler']]; v = read(s['output'])
    assert np.allclose(v, v[0], atol=1e-6), (name, path, 'not constant')
    return v[0]


def local(name):
    return R.from_quat(value(name, 'rotation')), value(name, 'translation')


def hermite(keys):
    k = np.array(keys, float); t = k[:, 0]; out = []
    for c in range(1, k.shape[1]):
        d = PchipInterpolator(t, k[:, c]).derivative()(t); d[0] = d[-1] = 0
        out.append(CubicHermiteSpline(t, k[:, c], d)(T))
    return np.stack(out, 1)


def smooth(s):
    s = np.clip(s, 0, 1); return s * s * (3 - 2 * s)


# guard pose (constant in the source)
Rp0, tp0 = local('B_Pelvis')
assert 'Rig' not in N[idx['B_Pelvis']] and not any(k in N[idx['Rig']] for k in ('translation', 'rotation', 'scale'))
legs = {}
for s in 'LR':
    Rt, tt = local(f'B_{s}_Thigh'); Rc, tc = local(f'B_{s}_Calf'); Rf, tf = local(f'B_{s}_Foot')
    Wt = Rp0 * Rt; Wc = Wt * Rc; Wf = Wc * Rf
    hip = tp0 + Rp0.apply(tt); knee = hip + Wt.apply(tc); ankle = knee + Wc.apply(tf)
    u = (ankle - hip) / np.linalg.norm(ankle - hip); pole = (knee - hip) - ((knee - hip) @ u) * u
    legs[s] = dict(tt=tt, a=np.linalg.norm(tc), b=np.linalg.norm(tf), tc=tc, tf=tf, Wt=Wt, Wc=Wc, Wf=Wf,
                   ankle=ankle, pole=pole / np.linalg.norm(pole), d1=Wt.apply(tc), d2=Wc.apply(tf))

P = hermite(PELVIS); off, yaw = P[:, :3], np.radians(P[:, 3])
lead = np.zeros((len(T), 3))
for (t0, t1), (a, b) in ((STEP_OUT, (np.zeros(3), LEAD)), (STEP_BACK, (LEAD, np.zeros(3)))):
    s = (T - t0) / (t1 - t0); m = (s >= 0) & (s <= 1)
    lead[m] = a + smooth(s[m])[:, None] * (b - a); lead[m, 1] += LIFT * np.sin(np.pi * s[m])
lead[(T > STEP_OUT[1]) & (T < STEP_BACK[0])] = LEAD


def frame(d, n):
    d = d / np.linalg.norm(d); n = n - (n @ d) * d; n /= np.linalg.norm(n)
    return np.stack([d, n, np.cross(d, n)], 1)


out = {k: [] for k in ['pt', 'pr', 'sp'] + [f'{s}{j}' for s in 'LR' for j in 'tcf']}
Rs_src = read(spine['output']); miss = 0.0; reach = 0.0
for k in range(len(T)):
    Ry = R.from_rotvec([0, yaw[k], 0]); Rp = Ry * Rp0; tp = tp0 + off[k]
    out['pt'].append(tp); out['pr'].append(Rp.as_quat())
    out['sp'].append((Rp.inv() * Rp0 * R.from_quat(Rs_src[k])).as_quat())   # chest keeps its world rotation
    for s in 'LR':
        g = legs[s]; hip = tp + Rp.apply(g['tt'])
        target = g['ankle'] + (lead[k] if s == 'L' else 0)
        D = target - hip; dist = np.linalg.norm(D); L = g['a'] + g['b']
        reach = max(reach, dist / L); dist_c = min(dist, 0.999 * L); u = D / dist
        pole = R.from_rotvec([0, KNEE_FOLLOW * yaw[k], 0]).apply(g['pole']); p = pole - (pole @ u) * u; p /= np.linalg.norm(p)
        ca = np.clip((g['a'] ** 2 + dist_c ** 2 - g['b'] ** 2) / (2 * g['a'] * dist_c), -1, 1)
        knee = hip + g['a'] * (ca * u + np.sqrt(1 - ca * ca) * p); ank = hip + u * dist_c
        miss = max(miss, np.linalg.norm(ank - target))
        d1, d2 = knee - hip, ank - knee; n_new = np.cross(d1, d2); n_old = np.cross(g['d1'], g['d2'])
        Wt = R.from_matrix(frame(d1, n_new) @ frame(g['d1'], n_old).T) * g['Wt']
        Wc = R.from_matrix(frame(d2, n_new) @ frame(g['d2'], n_old).T) * g['Wc']
        out[f'{s}t'].append((Rp.inv() * Wt).as_quat()); out[f'{s}c'].append((Wt.inv() * Wc).as_quat())
        out[f'{s}f'].append((Wc.inv() * g['Wf']).as_quat())                # planted orientation kept
for key in out:
    arr = np.array(out[key])
    if arr.shape[1] == 4:
        for k in range(1, len(arr)):
            if arr[k] @ arr[k - 1] < 0:
                arr[k] = -arr[k]
    out[key] = arr


def put(name, path, values):
    c = chan[(name, path)]; old = anim['samplers'][c['sampler']]
    acc = dict(doc['accessors'][old['output']], count=len(values)); acc.pop('min', None); acc.pop('max', None)
    anim['samplers'].append({'input': times_acc, 'interpolation': 'LINEAR',
                             'output': append_accessor(doc, binary, acc, values.astype(np.float32).tobytes())})
    c['sampler'] = len(anim['samplers']) - 1


put('B_Pelvis', 'translation', out['pt']); put('B_Pelvis', 'rotation', out['pr']); put('B_Spine', 'rotation', out['sp'])
for s in 'LR':
    put(f'B_{s}_Thigh', 'rotation', out[f'{s}t']); put(f'B_{s}_Calf', 'rotation', out[f'{s}c'])
    put(f'B_{s}_Foot', 'rotation', out[f'{s}f'])
print(f'ATTACK legs: {len(T)} keys, max leg reach {reach:.3f} of full length, max ankle miss {miss * 1000:.2f} mm')
write_glb(dst, doc, bytes(binary))
