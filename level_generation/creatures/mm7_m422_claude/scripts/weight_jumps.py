"""Weight discontinuities on a garment: edges whose two vertices' weight vectors differ by more than LIM (L1), with
their rest positions and top bones. Args: -- <blend> <garments comma> [limit]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
body = bpy.data.objects['Body']; me = body.data
G = [int(x) for x in a[1].split(',')]; LIM = float(a[2]) if len(a) > 2 else 0.6
gv = np.array([x.value for x in me.attributes['garment'].data]); co = np.array([v.co[:] for v in me.vertices])
ng = len(body.vertex_groups); W = np.zeros((len(co), ng))
for v in me.vertices:
    for e in v.groups: W[v.index, e.group] = e.weight
names = [g.name for g in body.vertex_groups]
E = np.array([tuple(e.vertices) for e in me.edges]); E = E[np.isin(gv[E[:, 0]], G) & np.isin(gv[E[:, 1]], G)]
d = np.abs(W[E[:, 0]] - W[E[:, 1]]).sum(1)
print('JUMPS edges', len(E), f'> {LIM}', int((d > LIM).sum()), 'p99', round(float(np.percentile(d, 99)), 3))
top = lambda i: ','.join(f'{names[j]}:{W[i, j]:.2f}' for j in np.argsort(-W[i])[:4] if W[i, j] > 0.01)
for k in np.argsort(-d)[:15]:
    i, j = E[k]
    print('JUMP', round(float(d[k]), 2), np.round(co[i], 3), top(i), '|', np.round(co[j], 3), top(j))
