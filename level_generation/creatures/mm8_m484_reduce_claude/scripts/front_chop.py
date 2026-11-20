#!/usr/bin/env python3
"""Minotaur Attack (and the Cast alias, which shares its samplers) re-aimed through the space in front of the body
centre, user review 2026-10-19: "make the attack anim slash like in front of him ... and dont look to the side".
The fitted overhead chop (mm8_m484_claude: local 2HandAxeAttack1, both hands on the handle, gated grips and contacts)
is kept; three things change, only in output values at the existing 60 Hz key times (length 1.6667 s and the
actors.yml impact 0.816667 s unchanged; pelvis and legs are not animated in this clip and stay planted):
- Re-aim: a spine twist about the vertical (spine 30 / 35 / 35 %) that grows through the cut: a little to his left in
  the chamber, then to his right through the impact and the follow-through. The old chop came down left of centre
  (impact head 14 cm left, follow-through at his left knee); the twisted cut crosses the centre line at the impact
  and ends in front of his right knee, a diagonal across the front.
- Head forward: neck and head keep the idle head's world orientation (the old chop turned and tilted the head
  sideways), with a small nod into the impact; neck and head share the correction.
- Jolts: the old Axe joint turned in the hand at a constant 225 deg/s and stopped dead at 0.60 s, and the downswing
  started from rest within one key (right forearm 0 -> 1,874 deg/s). Every upper-body channel (arms, hands, fingers,
  axe, clavicles) is low-passed over 0-0.95 s (Gaussian sigma SIGMA s, tapered at the window ends), the same
  filter on every channel. Filtering moves the left hand against the handle (up to 5 cm), so the left arm is then
  solved again (two-bone IK, the elbow kept on the side of the filtered elbow) to put the left hand exactly where the
  old clip had it relative to the axe at the same time, sliding included.
Usage: front_chop.py <in.glb> <out.glb>"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import CubicSpline

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gltf_pose import Pose, qmul, qinv, qrot, qaxis, qbetween, qslerp  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import write_glb, append_accessor  # noqa: E402

END, IMPACT = 1.6666666, 0.8166667
X, Y, I4 = np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 0, 1.0])
# spine twist (deg, + turns him to his left) and nod (deg down) keys; clamped spline, zero at both ends
TWIST = [(0.0, 0, 0), (0.55, 6, -2), (IMPACT, -12, 6), (1.0, -24, 8), (1.25, -12, 3), (END, 0, 0)]
SPINE = (('B_Spine', 0.30), ('B_Spine1', 0.35), ('B_Spine2', 0.35))
WINDOW, SIGMA, TAPER = (0.0, 0.95), 0.045, 0.10


def smoother(u):
    u = np.clip(u, 0, 1)
    return u * u * u * (u * (u * 6 - 15) + 10)


def low_pass(times, vals, rotation):
    """Gaussian low-pass of one channel inside WINDOW, blended in and out over TAPER"""
    v = vals.astype(float).copy()
    if rotation:
        for k in range(1, len(v)):
            if np.dot(v[k], v[k - 1]) < 0:
                v[k] = -v[k]
    dt = float(np.median(np.diff(times))); r = int(4 * SIGMA / dt); g = np.exp(-0.5 * (np.arange(-r, r + 1) * dt / SIGMA) ** 2)
    g /= g.sum(); pad = np.concatenate([np.repeat(v[:1], r, 0), v, np.repeat(v[-1:], r, 0)])
    sm = np.stack([np.convolve(pad[:, c], g, 'valid') for c in range(v.shape[1])], 1)
    if rotation:
        sm /= np.linalg.norm(sm, axis=1, keepdims=True)
    w = smoother(np.minimum((times - WINDOW[0]) / TAPER, (WINDOW[1] - times) / TAPER))[:, None]
    out = v * (1 - w) + sm * w
    if rotation:
        out /= np.linalg.norm(out, axis=1, keepdims=True)
    return out


def main(src, dst):
    p = Pose(src); doc = p.doc; binary = bytearray(p.bin); i = p.idx
    clip = p.clip('Attack'); base = p.local(clip, 0.0); P0, Q0 = p.world(base)
    an = next(a for a in doc['animations'] if a['name'] == 'Attack')
    chans = {(ch['target']['node'], ch['target']['path']): an['samplers'][ch['sampler']] for ch in an['channels']}
    times = clip[i['B_R_Hand']]['rotation'][0].astype(float); assert abs(times[-1] - END) < 1e-3
    tw = np.array(TWIST, float); stw = CubicSpline(tw[:, 0], tw[:, 1:], bc_type='clamped')
    # 1. low-pass every animated upper-body rotation channel (not spine / neck / head, which are rebuilt below)
    upper = [n for n in p.names if n and (n.startswith(('B_L_', 'B_R_')) and not n.endswith(('Thigh', 'Calf', 'Foot', 'Toe0'))
                                         or n == 'Axe')]
    new = {}
    for n in upper:
        tv = clip.get(i[n], {}).get('rotation')
        if tv is None or len(tv[0]) != len(times) or np.ptp(tv[1], axis=0).max() < 1e-6:
            continue
        new[n] = low_pass(times, tv[1], True)
    # 2. spine twist and forward head per key, on top of the (smoothed) old pose
    rebuilt = ['B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head']
    for n in rebuilt:
        new[n] = np.zeros((len(times), 4))
    short = 0.0
    for k, t in enumerate(times):
        L = p.local(clip, t)
        for n in upper:
            if n in new:
                L[i[n]][1] = new[n][k]
        yaw, nod = np.radians(stw(t))
        for name, frac in SPINE:
            j = i[name]; Pw, Qw = p.world(L)
            L[j][1] = qmul(qinv(Qw[p.parent[j]]), qmul(qaxis(Y, yaw * frac), Qw[j]))
        Pw, Qw = p.world(L)
        qh = qmul(qaxis(X, nod), Q0[i['B_Head']]); jn, jh = i['B_Neck'], i['B_Head']
        half = qslerp(I4, qmul(qh, qinv(Qw[jh])), 0.5)
        L[jn][1] = qmul(qinv(Qw[p.parent[jn]]), qmul(half, Qw[jn]))
        Pw, Qw = p.world(L); L[jh][1] = qmul(qinv(Qw[jn]), qh)
        # left hand back onto its old place on the handle
        Lo = p.local(clip, t); Po, Qo = p.world(Lo)
        rel_p = qrot(qinv(Qo[i['Axe']]), Po[i['B_L_Hand']] - Po[i['Axe']]); rel_q = qmul(qinv(Qo[i['Axe']]), Qo[i['B_L_Hand']])
        Pw, Qw = p.world(L); W = Pw[i['Axe']] + qrot(Qw[i['Axe']], rel_p); qw = qmul(Qw[i['Axe']], rel_q)
        ju, jf, jw = i['B_L_UpperArm'], i['B_L_Forearm'], i['B_L_Hand']
        S = Pw[ju]; a = np.linalg.norm(base[jf][0]); b = np.linalg.norm(base[jw][0])
        dist = np.linalg.norm(W - S); dd = (W - S) / dist; short = max(short, dist - (a + b)); dist = min(dist, a + b - 1e-4)
        e = Pw[jf] - S; perp = e - dd * np.dot(e, dd); perp /= np.linalg.norm(perp)
        ca = np.clip((a * a + dist * dist - b * b) / (2 * a * dist), -1, 1)
        E = S + a * (ca * dd + np.sqrt(1 - ca * ca) * perp)
        qu = qmul(qbetween(qrot(Qw[ju], Y), E - S), Qw[ju]); L[ju][1] = qmul(qinv(Qw[p.parent[ju]]), qu)
        Pw, Qw = p.world(L)
        qf = qmul(qbetween(qrot(Qw[jf], Y), S + dd * dist - Pw[jf]), Qw[jf]); L[jf][1] = qmul(qinv(Qw[p.parent[jf]]), qf)
        L[jw][1] = qmul(qinv(qf), qw)
        for n in ('B_L_UpperArm', 'B_L_Forearm', 'B_L_Hand'):
            new[n][k] = L[i[n]][1]
        for n in rebuilt:
            q = np.asarray(L[i[n]][1], float)
            if k and np.dot(new[n][k - 1], q) < 0:
                q = -q
            new[n][k] = q
    shared = {s['output'] for a in doc['animations'] if a['name'] not in ('Attack', 'Cast') for s in a['samplers']}
    written = 0
    for n, data in new.items():
        s = chans[(i[n], 'rotation')]; old = s['output']; acc = doc['accessors'][old]
        assert acc['count'] == len(times), n
        data = data.astype(np.float32)
        if old in shared:
            nid = append_accessor(doc, binary, acc, data.tobytes())
            for a in doc['animations']:
                if a['name'] in ('Attack', 'Cast'):
                    for s2 in a['samplers']:
                        if s2['output'] == old:
                            s2['output'] = nid
        else:
            v = doc['bufferViews'][acc['bufferView']]; off = v.get('byteOffset', 0) + acc.get('byteOffset', 0)
            binary[off:off + data.nbytes] = data.tobytes()
        written += 1
    write_glb(Path(dst), doc, bytes(binary))
    print('FRONT_CHOP', dst, json.dumps({'channels': written, 'smoothed': len(new) - len(rebuilt),
                                         'left_reach_short_mm': round(short * 1000, 1)}))


if __name__ == '__main__':
    main(*sys.argv[1:3])
