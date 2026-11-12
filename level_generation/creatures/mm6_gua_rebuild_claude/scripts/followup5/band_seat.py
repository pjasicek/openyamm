#!/usr/bin/env python3
"""Arm bands seated on the upper arms (follow-up 5, user 2026-11-12, left arm close-up: "the blue armband floats off the
upper arm with a gap, skin shows between band and arm").
Cause: the blue cuff (sleeves region of the mask, rigid on Bip01 X UpperArm) stands off the arm: its lower rim is a wider
tube than the arm skin under it, so the skin shows inside the rim from the side and from below.
Fix, geometry of the cuff only, every LOD and shadow mesh, both arms (the right cuff is the same shape): in bind space,
around the arm's own centreline (centroid of the bare skin ring just under the cuff), each cuff vertex is drawn in so
the lower rim lies RIM_GAP outside the arm skin at its angle; the pull fades to nothing at the cuff's top, where it
meets the mail sleeve. Weights, UVs and the paint are unchanged.
Args: <in glb> <out glb>"""
import sys
import numpy as np
from PIL import Image
from glbtool import Glb, Model, image, repack
IN, OUT = sys.argv[1:3]
RIM_GAP, KEEP_TOP = 0.0025, 0.25
g = Glb(IN); doc = g.json; m = Model(g)
names = [n.get('name') for n in doc['nodes']]; jn = [names[j] for j in m.joints]
w0 = m.world({})
mask = np.asarray(image(g, 'gua_region_mask').convert('RGB')).astype(float) / 255


def region(uv):
    h, w = mask.shape[:2]
    return mask[np.clip((uv[:, 1] * h).astype(int), 0, h - 1), np.clip((uv[:, 0] * w).astype(int), 0, w - 1)]


# reference geometry from LOD0
pr0 = m.primitives[0]; P0 = pr0['positions']; J0, W0 = pr0['joints'], pr0['weights']
uv0 = g.accessor(doc['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0'])
REF = {}
for s in 'LR':
    U = w0[names.index(f'Bip01 {s} UpperArm')][:3, 3]; F = w0[names.index(f'Bip01 {s} Forearm')][:3, 3]
    a = (F - U) / np.linalg.norm(F - U)
    arm = np.isin(J0, [jn.index(f'Bip01 {s} {k}') for k in ('UpperArm', 'UpperArm_H', 'Forearm_H')]).any(1)
    sv = (P0 - U) @ a
    near = arm & (np.linalg.norm(np.cross(P0 - U, a), axis=1) < 0.12) & (sv > -0.02) & (sv < 0.33)
    band = near & (region(uv0)[:, 0] > 0.5)
    s_lo, s_hi = sv[band].min(), sv[band].max()
    ring = near & ~band & (sv > s_hi + 0.015) & (sv < s_hi + 0.05)
    c = P0[ring].mean(0); c -= ((c - U) @ a) * a                          # centreline point on the arm's own skin
    e1 = np.cross(a, [0, 0, 1.0]); e1 /= np.linalg.norm(e1); e2 = np.cross(a, e1)
    v = P0[ring] - c; v -= np.outer(v @ a, a)
    th = np.arctan2(v @ e2, v @ e1); rr = np.linalg.norm(v, axis=1)
    bins = np.linspace(-np.pi, np.pi, 25); R = np.full(24, np.nan)
    for k in range(24):
        mm = (th >= bins[k]) & (th < bins[k + 1])
        if mm.any(): R[k] = rr[mm].max()
    ok = ~np.isnan(R); cen = 0.5 * (bins[:-1] + bins[1:])
    REF[s] = dict(U=U, a=a, c=c, e1=e1, e2=e2, s_lo=s_lo, s_hi=s_hi, th=cen[ok], R=R[ok])
    print('BAND %s cuff s %.3f..%.3f, arm skin radius under it %.1f..%.1f mm' % (s, s_lo, s_hi, R[ok].min() * 1000, R[ok].max() * 1000))


def seat(P, uv, J):
    P = P.copy(); moved = np.zeros(len(P))
    reg = region(uv)
    for s, d in REF.items():
        arm = np.isin(J, [jn.index(f'Bip01 {s} UpperArm')]).any(1)
        sv = (P - d['c']) @ d['a'] + (d['c'] - d['U']) @ d['a']
        sel = np.where(arm & (reg[:, 0] > 0.5) & (sv >= d['s_lo'] - 0.005) & (sv <= d['s_hi'] + 0.005)
                       & (np.linalg.norm(np.cross(P - d['U'], d['a']), axis=1) < 0.12))[0]
        if not len(sel): continue
        v = P[sel] - d['c']; ax = np.outer(v @ d['a'], d['a']); rad = v - ax
        r = np.linalg.norm(rad, axis=1); th = np.arctan2(rad @ d['e2'], rad @ d['e1'])
        Rarm = np.interp(th, d['th'], d['R'], period=2 * np.pi)
        f = np.clip((sv[sel] - d['s_lo']) / max(d['s_hi'] - d['s_lo'], 1e-6), 0, 1)
        k = np.clip((f - KEEP_TOP) / (1 - KEEP_TOP), 0, 1); k = k * k * (3 - 2 * k)
        # the cuff's own innermost radius at this angle comes down to the arm + RIM_GAP at the rim
        excess = np.maximum(0.0, r - (Rarm + RIM_GAP))
        rin = np.array([r[np.abs(((th - t + np.pi) % (2 * np.pi)) - np.pi) < 0.3].min() for t in th])
        pull = k * np.minimum(excess, np.maximum(0.0, rin - (Rarm + RIM_GAP)))
        newr = r - pull
        P[sel] = d['c'] + ax + rad / np.maximum(r, 1e-9)[:, None] * newr[:, None]
        moved[sel] = pull
    return P, moved


done = set(); tot = 0; mx = 0.0
for me in doc['meshes']:
    for pr in me['primitives']:
        a = pr['attributes']
        if a['POSITION'] in done: continue
        done.add(a['POSITION'])
        P = g.accessor(a['POSITION']).astype(float); uv = g.accessor(a['TEXCOORD_0']); J = g.accessor(a['JOINTS_0']).astype(int)
        Pn, mv = seat(P, uv, J)
        acc = doc['accessors'][a['POSITION']]; view = doc['bufferViews'][acc['bufferView']]
        off = view.get('byteOffset', 0) + acc.get('byteOffset', 0); assert view.get('byteStride', 12) == 12
        g.bin[off:off + len(Pn) * 12] = Pn.astype(np.float32).tobytes()
        acc['min'] = Pn.min(0).tolist(); acc['max'] = Pn.max(0).tolist()
        tot += int((mv > 1e-5).sum()); mx = max(mx, float(mv.max()))
print('BAND cuff vertices drawn in', tot, 'max %.1f mm' % (mx * 1000))
repack(g); g.write(OUT)
print('BAND written', OUT)
