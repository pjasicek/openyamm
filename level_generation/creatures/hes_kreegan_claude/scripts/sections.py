import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1f.blend'))
body = bpy.data.objects['Body']; co = np.array([v.co[:] for v in body.data.vertices])
for z in np.arange(0.1, 1.75, 0.05):
    m = (np.abs(co[:, 2] - z) < 0.012)
    t = m & (np.abs(co[:, 0]) < 0.2)
    if t.sum() == 0: continue
    c = co[t]
    l = m & (co[:, 0] > 0.0)
    print('SEC z %.2f torso x %.3f..%.3f y %.3f..%.3f | all x %.3f..%.3f' % (z, c[:, 0].min(), c[:, 0].max(), c[:, 1].min(), c[:, 1].max(), co[m][:, 0].min(), co[m][:, 0].max()))
