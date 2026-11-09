"""Rest triangles of the right hand zone from a blend. Args: blend out.npz"""
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); me = bpy.data.objects['Body'].data
P = np.array([v.co[:] for v in me.vertices]); T = np.array([p.vertices[:] for p in me.polygons]); c = P[T].mean(1)
np.savez(a[1], T=P[T[(c[:, 0] < -0.45) & (c[:, 2] < 0.05) & (c[:, 2] > -0.6)]])
print('DUMPH done')
