#!/usr/bin/env python3
"""Fist probe (follow-up 2026-11-11): one hand of a Titan GLB at a clip time. Vertices are grouped by their dominant
finger (Thumb, Index, Middle, Ring, Pinky; bones 1-3) or the palm (Hand). Each finger bone is a capsule: its posed
axis (joint to child joint; bone 3 to its farthest vertex) with the median distance of its own vertices as radius.
Reports
- pair depth: how far vertices of one finger reach inside another finger's capsule (cm; adjacent fingers that sink
  into each other read as fused), and fingertips (bone 3) inside the palm;
- thumb: thumb tip (distal thumb vertex) gap to the outside of the Index2/Middle2 capsules (cm; ~0 = resting on them,
  negative = inside them) and how far the tip sticks out of the fist (distance past the fist's convex extent along the
  hand's thumb side, cm);
- curl: angle between each finger's bone 3 and the hand bone direction (180 = folded back to the palm).
Usage: hand_probe.py <glb> <clip> <time> [--side Left|Right] [--json out]"""
import argparse, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose as gp
F = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')


def seg_dist(p, a, b):
    ab = b - a; t = np.clip((p - a) @ ab / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1), t


def probe(m, names, clip, time, side):
    w = m.world(m.sample(clip, time)); pts, _ = m.skinned_positions(w)[0]
    pr = m.primitives[0]; jn = [names[j] for j in m.joints]
    dom = np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pts))])
    J = lambda n: w[names.index(n)][:3, 3]
    hand = J(f'{side}Hand'); caps = {}
    for f in F:
        for k in (1, 2, 3):
            n = f'{side}Hand{f}{k}'; a = J(n); sel = dom == n
            if k < 3:
                b = J(f'{side}Hand{f}{k + 1}')
            else:
                d = pts[sel] - a; far = d[np.argmax(np.linalg.norm(d, axis=1))] if sel.any() else (a - J(f'{side}Hand{f}2'))
                b = a + far
            r = float(np.median(seg_dist(pts[sel], a, b)[0])) if sel.sum() > 3 else 0.005
            caps[n] = (a, b, r, sel)
    palm = dom == f'{side}Hand'
    out = {'pairs': {}, 'tips_in_palm': {}}
    for i, fa in enumerate(F):
        va = np.zeros(len(pts), bool)
        for k in (1, 2, 3):
            va |= caps[f'{side}Hand{fa}{k}'][3]
        for fb in F[i + 1:]:
            depth = 0.0
            for k in (1, 2, 3):
                a, b, r, _ = caps[f'{side}Hand{fb}{k}']
                d, t = seg_dist(pts[va], a, b); inside = (t > 0.05) & (t < 0.95)
                if inside.any():
                    depth = max(depth, float((r - d[inside]).max()))
            # and the reverse
            vb = np.zeros(len(pts), bool)
            for k in (1, 2, 3):
                vb |= caps[f'{side}Hand{fb}{k}'][3]
            for k in (1, 2, 3):
                a, b, r, _ = caps[f'{side}Hand{fa}{k}']
                d, t = seg_dist(pts[vb], a, b); inside = (t > 0.05) & (t < 0.95)
                if inside.any():
                    depth = max(depth, float((r - d[inside]).max()))
            out['pairs'][f'{fa}-{fb}'] = round(depth * 100, 2)
    # fingertips into the palm: tip vertices vs the palm surface (nearest palm vertex normal side is unknown; use the
    # palm's thickness: distance to the palm vertex cloud's local plane)
    from scipy.spatial import cKDTree
    kd = cKDTree(pts[palm])
    for f in F[1:]:
        tipv = pts[caps[f'{side}Hand{f}3'][3]]
        d, _ = kd.query(tipv)
        out['tips_in_palm'][f] = round(float(d.min()) * 100, 2)
    # thumb
    tv = pts[caps[f'{side}HandThumb3'][3]]; a3 = caps[f'{side}HandThumb3'][0]
    tip = tv[np.argmax(np.linalg.norm(tv - a3, axis=1))]
    gaps = {}
    for n in ('Index2', 'Middle2', 'Index1', 'Middle1'):
        a, b, r, _ = caps[f'{side}Hand{n[:-1]}{n[-1]}']
        gaps[n] = round(float(seg_dist(tip[None], a, b)[0][0] - r) * 100, 2)
    out['thumb_tip_gap_cm'] = gaps
    fist = np.zeros(len(pts), bool)
    for f in F[1:]:
        for k in (1, 2, 3):
            fist |= caps[f'{side}Hand{f}{k}'][3]
    c = pts[fist].mean(0); u = tip - c; L = np.linalg.norm(u); u /= L
    ext = float(((pts[fist] - c) @ u).max())
    out['thumb_tip_out_cm'] = round((L - ext) * 100, 2)
    hd = J(f'{side}HandMiddle1') - hand; hd /= np.linalg.norm(hd)
    out['curl_deg'] = {f: round(float(np.degrees(np.arccos(np.clip(((caps[f'{side}Hand{f}3'][1] - caps[f'{side}Hand{f}3'][0]) /
                       np.linalg.norm(caps[f'{side}Hand{f}3'][1] - caps[f'{side}Hand{f}3'][0])) @ hd, -1, 1)))), 1) for f in F[1:]}
    out['radius_cm'] = {n[len(side) + 4:]: round(v[2] * 100, 2) for n, v in caps.items()}
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('clip'); ap.add_argument('time', type=float)
    ap.add_argument('--side', action='append'); ap.add_argument('--json')
    o = ap.parse_args(); g = gp.Glb(o.glb); m = gp.Model(g); names = [n.get('name') for n in g.json['nodes']]
    res = {s: probe(m, names, o.clip, o.time, s) for s in (o.side or ['Left', 'Right'])}
    for s, r in res.items():
        print(s, o.clip, o.time, 'pairs', r['pairs'], 'tips->palm', r['tips_in_palm'], 'thumb gap', r['thumb_tip_gap_cm'],
              'thumb out', r['thumb_tip_out_cm'], 'curl', r['curl_deg'])
    if o.json:
        json.dump(res, open(o.json, 'w'), indent=1)
