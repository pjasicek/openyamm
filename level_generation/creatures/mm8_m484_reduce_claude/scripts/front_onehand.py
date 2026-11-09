#!/usr/bin/env python3
"""The Minotaur's only attack: the original fitted one-handed attack (`AttackOneHand`, mm8_m484_claude
work/gated_master_onehand_v1.blend, local 1Hand MaceAttackR2) reworked after user review 2026-10-19 ("did you
adjust the 'original' 1H attack? that should be the one to use. you can delete the 2H one"; earlier: "slash like in
front of him ... and dont look to the side").

The source (0.867 s, 60 Hz keys) stands still for 0.07 s, swings the axe round behind his right side in 0.12 s
(head up to 34 m/s), sweeps it from behind-right to his right front in two keys (up to 76 m/s, ending 0.83 m right
of centre), stops dead and holds for 0.23 s, then recovers in 0.2 s with the free left arm whipping at up to
3,000 deg/s. Changes (60 Hz keys; length 0.867 -> 1.1 s, so the backswing and the recovery are no longer frantic):
- Retime: a monotone time warp (new -> source, PCHIP through WARP) with velocity-continuous (modified Akima)
  sampling of the source keys: no still start, a slower backswing, a slower strike and a shorter hold.
- Re-aim: a spine twist about the vertical (spine 30 / 35 / 35 %, TWIST keys) that coils to his right in the
  backswing and turns him to his left through the strike and after it, so the blade keeps travelling across the
  front: it crosses the centre line at belt height at full speed (the impact) and decelerates on his left.
- Head forward: neck and head keep Standing's head world orientation (the source turned it 29 deg), with a small nod
  into the cut; neck and head share the correction.
- Jolts: the upper body (spine, arms, hands, fingers, axe, clavicles) is low-passed over the whole clip (Gaussian SMOOTH,
  tapered to the ends so the first and last poses stay), which turns the source's dead stop into a short
  follow-through.
- Ends: the first pose is Standing frame 0 (the source's own); the kilt bones, which end up to 3.4 cm from Standing,
  are blended into Standing's values over the last BLEND_END s, so idle -> attack -> idle does not pop.
Legs and pelvis follow the source's own (retimed) planted stance. Usage: front_onehand.py <in.glb> <out.npz>
(writes the per-channel outputs; ship_onehand.py builds the GLB)."""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import Akima1DInterpolator, CubicSpline, PchipInterpolator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gltf_pose import Pose, qmul, qinv, qaxis, qslerp  # noqa: E402

SRC_CLIP, SRC_END, END = 'AttackOneHand', 0.8666667, 1.1
WARP = [(0.0, 0.0), (0.06, 0.075), (0.30, 0.20), (0.46, 0.30), (0.54, 0.37), (0.60, 0.415), (0.66, 0.433),
        (0.76, 0.445), (0.82, 0.62), (END, SRC_END)]
TWIST = [(0.0, 0, 0), (0.30, -8, 0), (0.50, -4, -2), (0.57, 10, 2), (0.62, 28, 5), (0.68, 40, 8), (0.76, 44, 8), (0.90, 24, 4), (END, 0, 0)]
SPINE = (('B_Spine', 0.30), ('B_Spine1', 0.35), ('B_Spine2', 0.35))
SMOOTH = (0.0, END, 0.04, 0.06)                # low-pass window start, end, Gaussian sigma, taper (s)
BLEND_END = 0.20
X, Y, I4 = np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 0, 1.0])


def smoother(u):
    u = np.clip(u, 0, 1)
    return u * u * u * (u * (u * 6 - 15) + 10)


def sample(times, vals, t, rotation):
    v = vals.astype(float).copy()
    if rotation:
        for k in range(1, len(v)):
            if np.dot(v[k], v[k - 1]) < 0:
                v[k] = -v[k]
    if len(times) < 3:
        out = np.array([v[0] + (v[-1] - v[0]) * np.clip((x - times[0]) / max(times[-1] - times[0], 1e-9), 0, 1)
                        for x in t])
    else:
        out = Akima1DInterpolator(times, v, axis=0, method='makima')(np.clip(t, times[0], times[-1]))
    if rotation:
        out /= np.linalg.norm(out, axis=1, keepdims=True)
    return out


def low_pass(times, v, rotation):
    t0, t1, sigma, taper = SMOOTH
    dt = float(np.median(np.diff(times))); r = int(4 * sigma / dt)
    g = np.exp(-0.5 * (np.arange(-r, r + 1) * dt / sigma) ** 2); g /= g.sum()
    pad = np.concatenate([np.repeat(v[:1], r, 0), v, np.repeat(v[-1:], r, 0)])
    sm = np.stack([np.convolve(pad[:, c], g, 'valid') for c in range(v.shape[1])], 1)
    w = smoother(np.minimum((times - t0) / taper, (t1 - times) / taper))[:, None]
    out = v * (1 - w) + sm * w
    if rotation:
        out /= np.linalg.norm(out, axis=1, keepdims=True)
    return out


def main(src, dst):
    p = Pose(src); i = p.idx
    clip = p.clip(SRC_CLIP); std = p.local(p.clip('Standing'), 0.0); _, Qs = p.world(std)
    assert abs(clip[i['B_R_Hand']]['rotation'][0][-1] - SRC_END) < 1e-3
    times = np.round(np.arange(0, END + 1e-6, 1 / 60), 6)
    warp = PchipInterpolator(*zip(*WARP)); st = warp(times)
    tw = np.array(TWIST, float); stw = CubicSpline(tw[:, 0], tw[:, 1:], bc_type='clamped')
    upper = {n for n in p.names if n and (n.startswith(('B_L_', 'B_R_')) and not n.endswith(('Thigh', 'Calf', 'Foot', 'Toe0'))
                                          or n in ('Axe', 'B_Spine', 'B_Spine1', 'B_Spine2'))}
    out = {}
    for node, chans in clip.items():
        for path, (tt, vv) in chans.items():
            rot = path == 'rotation'
            v = sample(tt.astype(float), vv, st, rot) if len(tt) > 1 else np.repeat(vv[:1].astype(float), len(times), 0)
            if p.names[node] in upper and len(tt) > 2 and rot:
                v = low_pass(times, v, rot)
            if p.names[node].startswith('Skirt_'):             # kilt bones settle into Standing's pose
                T, R, S = std[node]; target = {'translation': T, 'rotation': R, 'scale': S}[path]
                w = smoother((times - (END - BLEND_END)) / BLEND_END)
                for k in range(len(times)):
                    if w[k] > 0:
                        v[k] = qslerp(v[k], np.asarray(target, float), w[k]) if rot else v[k] * (1 - w[k]) + np.asarray(target) * w[k]
            out[(node, path)] = v
    # spine twist and the forward head
    def locals_at(k):
        L = [list(x) for x in p.local({}, 0.0)]
        for (node, path), v in out.items():
            L[node][{'translation': 0, 'rotation': 1, 'scale': 2}[path]] = v[k]
        return L
    for n in ('B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head'):
        assert (i[n], 'rotation') in out, n
    for k, t in enumerate(times):
        L = locals_at(k); yaw, nod = np.radians(stw(t))
        for name, frac in SPINE:
            j = i[name]; Pw, Qw = p.world(L)
            L[j][1] = qmul(qinv(Qw[p.parent[j]]), qmul(qaxis(Y, yaw * frac), Qw[j]))
        Pw, Qw = p.world(L)
        qh = qmul(qaxis(X, nod), Qs[i['B_Head']]); jn, jh = i['B_Neck'], i['B_Head']
        half = qslerp(I4, qmul(qh, qinv(Qw[jh])), 0.5)
        L[jn][1] = qmul(qinv(Qw[p.parent[jn]]), qmul(half, Qw[jn]))
        Pw, Qw = p.world(L); L[jh][1] = qmul(qinv(Qw[jn]), qh)
        for n in ('B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head'):
            q = np.asarray(L[i[n]][1], float)
            if k and np.dot(out[(i[n], 'rotation')][k - 1], q) < 0:
                q = -q
            out[(i[n], 'rotation')][k] = q
    np.savez(dst, times=times, **{f'{p.names[n]}|{path}': v for (n, path), v in out.items()})
    print('FRONT_ONEHAND', dst, json.dumps({'channels': len(out), 'keys': len(times)}))


if __name__ == '__main__':
    main(*sys.argv[1:3])
