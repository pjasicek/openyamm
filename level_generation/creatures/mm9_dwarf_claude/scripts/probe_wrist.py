"""Diagnostic (run 2): parts, 'hand' face flag and weights of the mesh round the right wrist. Args: <blend>"""
import bpy, sys
import numpy as np
from collections import Counter
IN = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
H, F = J['Bip01 R Hand'], J['Bip01 R Forearm']; u = (H - F) / np.linalg.norm(H - F)
P = np.array([body.matrix_world @ v.co for v in me.vertices])
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
hf = np.zeros(len(me.polygons), int)
if 'hand' in me.attributes: me.attributes['hand'].data.foreach_get('value', hf)
pa = np.zeros(len(P), int); hv = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: pa[v] = max(pa[v], fp[p.index]); hv[v] = max(hv[v], hf[p.index])
al = (P - H) @ u; rad = np.linalg.norm((P - H) - np.outer(al, u), axis=1)
gs = np.zeros(len(P))
if 'graft_s' in me.attributes: me.attributes['graft_s'].data.foreach_get('value', gs)
names = [g.name for g in body.vertex_groups]
for a0 in np.arange(-0.06, 0.04, 0.01):
    b = (al >= a0) & (al < a0 + 0.01) & (rad < 0.09)
    print('PROBE', f'{a0*100:+.0f}cm', 'parts', dict(Counter(pa[b])), 'hand-flag', int(hv[b].sum()), 'graft_s mean', round(float(gs[b & (hv > 0)].mean()) if (b & (hv > 0)).any() else -1, 2))
print('PROBE groups', [n for n in names if ' R ' in n and ('Hand' in n or 'Forearm' in n)])
