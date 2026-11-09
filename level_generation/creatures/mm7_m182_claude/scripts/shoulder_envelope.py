"""Shoulder envelope for removing the Meshy wing (v2, system Python).

The Meshy wing is replaced by a procedural wing. Beyond |x| = 0.075 the Meshy arm, fingers and membrane are cut away;
inside it, the arm stub and thin membrane flaps hang off the shoulder. Rays along +X on a 2 mm (y, z) grid give the
outermost |x| of the remaining surface per row; inside the shoulder box the envelope is a harmonic fill from the
flank around it, so the stub and flaps do not set it. Vertices more than 2.5 mm
outside this envelope in the shoulder box are removed by scripts/assemble_wing.py and the holes filled.
Usage: shoulder_envelope.py <mesh.npz> <out.npz>"""
import sys
import numpy as np
from scipy import ndimage
d = np.load(sys.argv[1]); co = d['co'].copy(); T = d['tris']
co[:, 0] = np.abs(co[:, 0])              # symmetric mesh: work on |x|
ax = co[:, 0]
cut = (ax > .075) & (co[:, 2] > .235) & (co[:, 1] > -.36) & (co[:, 1] < -.02)
keep = ~cut[T].any(1)
STEP = .002; ys = np.arange(-.40, .02, STEP); zs = np.arange(.10, .45, STEP)
maxx = np.zeros((len(ys), len(zs)))
for t in T[keep]:
    p = co[t]; a, b, c = p[:, 1:]
    lo = np.floor((np.minimum(np.minimum(a, b), c) - [ys[0], zs[0]]) / STEP).astype(int) + 1
    hi = np.floor((np.maximum(np.maximum(a, b), c) - [ys[0], zs[0]]) / STEP).astype(int)
    lo = np.maximum(lo, 0); hi = np.minimum(hi, [len(ys) - 1, len(zs) - 1])
    if (hi < lo).any(): continue
    gy, gz = np.meshgrid(ys[lo[0]:hi[0] + 1], zs[lo[1]:hi[1] + 1], indexing='ij')
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-14: continue
    w0 = ((b[1] - c[1]) * (gy - c[0]) + (c[0] - b[0]) * (gz - c[1])) / den
    w1 = ((c[1] - a[1]) * (gy - c[0]) + (a[0] - c[0]) * (gz - c[1])) / den
    w2 = 1 - w0 - w1; m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
    xs = np.where(m, w0 * p[0, 0] + w1 * p[1, 0] + w2 * p[2, 0], 0)
    sub = maxx[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1]; np.maximum(sub, xs, out=sub)
# inside the shoulder box the envelope is inpainted from the surrounding flank (harmonic fill, boundary values from
# outside the box), so neither the stub, its opening nor the flaps set it
Y, Z = np.meshgrid(ys, zs, indexing='ij')
box = (Y > -.33) & (Y < -.12) & (Z > .25) & (Z < .38)
env = maxx.copy(); env[box] = np.mean(maxx[~box & (maxx > 0) & (Y > -.36) & (Y < -.08) & (Z > .22) & (Z < .41)])
for _ in range(4000):
    lap = .25 * (np.roll(env, 1, 0) + np.roll(env, -1, 0) + np.roll(env, 1, 1) + np.roll(env, -1, 1))
    env[box] = lap[box]
env = np.where(box, ndimage.gaussian_filter(env, 2), env)
np.savez(sys.argv[2], ys=ys, zs=zs, env=env, maxx=maxx)
print('ENVELOPE', 'removed protrusion max mm', round(float((maxx - env).max() * 1000), 1))
