"""Neck under the collar (user note 2026-11-02, "some artifacts here?": torn gold/skin shards where the neck meets the collar).
Cause: the head split's level cut (head_split.py, z 0.62 within the neck radius) gave the head set a flat diamond apron of the
shell's chest faces down to the brooch; the body's collar faces lie just over it, so the two layers z-fight in the viewer and the
apron's paint (collar remap, skin) shows through as shards.

Fix (positions only; faces, UVs, weights unchanged): per 10-degree angle about the neck axis the top of the body set's collar
(non-head faces within 13 cm of the axis, z > 0.55) is measured; every head-set vertex below that top + ABOVE moves in to the
neck tube: its radius becomes min(own, R(angle) - INSET), R = the head set's radius at the collar top, and its height at
least TOP - DEPTH, so the apron folds down inside the collar as a short tube, INSET behind the collar's inner face.
Args (Blender): <in blend> <out blend> [inset 0.004] [above 0.003] [depth 0.025]"""
import bpy, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
INSET = float(a[2]) if len(a) > 2 else 0.004
ABOVE = float(a[3]) if len(a) > 3 else 0.003
DEPTH = float(a[4]) if len(a) > 4 else 0.025
FLAPH = float(a[5]) if len(a) > 5 else 0.035
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data; rig = body.parent
nb = rig.data.bones['Bip01 Neck']
C = np.array((rig.matrix_world @ nb.head_local)[:2])
P = np.array([v.co[:] for v in me.vertices])
hf = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hf)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
head = np.zeros(len(P), bool); bodyv = np.zeros(len(P), bool)
for p in me.polygons:
    if hn[p.index]:
        continue
    if hf[p.index]:
        head[list(p.vertices)] = True
    else:
        bodyv[list(p.vertices)] = True
bodyv &= ~head
d = P[:, :2] - C
r = np.hypot(d[:, 0], d[:, 1]); ang = np.degrees(np.arctan2(d[:, 0], -d[:, 1]))
bins = np.arange(-180, 181, 10)
neckb = bodyv & (P[:, 2] > 0.55) & (r < 0.13)
top = np.array([P[neckb & (ang >= b) & (ang < b + 10), 2].max() if (neckb & (ang >= b) & (ang < b + 10)).any() else np.nan
                for b in bins[:-1]])
top = np.where(np.isnan(top), np.nanmin(top), top)
top = np.convolve(np.r_[top[-2:], top, top[:2]], np.ones(5) / 5, 'valid')
zc = np.interp(ang, bins[:-1] + 5, top, period=360)
# the head set's neck radius just above the collar top, per angle
band = head & (P[:, 2] > zc + 0.004) & (P[:, 2] < zc + 0.02) & (r < 0.13)
R = np.array([np.median(r[band & (ang >= b - 10) & (ang < b + 20)]) if (band & (ang >= b - 10) & (ang < b + 20)).any() else np.nan
              for b in bins[:-1]])
R = np.where(np.isnan(R), np.nanmedian(R), R)
Rv = np.interp(ang, bins[:-1] + 5, R, period=360)
# r6c: the collar's inner rim radius per angle (body vertices in the top 1.5 cm of the collar): the tube goes 2 mm inside it,
# so there is no gap between neck and collar to look into (an inset from the neck radius left a slit in side views)
rimv = bodyv & (r < 0.16) & (P[:, 2] > zc - 0.015) & (P[:, 2] <= zc + 0.001)
Rc = np.array([np.percentile(r[rimv & (ang >= b - 10) & (ang < b + 20)], 10) if (rimv & (ang >= b - 10) & (ang < b + 20)).sum() > 2 else np.nan
               for b in bins[:-1]])
Rc = np.where(np.isnan(Rc), Rv.mean() if False else np.nanmedian(Rc), Rc)
Rcv = np.interp(ang, bins[:-1] + 5, Rc, period=360)
Rv = np.maximum(Rv, Rcv - 0.002 + INSET)       # target radius = max(neck R, collar rim - 2 mm) - INSET
sel = head & (P[:, 2] < zc + ABOVE) & (r < 0.16)
# r6b: flaps - head vertices flaring more than 1.2 cm outside the neck tube near the collar (above its top too)
flap = head & (r > Rv + 0.012) & (P[:, 2] < zc + FLAPH)
sel |= flap
newP = P.copy()
rn = np.minimum(r, Rv - INSET)
# blend in over the ABOVE band so the visible neck keeps its shape
k = np.where(flap, 1.0, np.clip((zc + ABOVE - P[:, 2]) / max(ABOVE, 1e-4), 0, 1))
rr = r + (rn - r) * k
scale = np.where(r > 1e-6, rr / np.maximum(r, 1e-6), 1)
newP[sel, 0] = C[0] + d[sel, 0] * scale[sel]
newP[sel, 1] = C[1] + d[sel, 1] * scale[sel]
newP[sel, 2] = np.maximum(P[sel, 2], zc[sel] - DEPTH)
me.vertices.foreach_set('co', newP.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('NECKTUCK ' + json.dumps({'moved': int(sel.sum()), 'flap': int(flap.sum()), 'max_move_mm': round(float(np.linalg.norm(newP - P, axis=1).max()) * 1000, 1),
                                'collar_top_z': [round(float(t), 3) for t in top[::6]], 'neck_R': [round(float(x), 3) for x in R[::6]]}))
