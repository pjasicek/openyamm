"""Pass 2 (coordinator review): MM9's ram horns curl wider than the head-only model's. Horn vertices of the head shell
(|x| beyond X0, all above the jaw) are scaled about the horn root by up to K (ramped from X0 to X1), positions only, so
UVs and paint stay (texels stretch by K). Args: <in blend> <out blend> [K]"""
import bpy, sys, numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; IN, OUT = a[:2]; K = float(a[2]) if len(a) > 2 else 1.4
X0, X1 = 0.14, 0.20
bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Body']; me = o.data
pa = np.zeros(len(me.vertices), int); me.attributes['part'].data.foreach_get('value', pa)
P = np.array([v.co[:] for v in me.vertices])
h = pa == 10
for s in (-1, 1):
    ring = h & (np.abs(P[:, 0] - s * 0.15) < 0.02) & (P[:, 2] > 0.6)
    root = P[ring].mean(0); root[0] = s * 0.13
    m = h & (P[:, 0] * s > X0) & (P[:, 2] > 0.55)
    t = np.clip((P[m, 0] * s - X0) / (X1 - X0), 0, 1); k = 1 + (K - 1) * t * t * (3 - 2 * t)
    P[m] = root + (P[m] - root) * k[:, None]
    print('HORN', s, int(m.sum()), 'root', root.round(3))
for v, p in zip(me.vertices, P): v.co = Vector(p)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
