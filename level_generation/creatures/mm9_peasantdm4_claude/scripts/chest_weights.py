"""Diagnostic: weight shares of the body (non-head, non-hand) vertices of the chest/collarbone region by height band
(Blender rest; front y < Y_MAX, |x| < X_MAX). Args (Blender): <blend> [x_max 0.2] [y_max 0.2] [z0 0.1] [z1 0.36]"""
import bpy, bmesh, sys
from collections import defaultdict
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
XM = float(a[1]) if len(a) > 1 else 0.2; YM = float(a[2]) if len(a) > 2 else 0.2
Z0 = float(a[3]) if len(a) > 3 else 0.1; Z1 = float(a[4]) if len(a) > 4 else 0.36
ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); hl = bm.faces.layers.int['head']; kl = bm.faces.layers.int['hand']
vs = {v.index for f in bm.faces if not f[hl] and not f[kl] for v in f.verts}
names = [g.name for g in ob.vertex_groups]
for side, cond in (('front', lambda y: y < 0.0), ('back', lambda y: y >= 0.0)):
    share = defaultdict(lambda: defaultdict(float)); cnt = defaultdict(int)
    for i in vs:
        v = me.vertices[i]; x, y, z = v.co
        if abs(x) > XM or z < Z0 or z > Z1 or not cond(y) or y > YM: continue
        zb = round(z * 20) / 20; tot = sum(g.weight for g in v.groups) or 1; cnt[zb] += 1
        for g in v.groups: share[zb][names[g.group]] += g.weight / tot
    for zb in sorted(cnt):
        n = cnt[zb]
        print('CHESTW %s z %.2f n %4d ' % (side, zb, n) + ', '.join(f'{k} {s / n:.2f}' for k, s in sorted(share[zb].items(), key=lambda kv: -kv[1])[:6]))
