"""Cross-section segments of the Body (bind pose, Meshy space = rig space) at y stations and at x = 0, with each
face's lip flag and dominant side. Args: -- <blend> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects.get('Body') or bpy.data.objects['DragonKing']; me = body.data
CO = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
lip = np.zeros(len(me.polygons), bool)
if 'lip' in me.attributes: me.attributes['lip'].data.foreach_get('value', lip)
UPPER = {'Xheadpiv', 'Xhead', 'Xjawbase', 'Xtopfinpiv', 'Xtopfinpiv01', 'Xfinpiv', 'Xfinpiv01'}
LOWER = {'Xjaw', 'Xjawpivot', 'Xchinfinpiv', 'Xchinfinpiv01', 'Xbotfinpiv', 'Xbotfinpiv01', 'Xtong', 'Xtongpiv'}
vg = {g.index: g.name for g in body.vertex_groups}
side = np.zeros(len(me.vertices))
for v in me.vertices:
    s = sum(g.weight for g in v.groups) or 1
    side[v.index] = (sum(g.weight for g in v.groups if vg[g.group] in UPPER) - sum(g.weight for g in v.groups if vg[g.group] in LOWER)) / s
tris = [tuple(p.vertices) for p in me.polygons]
segs = {}
def cut(axis, c):
    out = []
    for fi, t in enumerate(tris):
        P = CO[list(t)]; d = P[:, axis] - c
        if d.min() > 0 or d.max() < 0: continue
        pts = []
        n = len(t)
        for i in range(n):
            j = (i + 1) % n
            if (d[i] > 0) != (d[j] > 0):
                w = d[i] / (d[i] - d[j]); pts.append(P[i] + w * (P[j] - P[i]))
        if len(pts) == 2:
            sd = side[list(t)].mean()
            out.append(np.concatenate([pts[0], pts[1], [lip[fi], sd]]))
    return np.array(out)
res = {}
for y in (-4.8, -4.4, -4.0, -3.6, -3.2, -2.8, -2.4):
    res[f'y{y}'] = cut(1, y)
res['x0'] = cut(0, 0.0); res['x03'] = cut(0, 0.3)
np.savez(a[1], **res)
print('SLICES', {k: len(v) for k, v in res.items()})
