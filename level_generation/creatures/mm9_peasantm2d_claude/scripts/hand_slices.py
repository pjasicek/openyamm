import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
me = bpy.data.objects['Body'].data
P = np.array([v.co[:] for v in me.vertices]); fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
pa = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: pa[v] = fp[p.index]
h = P[(pa == 4) & (P[:, 0] < 0)]
top = h[h[:, 2] > h[:, 2].max() - 0.01].mean(0); bot = h[h[:, 2] < h[:, 2].min() + 0.01].mean(0)
d = (bot - top) / np.linalg.norm(bot - top); t = (h - top) @ d
print('HS top', top.round(3), 'bot', bot.round(3), 'len', round(float(np.linalg.norm(bot-top)), 3))
for k in np.arange(0, t.max(), 0.02):
    m = np.abs(t - k) < 0.008
    if m.sum() > 3:
        q = h[m]; r = q - q.mean(0); r -= np.outer(r @ d, d)
        print('HS', round(k, 2), q.mean(0).round(3), 'radius', round(float(np.linalg.norm(r, axis=1).mean()), 3), int(m.sum()))
cuff = P[(pa == 1) & (P[:, 0] < -0.3)]
print('HS sleeve lowest', cuff[cuff[:, 2].argmin()].round(3))
