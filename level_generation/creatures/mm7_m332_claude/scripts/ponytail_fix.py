"""m332: Smart Topology modelled the ponytail (P04) as a stiff arc that stands up to 15 cm off the back (it reads as a horn
in profile; the native and the HD masters let it hang down the back). Below the head's back (z < Z0) the ponytail
is shifted toward the back (y only) by one smooth curve over height: per 1 cm the gap between the tail's front and the
back skin (+ GAP), weighted from 0 at Z0 rising toward Z1, Gaussian-smoothed, applied per vertex by interpolation
(per-band moves shredded the tip), so the tail keeps its thickness.
Edits the 'Body' mesh (not orig_co). Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
ob = bpy.data.objects['Body']; me = ob.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(v.co) for v in me.vertices])
tail = np.where(pv == 4)[0]; skin = np.where((pv == 0) | (pv == 1))[0]
Z1, Z0, GAP = co[tail, 2].min(), float(os.environ.get('Z0', '1.52')), 0.025
zs = np.arange(Z1, Z0 + 0.01, 0.01); dys = []
for z in zs:
    band = tail[np.abs(co[tail, 2] - z) < 0.012]
    near = skin[(np.abs(co[skin, 2] - z) < 0.012) & (np.abs(co[skin, 0] - (co[band, 0].mean() if len(band) else 0)) < 0.06)]
    if not len(band) or not len(near):
        dys.append(np.nan); continue
    w = float(np.clip((Z0 - z) / 0.08, 0, 1))          # full pull 8 cm below Z0
    dys.append(min(0.0, (co[near, 1].max() + GAP - co[band, 1].min()) * w))
dys = np.array(dys); ok = ~np.isnan(dys); dys = np.interp(zs, zs[ok], dys[ok])
k = np.exp(-0.5 * (np.arange(-4, 5) / 2.0) ** 2); k /= k.sum()
dys = np.convolve(np.concatenate([np.repeat(dys[:1], 4), dys, np.repeat(dys[-1:], 4)]), k, 'valid')   # one smooth curve
dy = np.interp(co[tail, 2], zs, dys); dy[co[tail, 2] > Z0] = 0
co[tail, 1] += dy; moved = float(dy.min())
me.vertices.foreach_set('co', co.ravel()); me.update()
# orig_co stays: the Meshy weight transfer matches the original (Meshy-rigged) tail positions
print('PONYTAIL pulled toward the back, max move cm', round(-moved * 100, 1), 'tail z', round(float(Z1), 3), '..', round(float(co[tail, 2].max()), 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
