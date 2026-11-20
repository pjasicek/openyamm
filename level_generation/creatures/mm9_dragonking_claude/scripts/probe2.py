import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
mp = bpy.data.objects['MeshyPosed']
P = np.array([tuple(v.co) for v in mp.data.vertices])
for zlo in (12, 13, 14, 15, 16, 17):
    sel = (P[:, 2] > zlo) & (P[:, 2] < zlo + 1) & (P[:, 1] < 0)
    xs = np.sort(np.abs(P[sel, 0]))
    h, e = np.histogram(xs, bins=np.arange(0, 9, 0.5))
    print('z', zlo, list(h))
