#!/usr/bin/env python3
"""Staff grip gate: per clip at 30 fps against the staff shaft (the straight part, LichKingStaff primitive on Bone01, vertices within 0.25 m of
the fist; radius RS):
- joints: the right finger joints' (2, 3) distance to the shaft axis, inside = a joint within RS + 6 mm, and the angular spread (wrap) of the
  joints round the axis (r1-r13 gate, kept);
- palm (2026-11-01): the palm-side skin of the right hand (R Hand vertices between wrist and knuckles whose bind normal faces the palm side)
  against the shaft surface: min gap and the gap at the palm's 10th percentile; the axis must run along the palm, so a staff beside the
  fingertips fails;
- pads: per finger and phalanx, the distal half of the phalanx's skin (vertices led by that bone, beyond the median along the bone) against
  the surface: min gap per phalanx, worst over the clip;
- thumb: the angle round the axis between where the palm meets the shaft (its 8 nearest palm vertices) and the thumb's last phalanx (a thumb
  closing on the far side of the shaft reads > 90 deg); fingertips: the same angle for the four fingers' last phalanges (least of the four);
- skin inside: hand vertices (R Hand and finger bones) inside the shaft's circumscribed radius RS (no tolerance), worst depth.
The palm side comes from rig.json['grip']['palm_side'] (raw ABC Blender frame) carried into the GLB (glTF frame, mirrored with --mirrored,
which the export is). Args: <glb> [json] [--mirrored] [--clips A,B] [--every N]"""
import sys, json, numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
args = [a for a in sys.argv[1:] if not a.startswith('--')]
opt = {a.split('=')[0]: (a.split('=')[1] if '=' in a else True) for a in sys.argv[1:] if a.startswith('--')}
m = Model(Glb(args[0])); doc = m.glb.json; nn = [n['name'] for n in doc['nodes']]
prims = doc['meshes'][0]['primitives']
mats = [doc['materials'][p['material']]['name'] for p in prims]
si = mats.index('LichKingStaff'); bi = [i for i, n in enumerate(mats) if n.startswith('LichKing_') or n == 'LichKing'][0]; RS = 0.0165
jn = [nn[j] for j in m.joints]; pj = m.primitives[si]
STAFFV = np.where((pj['joints'][:, 0] == jn.index('Bone01')) & (pj['weights'][:, 0] > 0.99))[0]   # the shaft only (caps share the material)
rj = json.load(open('work/rig.json')); GR = rj['grip']
def tog(p): p = np.array([p[0], p[2], -p[1]], float); return p * ([-1, 1, 1] if opt.get('--mirrored') else 1)
# --- bind-time selections
IB = m.inverse_binds; Wb = {jn[k]: np.linalg.inv(IB[k]) for k in range(len(jn))}
pb = m.primitives[bi]; V = pb['positions']; J = pb['joints']; Wt = pb['weights']
NRM = m.glb.accessor(prims[bi]['attributes']['NORMAL']).astype(float)
def lead(v):
    return jn[J[v][np.argmax(Wt[v])]]
dom = np.array([jn[J[v][np.argmax(Wt[v])]] for v in range(len(V))])
dw = Wt.max(1)
FING = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
fbones = [f'Bip01 R {f}{k}' for f in FING for k in (1, 2, 3)]
hand_all = np.where(np.isin(dom, fbones + ['Bip01 R Hand']))[0]
n_palm = tog(GR['palm_side']); n_palm /= np.linalg.norm(n_palm); fd = tog(GR['finger_dir']); fd /= np.linalg.norm(fd)
wr = Wb['Bip01 R Hand'][:3, 3]; kn = np.mean([Wb[f'Bip01 R {f}1'][:3, 3] for f in FING[1:]], 0)
L = (kn - wr) @ fd; s = (V - wr) @ fd
palm = np.where((dom == 'Bip01 R Hand') & (dw > 0.5) & (s > 0.35 * L) & (s < L + 0.012) & (NRM @ n_palm > 0.35))[0]
Rh = Wb['Bip01 R Hand'][:3, :3]; n_loc = Rh.T @ n_palm
pads = {}
for f in FING:
    for k in (1, 2, 3):
        b = f'Bip01 R {f}{k}'; vv = np.where(dom == b)[0]
        if len(vv) < 3: continue
        h = Wb[b][:3, 3]; d = (Wb[f'Bip01 R {f}{k + 1}'][:3, 3] - h) if k < 3 else (h - Wb[f'Bip01 R {f}{k - 1}'][:3, 3])
        d /= np.linalg.norm(d); pr = (V[vv] - h) @ d; pads[b] = vv[pr >= np.median(pr)]
print(f'# palm vertices {len(palm)}, hand vertices {len(hand_all)}, pad sets {len(pads)}')
clips = opt['--clips'].split(',') if '--clips' in opt else [a['name'] for a in doc['animations']]
every = int(opt.get('--every', 1))
rep = {}
for clip in clips:
    T = m.clip_times(clip)[-1]; worst = 0.0; wrap_min = 999; arr = []
    pg_min, pg10, ins, thumb, tips_a = [], [], 0.0, [], []; padw = {b: -1.0 for b in pads}; padmin = {b: 9.0 for b in pads}
    for t in np.arange(0, T + 1e-6, every / 30):
        w = m.world(m.sample(clip, float(t))); SP = m.skinned_positions(w); S = SP[si][0]; B = SP[bi][0]
        fist = np.mean([w[nn.index(f'Bip01 R {f}2')][:3, 3] for f in ('Index', 'Middle', 'Ring', 'Pinky')], 0)
        S = S[STAFFV]; S = S[np.linalg.norm(S - fist, axis=1) < 0.25]; c = S.mean(0); u = np.linalg.svd(S - c)[2][0]
        span = (S - c) @ u
        def rad(P): d = P - c; return np.linalg.norm(d - np.outer(d @ u, u), axis=1), d @ u
        pts = []
        for f in FING:
            for k in (2, 3):
                pts.append(w[nn.index(f'Bip01 R {f}{k}')][:3, 3])
        pts = np.array(pts); d = pts - c; r = np.linalg.norm(d - np.outer(d @ u, u), axis=1)
        worst = max(worst, float((RS + 0.006 - r).max()))
        e1 = d[2] - (d[2] @ u) * u; e1 /= np.linalg.norm(e1); e2 = np.cross(u, e1)
        ang = np.degrees(np.arctan2(d @ e2, d @ e1)); wrap_min = min(wrap_min, float(np.ptp(ang)))
        arr.append(float(r.min()))
        # palm, pads, thumb, inside
        rp, _ = rad(B[palm]); gp = rp - RS; pg_min.append(float(gp.min())); pg10.append(float(np.percentile(gp, 10)))
        rh, sh = rad(B[hand_all]); ok = (sh > span.min()) & (sh < span.max()); ins = max(ins, float((RS - rh[ok]).max(initial=0)))
        for b, vv in pads.items():
            g_ = float((rad(B[vv])[0] - RS).min()); padw[b] = max(padw[b], g_); padmin[b] = min(padmin[b], g_)
        pc = B[palm][np.argsort(gp)[:8]].mean(0) - c; pc -= (pc @ u) * u                 # where the palm meets the shaft
        def angf(b):
            tc = B[pads[b]].mean(0) - c; tc -= (tc @ u) * u
            return float(np.degrees(np.arccos(np.clip(pc @ tc / np.linalg.norm(pc) / np.linalg.norm(tc), -1, 1))))
        thumb.append(angf('Bip01 R Thumb3')); tips_a.append(min(angf(f'Bip01 R {f}3') for f in FING[1:]))
    pr = {f: [round(padw[f'Bip01 R {f}{k}'] * 100, 2) for k in (1, 2, 3) if f'Bip01 R {f}{k}' in padw] for f in FING}
    rep[clip] = dict(min_joint_dist_cm=round(min(arr) * 100, 2), inside_cm=round(max(worst, 0) * 100, 2), wrap_deg=round(wrap_min, 0),
                     palm_gap_min_cm=[round(min(pg_min) * 100, 2), round(max(pg_min) * 100, 2)], palm_gap_p10_cm=round(max(pg10) * 100, 2),
                     skin_inside_cm=round(ins * 100, 2), thumb_deg=[round(min(thumb)), round(max(thumb))], fingertip_deg_min=round(min(tips_a)), pad_gap_worst_cm=pr,
                     pad_gap_min_cm={b[8:]: round(v * 100, 2) for b, v in padmin.items()})
    print(f'{clip:15} joint-to-axis min {min(arr)*100:5.2f} cm  inside {max(worst,0)*100:4.2f} cm  wrap {wrap_min:4.0f} deg | palm gap '
          f'{min(pg_min)*100:5.2f}..{max(pg_min)*100:5.2f} p10 {max(pg10)*100:5.2f} cm  skin inside {ins*100:4.2f} cm  thumb {min(thumb):4.0f}..{max(thumb):4.0f} deg  '
          f'fingertips >= {min(tips_a):4.0f} deg')
    print('   pads (worst gap cm, phalanx 1/2/3):', '  '.join(f'{f} {"/".join(str(x) for x in v)}' for f, v in pr.items()))
if args[1:]: json.dump(rep, open(args[1], 'w'), indent=1)
