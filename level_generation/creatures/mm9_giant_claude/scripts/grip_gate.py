#!/usr/bin/env python3
"""Grip gate after mm9_lichking_claude/scripts/grip_gate.py (third pass, 2026-11-01), every clip at 30 fps on the runtime GLB, per hand:
the finger joints (heads of each finger's 2nd and 3rd bones, the thumb's too) against the shaft's axis (Xhammer's y through its origin):
the nearest joint-to-axis distance; the finger and thumb VERTICES inside the shaft (radius R, deepest, cm); the wrap = the angular spread
of those joints round the axis (deg, smallest over the frames that hold). The left hand counts only on frames where it holds the shaft
(its four fingers' 2nd joints all within 9 cm of the axis). Pads (2026-11-01, user: "his pinky is not holding the hammer"): per finger,
the 2nd and 3rd phalanx's nearest skin to the shaft's SURFACE (cm), worst finger and phalanx over the held frames: a finger standing off the
shaft passed the joint and wrap numbers above. Args: <glb> [json]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
R = 0.030
m = Model(Glb(sys.argv[1])); d = m.glb.json; names = [n.get('name') for n in d['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
dom = np.concatenate([np.array([jn[P[k]['joints'][v][np.argmax(P[k]['weights'][v])]] for v in range(len(P[k]['positions']))]) for k in USE])
FING = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
iX = names.index('Xhammer')
rep = {}
for an in d['animations']:
    c = an['name']; T = m.clip_times(c)[-1]; rep[c] = {}
    for S in 'RL':
        fv = np.where(np.array([f' {S} ' in x and any(k in x for k in FING) for x in dom]))[0]
        jid = [names.index(f'Bip01 {S} {f}{k}') for f in FING for k in (2, 3)]
        gid = [names.index(f'Bip01 {S} {f}2') for f in FING[1:]]
        mind, inside, wraps, held = 9.0, 0.0, [], 0
        pv = {(f, k): np.where(dom == f'Bip01 {S} {f}{k}')[0] for f in FING[1:] for k in (2, 3)}; padw = {}
        for t in np.arange(0, T + 1e-6, 1 / 30):
            w = m.world(m.sample(c, float(t)))
            o = w[iX][:3, 3]; a = w[iX][:3, 1] / np.linalg.norm(w[iX][:3, 1])
            rad = lambda p: np.linalg.norm((p - o) - np.outer((p - o) @ a, a), axis=1)
            if S == 'L' and rad(np.array([w[i][:3, 3] for i in gid])).max() > 0.09: continue
            held += 1
            jp = np.array([w[i][:3, 3] for i in jid]); rj = rad(jp); mind = min(mind, float(rj.min()))
            X = np.concatenate([m.skinned_positions(w)[k][0] for k in USE])[fv]; al = (X - o) @ a; on = (al > -0.38) & (al < 1.27)
            inside = max(inside, float((R - rad(X[on])).max()) if on.any() else 0)
            XA = np.concatenate([m.skinned_positions(w)[k][0] for k in USE])
            for fk, ids in pv.items(): padw[fk] = max(padw.get(fk, 0.0), float(rad(XA[ids]).min() - R))
            dj = jp - o; dj = dj - np.outer(dj @ a, a); e1 = dj[2] / np.linalg.norm(dj[2]); e2 = np.cross(a, e1)
            ang = np.sort(np.degrees(np.arctan2(dj @ e2, dj @ e1))); wraps.append(360 - np.diff(np.r_[ang, ang[0] + 360]).max())
        if held:
            rep[c][S] = dict(frames=held, joint_to_axis_min_cm=round(mind * 100, 2), inside_cm=round(max(inside, 0) * 100, 2), wrap_deg_min=round(float(min(wraps)), 0), wrap_deg_median=round(float(np.median(wraps)), 0),
                              pad_gap_cm={f'{f}{k}': round(v * 100, 2) for (f, k), v in padw.items()})
    print(f"{c:13s} " + ' | '.join(f"{S}: joints {v['joint_to_axis_min_cm']:4.2f} cm, inside {v['inside_cm']:4.2f} cm, wrap min/med {v['wrap_deg_min']:3.0f}/{v['wrap_deg_median']:3.0f} deg, worst pad gap {max(v['pad_gap_cm'].values()):4.2f} cm {max(v['pad_gap_cm'], key=v['pad_gap_cm'].get)} ({v['frames']} f)" for S, v in rep[c].items()), flush=True)
if len(sys.argv) > 2: json.dump(rep, open(sys.argv[2], 'w'), indent=1)
