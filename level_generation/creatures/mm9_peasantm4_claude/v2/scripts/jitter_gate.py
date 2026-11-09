#!/usr/bin/env python3
"""Hand jitter gate (2026-10-30, user on Forad v3 Talk: "the hand is jiggling constantly" after a per-key arm
correction). At 48 fps, per clip and hand: the wrist's world-position second difference |p[i+1] - 2 p[i] + p[i-1]|
(mm per frame^2) and the hand's world angular velocity (deg per frame), for a corrected GLB and for the reference
(MM9's untouched clips, clips_mm9.py output). A clip fails when the corrected maximum exceeds the reference maximum
by more than RATIO x and ABS (both: a clip whose MM9 motion is already fast keeps its own headroom).
Shoulder chain (2026-10-30, user on Forad v3.1 Talk: "weird slight movement in the right shoulder" while the hand
held still): per frame the clavicle, upper-arm and forearm world angular velocity (deg/frame) and angular
acceleration (deg/frame^2), and the second difference of the shoulder skin (vertices weighted mostly to that side's
clavicle or upper arm, p95 over them, mm/frame^2). These are compared frame by frame: a clip fails where a value
exceeds MM9's at the same frame by more than --excess-ang, --excess-angacc or --excess-skin (a joint that moves
while MM9's is still).
Usage: jitter_gate.py <glb> <reference glb> <out json> --side L=<token> --side R=<token> [--ratio 1.5]
       [--abs-acc 2.0] [--abs-ang 2.0] [--excess-ang 1.0] [--excess-angacc 1.0] [--excess-skin 2.0] [--clips A,B]"""
import argparse, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

ap = argparse.ArgumentParser()
ap.add_argument('glb'); ap.add_argument('ref'); ap.add_argument('out')
ap.add_argument('--side', action='append', required=True)
ap.add_argument('--ratio', type=float, default=1.5)
ap.add_argument('--abs-acc', type=float, default=2.0, help='mm per frame^2 above the reference maximum')
ap.add_argument('--abs-ang', type=float, default=2.0, help='deg per frame above the reference maximum')
ap.add_argument('--clips', default='')
ap.add_argument('--excess-ang', type=float, default=1.0)
ap.add_argument('--excess-angacc', type=float, default=1.0)
ap.add_argument('--excess-skin', type=float, default=2.0)
ap.add_argument('--fps', type=float, default=48.0)
o = ap.parse_args()


def angvel(R):
    return np.array([np.degrees(np.arccos(np.clip((np.trace(a.T @ b) - 1) / 2, -1, 1)))
                     for a, b in zip(R[:-1], R[1:])]) if len(R) > 1 else np.zeros(1)


def angacc(R):
    """deg/frame^2: angle of the change of the per-frame relative rotation."""
    D = [b @ a.T for a, b in zip(R[:-1], R[1:])]
    return angvel(D) if len(D) > 1 else np.zeros(1)


def curves(path):
    m = Model(Glb(Path(path)))
    names = [n.get('name') for n in m.glb.json['nodes']]
    jn = [names[j] for j in m.joints]
    P = m.primitives
    USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
    dom = np.concatenate([np.array([jn[P[k]['joints'][v][np.argmax(P[k]['weights'][v])]]
                                    for v in range(len(P[k]['positions']))]) for k in USE])
    res = {}
    for clip in m.clips:
        if o.clips and clip not in o.clips.split(','):
            continue
        dur = max(m.clip_times(clip))
        ts = np.arange(0, dur + 1e-6, 1 / o.fps)
        W = [m.world(m.sample(clip, float(t))) for t in ts]
        X = None
        res[clip] = {}
        for s in o.side:
            key, tok = s.split('=', 1)
            find = lambda end: names.index(next(j for j in jn if tok in j and j.endswith(end)))
            h = find('Hand')
            p = np.array([w[h][:3, 3] for w in W])
            rot = lambda i: [w[i][:3, :3] / np.linalg.norm(w[i][:3, :3], axis=0) for w in W]
            R = rot(h)
            acc = np.linalg.norm(p[2:] - 2 * p[1:-1] + p[:-2], axis=1) * 1000 if len(p) > 2 else np.zeros(1)
            chain = {}
            for b in ('Clavicle', 'UpperArm', 'Forearm'):
                Rb = rot(find(b))
                chain[b] = (angvel(Rb), angacc(Rb))
            sv = np.where(np.isin(dom, [j for j in jn if tok in j and (j.endswith('Clavicle') or j.endswith('UpperArm'))]))[0]
            if X is None:
                X = np.array([np.concatenate([sp[0] for k, sp in enumerate(m.skinned_positions(w)) if k in USE])
                              for w in W])
            Y = X[:, sv]
            sk = np.percentile(np.linalg.norm(Y[2:] - 2 * Y[1:-1] + Y[:-2], axis=2), 95, axis=1) * 1000 \
                if len(Y) > 2 else np.zeros(1)
            res[clip][key] = (acc, angvel(R), chain, sk)
    return res


A, B = curves(o.glb), curves(o.ref)
rep, fails = {}, 0
for clip, sides in A.items():
    if clip not in B:
        continue
    rep[clip] = {}
    for key, (acc, ang, chain, sk) in sides.items():
        racc, rang, rchain, rsk = B[clip][key]
        fa = acc.max() > max(o.ratio * racc.max(), racc.max() + o.abs_acc)
        fw = ang.max() > max(o.ratio * rang.max(), rang.max() + o.abs_ang)
        e = {'acc_max_mm': round(float(acc.max()), 2), 'acc_ref_mm': round(float(racc.max()), 2),
             'acc_frame': int(np.argmax(acc)) + 1, 'ang_max_deg': round(float(ang.max()), 2),
             'ang_ref_deg': round(float(rang.max()), 2), 'ang_frame': int(np.argmax(ang))}
        fc = False
        for b, (av, aa) in chain.items():
            rav, raa = rchain[b]
            xv, xa = av - rav, aa - raa
            e[b] = {'angvel_excess': round(float(xv.max()), 2), 'angvel_excess_frame': int(np.argmax(xv)),
                    'angacc_excess': round(float(xa.max()), 2), 'angacc_excess_frame': int(np.argmax(xa)) + 1}
            fc |= bool(xv.max() > o.excess_ang or xa.max() > o.excess_angacc)
        xs = sk - rsk
        e['shoulder_skin'] = {'acc_excess_mm': round(float(xs.max()), 2), 'frame': int(np.argmax(xs)) + 1,
                              'acc_max_mm': round(float(sk.max()), 2), 'acc_ref_mm': round(float(rsk.max()), 2)}
        fc |= bool(xs.max() > o.excess_skin)
        e['fail'] = bool(fa or fw or fc)
        fails += e['fail']
        rep[clip][key] = e
    print(f'{clip:12s} ' + ' | '.join(
        f"{k}: hand acc {v['acc_max_mm']} (MM9 {v['acc_ref_mm']}) ang {v['ang_max_deg']} (MM9 {v['ang_ref_deg']}); "
        f"excess over MM9 per frame: upper arm {v['UpperArm']['angvel_excess']} deg/f "
        f"{v['UpperArm']['angacc_excess']} deg/f2, forearm {v['Forearm']['angvel_excess']} deg/f, "
        f"shoulder skin {v['shoulder_skin']['acc_excess_mm']} mm/f2{' FAIL' if v['fail'] else ''}"
        for k, v in rep[clip].items()))
json.dump(rep, open(o.out, 'w'), indent=1)
print('JITTER fails', fails)
