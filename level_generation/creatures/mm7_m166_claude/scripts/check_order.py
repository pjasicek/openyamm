"""Check that the first vertices of work/uv_master.blend still follow the Meshy order (raw_st1.npz)."""
import bpy, os
import numpy as np
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, 'work/uv_master.blend'))
me = bpy.data.objects['Beholder'].data
co = np.array([tuple(v.co) for v in me.vertices]); raw = np.load(os.path.join(P, 'work/raw_st1.npz'))['co']
n = len(raw); d = co[:n] - raw; d[:, 2] -= np.median(d[:, 2])
print('ORDER max dev', float(np.abs(d).max()), 'bad', int((np.abs(d).max(1) > 1e-4).sum()), 'of', n, 'total', len(co))
