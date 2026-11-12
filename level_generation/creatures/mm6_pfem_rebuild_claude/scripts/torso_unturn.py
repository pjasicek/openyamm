#!/usr/bin/env python3
"""Follow-up 2 (2026-11-12, the user: "what is wrong with her torso?"): assemble.py turned the sleeves onto MM9's bind arm by rotating
every shell vertex with |x| > 5 cm and a positive reach along the v3 arm about the shoulder. That reach includes the bodice's sides down to
the waist, so the whole side of the bodice swung 5-7 cm outwards: a boxy bodice wider than the belt and the skirt top, a shelf at both hips
(compose.py then tucked only the rim under the belt's top edge, which made the step).
This keeps the turn on the white sleeves and chemise and undoes it on the green bodice (the region mask of the paint, by UV), blended over a
few rings at the armhole. Positions only: topology, UVs and paints are unchanged (the paints belong to work/uv.npz).
Writes <asm out> (asm2 with new co) and <uv out> (uv.npz with new co). Args: <asm2 npz> <uv npz> <region mask png> <asm out> <uv out>"""
import json
import sys
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix

A_, U_, MASK, AO, UO = sys.argv[1:6]
A = dict(np.load(A_)); U = dict(np.load(U_))
names = [str(x) for x in A['names']]; co, cu, comp, tri = A['co'], A['co_up'], A['comp'], A['tri']
JJ = {k: np.array(v) for k, v in json.loads(str(A['v3joints'])).items()}
SH, EL = JJ['mixamorig:RightArm'], JJ['mixamorig:RightForeArm']
MM9_DIR = np.array([-0.382, -0.026, -0.255]); MM9_DIR /= np.linalg.norm(MM9_DIR)
u3 = (EL - SH) / np.linalg.norm(EL - SH)


def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def rodr(a, b, k):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); s_ = np.linalg.norm(v); th_ = np.arctan2(s_, a @ b) * k
    if s_ < 1e-9: return np.eye(3)
    v /= s_; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(th_) * K + (1 - np.cos(th_)) * K @ K


# green (bodice) per asm vertex: the body set's region mask at each UV copy, max over copies
R = np.asarray(Image.open(MASK))[..., 0].astype(float) / 255.0; S = R.shape[0]
uv, orig, utri, umat = U['uv'], U['orig'], U['tri'], U['mat']
vm = np.full(len(uv), -1); vm[utri.ravel()] = np.repeat(umat, 3)
px = np.clip((uv[:, 0] * S).astype(int), 0, S - 1); py = np.clip(((1 - uv[:, 1]) * S).astype(int), 0, S - 1)
gv = np.where(vm == 0, R[py, px], 0.0)
green = np.zeros(len(co)); np.maximum.at(green, orig, gv)
dress = comp == names.index('dress')
# keep = 1 keeps the sleeve turn (white sleeve), 0 undoes it (green bodice); smoothed over the dress's edges
keep = np.where(dress, 1.0 - np.clip(green, 0, 1), 1.0)
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
Ad = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(co), len(co))).tocsr(); Ad.data[:] = 1
deg = np.maximum(np.asarray(Ad.sum(1)).ravel(), 1)
for _ in range(int(__import__('os').environ.get('PASSES', '3'))):
    keep[dress] = 0.5 * keep[dress] + 0.5 * ((Ad @ keep) / deg)[dress]
new = co.copy(); moved = 0; shift = np.zeros(len(co))
for sgn in (-1, 1):
    fl = np.array([1 if sgn < 0 else -1, 1, 1])
    s0, m, a = SH * fl, MM9_DIR * fl, u3 * fl
    kk = ss((cu - s0) @ a, -0.03, 0.08)
    for i in np.where(dress & (co[:, 0] * sgn > 0.05) & (kk > 0) & (keep < 0.999))[0]:
        full = s0 + rodr(a, m, kk[i]) @ (cu[i] - s0)
        part = s0 + rodr(a, m, kk[i] * keep[i]) @ (cu[i] - s0)
        new[i] = co[i] + (part - full); shift[i] = np.linalg.norm(part - full); moved += 1
A['co'] = new
U['co'] = new[orig]
np.savez(AO, **A); np.savez(UO, **U)
# waist half-widths before / after, bodice only
w = []
for z in (0.20, 0.24, 0.28):
    s = dress & (np.abs(co[:, 2] - z) < 0.01)
    w.append(f'z{z:.2f} {np.abs(co[s, 0]).max():.3f}->{np.abs(new[s, 0]).max():.3f}')
print('UNTURN moved', moved, 'max shift mm', round(float(shift.max()) * 1000, 1), 'bodice half-width', ', '.join(w))
