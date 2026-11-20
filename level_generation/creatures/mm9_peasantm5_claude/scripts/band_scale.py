"""PeasantM5 hip band (shirt skirt below the chest, belt, the trouser tops inside them): scaled about the body axis per height
toward MM9 M5's hip extents, ALL layers by the same factors, so the skirt, the hidden trouser top and the inner folds keep their
order (the offset-field fit pulled the skirt in onto the trousers: `review/clay_fit_final.png`). Per 2 cm slice of the band
(z ZLO..ZHI, 4 cm ramps), the 97th-percentile reach of our trunk vertices (|x| < 0.35, arms and hands excluded by weight) to
+x, -x, +y, -y from the slice centre is compared with MM9 M5's surface samples in the same slice; factors clamped to
0.75..1.05 and Gaussian-smoothed over z (3 cm); vertex weight = band ramp x trunk/thigh bone share. Positions only.
Args: -- <in blend> <out blend> <m5 npz> [ZLO -0.20] [ZHI 0.30]"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, M5 = a[:3]; ZLO = float(a[3]) if len(a) > 3 else -0.20; ZHI = float(a[4]) if len(a) > 4 else 0.30
D = np.load(M5); C, T = D['co'].astype(float), D['tris']
A_, B_, C_ = C[T[:, 0]], C[T[:, 1]], C[T[:, 2]]
S = np.concatenate([A_ + u * (B_ - A_) + v * (C_ - A_) for u in np.linspace(0, 1, 6) for v in np.linspace(0, 1, 6) if u + v <= 1])
bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Body']; me = o.data; vg = {g.index: g.name for g in o.vertex_groups}
co = np.array([v.co[:] for v in me.vertices])
TRUNK = ('Spine', 'Pelvis', 'Thigh', 'Bone', 'Bip01')
W = np.zeros(len(co))
for v in me.vertices:
    tot = sum(g.weight for g in v.groups)
    if tot > 0:
        W[v.index] = sum(g.weight for g in v.groups if vg[g.group] == 'Bip01' or any(k in vg[g.group] for k in ('Spine', 'Pelvis', 'Thigh', 'Bone'))) / tot
zs = np.arange(ZLO - 0.04, ZHI + 0.04 + 1e-6, 0.02); F = np.ones((len(zs), 4)); CTR = np.zeros((len(zs), 2))
def reach(P, c):
    d = P - c; out = []
    for ax, sg in ((0, 1), (0, -1), (1, 1), (1, -1)):
        r = d[:, ax] * sg; r = r[r > 0]; out.append(np.percentile(r, 97) if len(r) > 10 else np.nan)
    return np.array(out)
for k, z in enumerate(zs):
    mo = (np.abs(co[:, 2] - z) < 0.025) & (np.abs(co[:, 0]) < 0.35) & (W > 0.5)
    ms = (np.abs(S[:, 2] - z) < 0.025) & (np.abs(S[:, 0]) < 0.35)
    if mo.sum() < 12 or ms.sum() < 40: continue
    c = np.array([0.0, np.median(S[ms, 1])]); CTR[k] = c
    f = reach(S[ms][:, :2], c) / reach(co[mo][:, :2], c)
    F[k] = np.where(np.isnan(f), 1.0, np.clip(f, 0.75, 1.05))
ker = np.exp(-0.5 * (np.arange(-3, 4) * 0.02 / 0.03) ** 2); ker /= ker.sum()
Fs = np.stack([np.convolve(np.pad(F[:, j], 3, mode='edge'), ker, 'valid') for j in range(4)], 1)
Cs = np.stack([np.convolve(np.pad(CTR[:, j], 3, mode='edge'), ker, 'valid') for j in range(2)], 1)
ramp = np.clip((co[:, 2] - (ZLO - 0.04)) / 0.04, 0, 1) * np.clip(((ZHI + 0.04) - co[:, 2]) / 0.04, 0, 1)
w = ramp * W
new = co.copy()
for i in np.where(w > 0)[0]:
    k = np.interp(co[i, 2], zs, np.arange(len(zs)))
    f = np.array([np.interp(k, np.arange(len(zs)), Fs[:, j]) for j in range(4)])
    c = np.array([0.0, np.interp(k, np.arange(len(zs)), Cs[:, 1])])
    d = co[i, :2] - c
    fx = f[0] if d[0] > 0 else f[1]; fy = f[2] if d[1] > 0 else f[3]
    new[i, :2] = c + d * (1 + (np.array([fx, fy]) - 1) * w[i])
for v in me.vertices: v.co = Vector(new[v.index])
me.update(); bpy.ops.wm.save_as_mainfile(filepath=OUT)
m = np.linalg.norm(new - co, axis=1)
print('BAND_SCALE', json.dumps(dict(moved=int((m > 1e-4).sum()), max_mm=round(float(m.max() * 1000), 1),
      factors={f'{z:.2f}': [round(x, 3) for x in Fs[k]] for k, z in enumerate(zs) if k % 3 == 0})))
