"""Landmarks on the cleaned body (Blender coords, figure faces -Y, figure's right = -X) for fit_nj.json. Args: <clean blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
o = bpy.data.objects['Body']; me = o.data
P = np.array([v.co[:] for v in me.vertices])
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
pa = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: pa[v] = fp[p.index]
R = P[:, 0] < 0
hand = P[(pa == 4) & R]
print('hand bbox', hand.min(0).round(3), hand.max(0).round(3))
# hand axis: PCA
c = hand.mean(0); u, s, vt = np.linalg.svd(hand - c); ax = vt[0] * np.sign(-vt[0][2])
tip = hand[np.argmin((hand - c) @ -ax)] if False else hand[np.argmax((hand - c) @ -ax)]
print('hand centre', c.round(3), 'axis down', (-ax).round(3), 'tip', tip.round(3))
# arm: coat verts on the right beyond x<-0.2, slices perpendicular to a rough axis
arm = P[(pa == 1) & (P[:, 0] < -0.19) & (P[:, 2] > 0.12)]
top = np.array([-0.21, 0.0, 0.53]); bot = hand[np.argmax(hand[:, 2])]
d = (bot - top) / np.linalg.norm(bot - top)
t = (arm - top) @ d
for k in np.arange(0.0, np.linalg.norm(bot - top) + 0.03, 0.03):
    m = np.abs(t - k) < 0.012
    if m.sum() > 4:
        q = arm[m]; print('arm slice', round(k, 2), (0.5 * (q.min(0) + q.max(0))).round(3), np.ptp(q, 0).round(3), int(m.sum()))
for name, part in (('hose', 5), ('boot', 6)):
    q = P[(pa == part) & R]
    for z in np.arange(q[:, 2].max(), q[:, 2].min(), -0.04):
        m = np.abs(q[:, 2] - z) < 0.012
        if m.sum() > 4:
            r = q[m]; print(name, round(z, 2), (0.5 * (r.min(0) + r.max(0))).round(3), np.ptp(r, 0).round(3))
boot = P[(pa == 6) & R]
print('boot toe', boot[np.argmin(boot[:, 1])].round(3), 'heel', boot[np.argmax(boot[:, 1])].round(3), 'sole z', boot[:, 2].min().round(3))
co = P[pa == 1]
for z in (0.7, 0.66, 0.62, 0.58, 0.54, 0.5, 0.45, 0.4, 0.3, 0.2, 0.1, 0.0):
    m = np.abs(co[:, 2] - z) < 0.01
    r = co[m]
    if len(r): print('coat z', z, 'x', r[:, 0].min().round(3), r[:, 0].max().round(3), 'y', r[:, 1].min().round(3), r[:, 1].max().round(3))
print('coat top', co[:, 2].max().round(3), 'collar ring', co[co[:, 2] > co[:, 2].max() - 0.03].min(0).round(3), co[co[:, 2] > co[:, 2].max() - 0.03].max(0).round(3))
