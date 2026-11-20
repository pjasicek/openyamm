"""Rigid-head probe: for the head-set vertices, the Head weight share by height and depth (front face vs nape).
Args (Blender): <blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
body = bpy.data.objects['Body']; me = body.data
hf = np.zeros(len(me.polygons), int); me.attributes['head'].data.foreach_get('value', hf)
hv = np.zeros(len(me.vertices), bool)
for p in me.polygons:
    if hf[p.index]: hv[list(p.vertices)] = True
names = {g.index: g.name for g in body.vertex_groups}
rows = []
for v in me.vertices:
    if not hv[v.index]: continue
    tot = sum(g.weight for g in v.groups) or 1
    w = {names[g.group]: g.weight / tot for g in v.groups}
    co = body.matrix_world @ v.co
    rows.append((co.z, co.y, w.get('Bip01 Head', 0) + w.get('Bip01 Ponytail1', 0), w.get('Bip01 Neck', 0)))
r = np.array(rows)
for z0 in np.arange(0.60, 0.96, 0.03):
    m = (r[:, 0] >= z0) & (r[:, 0] < z0 + 0.03)
    if not m.any(): continue
    fr = m & (r[:, 1] < -0.02); bk = m & (r[:, 1] >= 0.02)
    print('FACEW z %.2f n %d head front %.2f back %.2f min_front %.2f neck_front %.2f' % (z0, m.sum(),
          r[fr, 2].mean() if fr.any() else -1, r[bk, 2].mean() if bk.any() else -1, r[fr, 2].min() if fr.any() else -1,
          r[fr, 3].mean() if fr.any() else -1))
