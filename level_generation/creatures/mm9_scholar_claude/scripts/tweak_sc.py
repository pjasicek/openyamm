#!/usr/bin/env python3
"""Scholar geometry tweak after the paint (positions only, UVs unchanged; no face feature moves).
EARS: Meshy's ear tips (part of the head shell, beside the temples) poked out through the long hair at both sides (viewer face sheets f1-f4;
the clay of the head and hair shells, work/st/dbgh_sheet.png). Head-shell vertices beyond |x| X0 in the ear band (z Z0-Z1), behind the face front (y > EAR_YMIN), are folded toward
the skull: |x| -> X0 + K (|x| - X0), faded over the band's top and bottom 1 cm. The hair covers them as in MM9.
(A first version pulled every side vertex inside the hair's nearest inner surface and moved cheek-side skin by 2-3 mm: dropped.)
Writes <out asm npz> and <out uv npz> (uv npz co = tweaked asm co[orig]). Args: <asm npz> <uv npz> <out asm npz> <out uv npz>"""
import sys, os
import numpy as np
A, U, OA, OU = sys.argv[1:5]
S = dict(np.load(A)); co, comp = S['co'].copy(), S['comp']; names = [str(x) for x in S['names']]
H = names.index('head')
X0, K, Z0, Z1 = (float(os.environ.get(k, d)) for k, d in (('EAR_X0', '0.064'), ('EARK', '0.0'), ('EAR_Z0', '0.72'), ('EAR_Z1', '0.86')))
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
v = np.where((comp == H) & (np.abs(co[:, 0]) > X0) & (co[:, 1] > float(os.environ.get('EAR_YMIN', '-0.025'))))[0]      # behind the face front only
f = ss(co[v, 2], Z0, Z0 + 0.01) * (1 - ss(co[v, 2], Z1 - 0.01, Z1))
ax = np.abs(co[v, 0]); nx = X0 + K * (ax - X0); new = ax + (nx - ax) * f
print('EARS folded', int((f > 0).sum()), 'vertices, max', round(float((ax - new).max()) * 1000, 1), 'mm')
co[v, 0] = np.sign(co[v, 0]) * new
# 2. The legs (Meshy's boots, 27 cm tall, + a plain shin tube) pushed through the robe when walking (robe gate 7.9 cm, the boot shafts in front
#    of the lagging robe; MM9's own feet are low shoes under the hem): everything above BOOTTOP over the floor is compressed to BOOTK of its
#    height, so the boots become low shoes and the shin a short stub inside the hem. (r16: 0.10 / 0.15 -> 0.09 / 0.05: the stub top ring
#    still came out through the robe front in Running 7.3 cm and Cower 5.5 cm.)
L_ = names.index('legs'); lv = np.where(comp == L_)[0]; Z0 = -0.8986; t0 = Z0 + float(os.environ.get('BOOTTOP', '0.09')); BK = float(os.environ.get('BOOTK', '0.05'))
zz = co[lv, 2]; hi = zz > t0; zmax = zz.max()
co[lv[hi], 2] = t0 + (zz[hi] - t0) * BK
print('LEGS top', round(float(zmax), 3), '->', round(float(co[lv, 2].max()), 3))
# 3. The forearm stubs of the grafted hands (7 cm behind MM9's wrist) ended in a cut ring visible inside the wide bell sleeves (viewer Fidget):
#    the stub behind the wrist is stretched to STUBK of its length up the forearm axis, so its end sits deep in the sleeve's shade.
#    (An inner sleeve cap, cuff_caps_sc.py, closed the view but MM9's Fidget folds the left hand back 114 deg into the sleeve: the closed
#    sleeve then counted the fingers as inside the body, 42 frames; not used.)
Hh = names.index('hands'); hv2 = np.where(comp == Hh)[0]; wr0, ax0 = S['wr'], S['ax']; STUBK = float(os.environ.get('STUBK', '1.0')); nst = 0
for sg in (1, -1):
    w = wr0 * [sg, 1, 1]; a = ax0 * [sg, 1, 1]; q = hv2[co[hv2, 0] * sg > 0]
    al = (co[q] - w) @ a; b = al < -0.005
    co[q[b]] += a[None] * ((al[b] + 0.005) * (STUBK - 1))[:, None]; nst += int(b.sum())
print('STUB verts', nst, 'length x', STUBK)
# 4. Mouth corners (review r9: the Master Scholar's mouth read downturned and stern; MM9's smiles slightly): head vertices within MR of each
#    mouth corner (CX, CY, CZ mirrored) rise LIFT, falling off as (1 - d / MR)^2 (the paint moves with them; shared by both tiers).
CX, CY, CZ, MR, LIFT = (float(os.environ.get(k, d)) for k, d in (('MC_X', '0.022'), ('MC_Y', '-0.065'), ('MC_Z', '0.733'), ('MC_R', '0.011'), ('MC_LIFT', '0.0022')))
hv3 = np.where(comp == H)[0]; nm = 0
for sx in (1, -1):
    d = np.linalg.norm(co[hv3] - np.array([CX * sx, CY, CZ]), axis=1); w = np.clip(1 - d / MR, 0, 1) ** 2
    co[hv3, 2] += LIFT * w; nm += int((w > 0).sum())
print('MOUTH corners lifted', nm, 'vertices, max', LIFT * 1000, 'mm')
S['co'] = co; np.savez(OA, **S)
D = dict(np.load(U)); D['co'] = co[D['orig']]; np.savez(OU, **D); print('TWEAKED', OA, OU)
