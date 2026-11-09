"""Map the dragon's lip faces (reweight_mouth.py 'lip': faces spanning the mouth plane, which open into the mouth
interior when the MM9 jaw drops) onto a red mouth patch in a free corner of the atlas: u runs front -> back along
the snout, v from the lower lip (bottom of the patch) to the upper lip (top). compose_dragon.py paints the patch.
Args: <in blend> <out blend> <patch json>"""
import bpy, sys, json
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
PATCH = (0.003, 0.966, 0.031, 0.031)   # u0, v0, width, height (UV units; 64 px at 2K, top-left corner)
bpy.ops.wm.open_mainfile(filepath=argv[0])
ob = bpy.data.objects['Body']; me = ob.data
lip = me.attributes['lip']
uv = me.uv_layers.active.data
faces = [p for p in me.polygons if lip.data[p.index].value]
ys = np.array([me.vertices[i].co.y for p in faces for i in p.vertices])
zs = np.array([me.vertices[i].co.z for p in faces for i in p.vertices])
y0, y1, z0, z1 = ys.min(), ys.max(), zs.min(), zs.max()
u0, v0, w, h = PATCH
m = 0.12
for p in faces:
    for li, vi in zip(p.loop_indices, p.vertices):
        co = me.vertices[vi].co
        fu = (co.y - y0) / max(y1 - y0, 1e-6)
        fv = (co.z - z0) / max(z1 - z0, 1e-6)
        uv[li].uv = (u0 + w * (m + (1 - 2 * m) * fu), v0 + h * (m + (1 - 2 * m) * fv))
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
json.dump({'patch_uv': PATCH, 'faces': len(faces)}, open(argv[2], 'w'))
print('MOUTHUV', len(faces))
