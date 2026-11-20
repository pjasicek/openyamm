"""Rest-pose cross-sections of the back of the skin shell (piece 0) to find the ponytail: per height, the vertices behind
the back surface (y beyond the back's own depth at that height). Args: -- <blend>"""
import bpy, sys, os
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(v.co) for v in me.vertices]); sk = co[pv == 0]
for z in np.arange(0.85, 1.75, 0.05):
    m = np.abs(sk[:, 2] - z) < 0.025
    s = sk[m]
    if not len(s):
        continue
    mid = s[np.abs(s[:, 0]) < 0.06]
    ys = np.sort(mid[:, 1])[::-1][:6] if len(mid) else []
    print('BACK z', round(z, 2), 'max y (|x|<6cm)', [round(float(y), 3) for y in ys], 'n', len(mid))
