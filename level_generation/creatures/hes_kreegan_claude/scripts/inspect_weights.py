import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
body = bpy.data.objects['Body']; me = body.data
co = np.array([v.co[:] for v in me.vertices])
for gname in sys.argv[sys.argv.index('--') + 1:]:
    gi = body.vertex_groups[gname].index
    w = np.array([next((g.weight for g in v.groups if g.group == gi), 0) for v in me.vertices])
    m = w > 0.3
    if m.sum() == 0: print('WGT', gname, 0); continue
    c = co[m]
    print('WGT', gname, int(m.sum()), 'min', np.round(c.min(0), 3).tolist(), 'max', np.round(c.max(0), 3).tolist(), 'mean', np.round(c.mean(0), 3).tolist())
