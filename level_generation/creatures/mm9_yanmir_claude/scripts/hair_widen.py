"""The back of the head (the coordinator: a smooth pale column above the mantle; MM9's hair is a broad block down to the shoulders).
The head set's hair behind the ears widens toward its lower edge: x scaled by up to 1 + WIDEN (full below z 1.00, none above z 1.17,
so the crown's band keeps its fit), pushed back a little; ears and face stay (y > 0.02 ramp). Vertex moves only: topology and UVs stay
(the paint belongs to work/uv_v1.blend). Args: <in blend> <out blend> [widen]"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]; WIDEN = float(a[2]) if len(a) > 2 else 0.22
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
mat = np.zeros(len(me.polygons), int); me.attributes['mat'].data.foreach_get('value', mat)
pa = np.zeros(len(me.vertices), int); me.attributes['part'].data.foreach_get('value', pa)
hv = np.zeros(len(me.vertices), bool)
for p in me.polygons:
    if mat[p.index] == 2: hv[list(p.vertices)] = True
hv &= pa == 0
P = np.array([v.co[:] for v in me.vertices])
def ss(x, a_, b_):
    t = np.clip((x - a_) / (b_ - a_), 0, 1); return t * t * (3 - 2 * t)
w = hv * ss(P[:, 1], 0.02, 0.07) * (1 - ss(P[:, 2], 1.00, 1.17))
Q = P.copy(); Q[:, 0] *= 1 + WIDEN * w; Q[:, 1] += 0.012 * w
for v, q in zip(me.vertices, Q): v.co = q
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HAIR widened', int((w > 0.01).sum()), 'verts, max x', round(float(np.abs(Q[hv, 0]).max()), 3), 'was', round(float(np.abs(P[hv, 0]).max()), 3))
