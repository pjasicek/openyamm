"""Placement test: head parts on the fitted body, no join; prints sections. Args: <pose blend> <head blend> <out blend> s oy oz"""
import bpy, sys
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
POSE, HEAD, OUT = a[:3]; S, OY, OZ = float(a[3]), float(a[4]), float(a[5])
bpy.ops.wm.open_mainfile(filepath=POSE)
with bpy.data.libraries.load(HEAD) as (src, dst):
    dst.objects = [n for n in src.objects]
for o in dst.objects:
    bpy.context.scene.collection.objects.link(o)
    o.data.transform(Matrix.Translation((0, OY, OZ)) @ Matrix.Scale(S, 4))
b = bpy.data.objects['Body']
P = np.array([v.co[:] for v in b.data.vertices])
for z in np.arange(0.55, 1.16, 0.05):
    q = P[(np.abs(P[:, 2] - z) < 0.02) & (np.abs(P[:, 0]) < 0.33)]
    if len(q): print('BODY z', round(z, 2), 'x', np.round(np.abs(q[:, 0]).max(), 3), 'y', np.round(q[:, 1].min(), 3), np.round(q[:, 1].max(), 3))
for o in dst.objects:
    if o.name == 'Face':
        Q = np.array([v.co[:] for v in o.data.vertices])
        print('FACE bbox', Q.min(0).round(3), Q.max(0).round(3))
        for z in np.arange(0.55, 1.16, 0.05):
            q = Q[(np.abs(Q[:, 2] - z) < 0.02)]
            if len(q): print('HEAD z', round(z, 2), 'x', np.round(np.abs(q[:, 0]).max(), 3), 'y', np.round(q[:, 1].min(), 3), np.round(q[:, 1].max(), 3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('ASSEMBLED')
