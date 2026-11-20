"""Position-only fixes on the UV'd master (topology and UVs untouched, so the paints stay valid):
soles: everything of the feet below floor + band is compressed into [floor + 3 mm, floor + band] (Meshy's claws reached
9.8 cm under MM9's floor). Args: <in blend> <out blend>"""
import bpy, sys, numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Body']; me = o.data
F, BAND = -1.368, 0.08
P = np.array([v.co[:] for v in me.vertices])
m = (P[:, 2] < F + BAND) & (np.abs(P[:, 0]) > 0.08)
zmin = P[m, 2].min()
P[m, 2] = F + 0.003 + (P[m, 2] - zmin) * (BAND - 0.003) / (F + BAND - zmin)
for v, p in zip(me.vertices, P): v.co = Vector(p)
print('SOLES', int(m.sum()), 'from', round(zmin, 4))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
