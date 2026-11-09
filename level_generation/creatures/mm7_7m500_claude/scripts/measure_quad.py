"""Quadruped joints measured on the mesh (rat chain format for rig_rat.py), for a standing dog/cat (m509 Dog, reused by
the m500 Cat): forward -Y, up +Z, left +X, paws at z = 0, the main shell = piece 0. Writes work/joints.json.
- Legs: horizontal slabs of the shell near the ground (z 4-10 % of the withers height) cluster into four paws by
  quadrant (side of x = 0, front/back of their median y). Each leg is traced upward (3 cm slabs, the centroid of the
  shell vertices within 1.3 LEG_R of the previous centre) up to the trunk's underside at x = 0 above it (zt). Joints from
  the traced centreline at fixed fractions of zt: front = shoulder (55 % up the trunk above the leg, 2 cm
  behind), elbow (0.95 zt), wrist (0.25 zt), toe (the most forward paw vertex near the floor); hind = hip
  (halfway up the trunk), stifle (0.85 zt, 3 cm forward), hock (0.30 zt, 2 cm back), toe.
- Spine: midline points halfway between the trunk's bottom and top (|x| < 3 cm) at the hip, mid-back, withers and the neck base (5 % of the
  body length ahead of the withers). Neck and head: neck base -> skull base (40 % of the way to the nose) -> nose tip
  (the most forward shell vertex above the elbow height).
- Tail: shell vertices behind the hips that are not leg (farther than LEG_R from either hind centreline) and above the
  hock; ordered by their distance from the tail root (the rearmost-top trunk point) and cut into 6 equal arcs; the
  centroids of the arcs are the chain (it follows a hanging or curled tail).
Args: -- <blend>"""
import bpy, sys, os, json
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[-1]))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
me = bpy.data.objects['Body'].data
co = np.array([tuple(v.co) for v in me.vertices]); pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
S = co[pv == 0]
L = S[:, 1].max() - S[:, 1].min()
LEG_R = float(os.environ.get('LEG_R', '0.06'))
zb = np.percentile(S[:, 2], 97)                       # withers/back height (ears excluded by the percentile)
low = S[(S[:, 2] > 0.04 * zb) & (S[:, 2] < 0.10 * zb)]


def trunk(y, zmin):
    """(bottom, top) of the trunk at y on the midline (|x| < 3 cm, above zmin)"""
    m = S[(np.abs(S[:, 0]) < 0.03) & (np.abs(S[:, 1] - y) < 0.02) & (S[:, 2] > zmin)]
    return float(m[:, 2].min()), float(m[:, 2].max())

ymid = np.median(low[:, 1])
legs = {}
for kind, ysel in (('Front', low[:, 1] < ymid), ('Hind', low[:, 1] >= ymid)):
    for sd, xs in (('L', low[:, 0] > 0), ('R', low[:, 0] <= 0)):
        p = low[ysel & xs]; c = p.mean(0); pts = [c.copy()]
        # the leg top = the trunk's underside at x = 0 above this leg pair (the chest / groin)
        und = S[(np.abs(S[:, 0]) < 0.03) & (np.abs(S[:, 1] - c[1]) < 0.05) & (S[:, 2] > 0.15 * zb)]
        zt = float(und[:, 2].min()) if len(und) else 0.5 * zb
        z = c[2]
        while z < zt:
            z += 0.01
            sl = S[(np.abs(S[:, 2] - z) < 0.015) & (np.linalg.norm(S[:, :2] - c[:2], axis=1) < LEG_R * 1.3)]
            if len(sl) < 3:
                continue
            c = np.array([sl[:, 0].mean(), sl[:, 1].mean(), z]); pts.append(c.copy())
        pts = np.array(pts)
        at = lambda zz: np.array([np.interp(zz, pts[:, 2], pts[:, 0]), np.interp(zz, pts[:, 2], pts[:, 1]), zz])
        paw = S[(np.linalg.norm(S[:, :2] - pts[0, :2], axis=1) < LEG_R * 1.5) & (S[:, 2] < 0.08 * zb)]
        toe = paw[np.argmin(paw[:, 1])].copy(); toe[2] = max(toe[2], 0.015)
        top = at(zt)
        if kind == 'Front':
            b_, t_ = trunk(top[1], 0.9 * zt); sh = np.array([top[0] * 0.8, top[1] + 0.02, b_ + 0.55 * (t_ - b_)])
            chain = [sh, at(0.95 * zt), at(0.25 * zt), toe]
        else:
            b_, t_ = trunk(top[1], 0.9 * zt); hp = np.array([top[0] * 0.8, top[1], b_ + 0.5 * (t_ - b_)])
            kn = at(0.85 * zt) + np.array([0, -0.03, 0]); hk = at(0.30 * zt) + np.array([0, 0.02, 0])
            chain = [hp, kn, hk, toe]
        legs[f'{kind}_{sd}'] = {'chain': chain, 'line': pts, 'zt': zt}
        print('LEG', kind, sd, 'top z', round(zt, 3), 'pts', len(pts))


def centre(y, zmin):
    """midline point at y: halfway between the trunk's bottom and top (|x| < 3 cm)"""
    b_, t_ = trunk(y, zmin)
    return np.array([0.0, y, 0.5 * (b_ + t_)])


hy = np.mean([legs[f'Hind_{s}']['chain'][0][1] for s in 'LR']); fy = np.mean([legs[f'Front_{s}']['chain'][0][1] for s in 'LR'])
zt_f = np.mean([legs[f'Front_{s}']['zt'] for s in 'LR']); zt_h = np.mean([legs[f'Hind_{s}']['zt'] for s in 'LR'])
spine = [centre(hy, zt_h * 0.9), centre((hy + fy) / 2, zt_h * 0.9), centre(fy, zt_f * 0.9), centre(fy - 0.05 * L, zt_f * 0.95)]
above = S[S[:, 2] > zt_f]
nose = above[np.argmin(above[:, 1])].copy(); nose[0] = 0.0
skull = spine[3] + 0.6 * (nose - spine[3]); skull = centre(skull[1], zt_f) * 0 + np.array([0.0, skull[1], centre(skull[1], zt_f)[2]])
# tail: behind the hips, not leg, above the hock
root = centre(S[:, 1].max() * 0 + hy + 0.04 * L, zt_h)
hl = [legs[f'Hind_{s}']['line'] for s in 'LR']


def dist_line(p, line):
    return np.min(np.linalg.norm(line[None, :, :] - p[:, None, :], axis=2), axis=1)


cand = S[(S[:, 1] > hy + 0.04 * L) & (S[:, 2] > 0.30 * zt_h)]
for ln in hl:
    cand = cand[dist_line(cand, ln) > LEG_R * 1.3]
d = np.linalg.norm(cand - root, axis=1); order = np.argsort(d); dmax = d.max()
tail = [root]
for k in range(1, 7):
    sel = cand[(d > dmax * (k - 1) / 6) & (d <= dmax * k / 6)]
    tail.append(sel.mean(0) if len(sel) else tail[-1])
tail[-1] = cand[np.argmax(d)]
J = {'note': 'measure_quad.py on work/step1.blend', 'chains': {
    'Spine': [list(map(float, p)) for p in spine],
    'Neck': [list(map(float, spine[3])), list(map(float, skull))],
    'Head': [list(map(float, skull)), list(map(float, nose))],
    'Tail': [list(map(float, p)) for p in tail]}}
for k, v in legs.items():
    J['chains'][k] = [list(map(float, p)) for p in v['chain']]
json.dump(J, open(os.path.join(HERE, 'work', 'joints.json'), 'w'), indent=1)
for k, v in J['chains'].items():
    print('CHAIN', k, [[round(x, 3) for x in p] for p in v])
