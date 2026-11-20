"""MPFB's bare hand is thin for a leather glove (MM9's fist is a mitt): the grafted hand is pushed out along its normals, fading to nothing at the cuff. Args: <in blend> <out blend>"""
import bpy, sys
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
s = np.zeros(len(me.vertices)); me.attributes['graft_s'].data.foreach_get('value', s)
h = np.zeros(len(me.polygons), int); me.attributes['hand'].data.foreach_get('value', h)
ids = np.unique(np.concatenate([list(p.vertices) for p in me.polygons if h[p.index]]))
N = np.array([v.normal[:] for v in me.vertices]); P = np.array([v.co[:] for v in me.vertices])
T = 0.0042
P[ids] += N[ids] * (T * np.clip(s[ids], 0, 1))[:, None]
for i in ids: me.vertices[int(i)].co = Vector(P[i])
me.update()
print('GLOVE', len(ids), 'verts', T)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
