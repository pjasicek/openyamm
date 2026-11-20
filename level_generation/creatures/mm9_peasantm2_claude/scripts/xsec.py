import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
o = bpy.data.objects['Body']; me = o.data
P = np.array([v.co[:] for v in me.vertices]); fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
pa = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: pa[v] = fp[p.index]
gi = {g.index: g.name for g in o.vertex_groups}
arm = np.zeros(len(P))
for v in me.vertices: arm[v.index] = sum(g.weight for g in v.groups if any(k in gi[g.group] for k in ('UpperArm', 'Forearm')))
for z in (0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15):
    m = (pa == 1) & (np.abs(P[:, 2] - z) < 0.01) & (P[:, 0] < 0)
    q = P[m]; a = arm[m]; o_ = np.argsort(q[:, 0])
    print('XS z', z, ' '.join(f'{q[i,0]:.2f}/{q[i,1]:.2f}:{a[i]:.1f}' for i in o_[::max(1, len(o_)//18)]))
