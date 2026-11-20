"""Dominant bone per rest-mesh triangle (same order as dump_mesh.py loop triangles) -> work/face_bones.npz
(names, index per face)."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data; me.calc_loop_triangles()
names = [g.name for g in o.vertex_groups]
W = np.zeros((len(me.vertices), len(names)), np.float32)
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
tri = np.array([t.vertices[:] for t in me.loop_triangles])
dom = W[tri].sum(1).argmax(1)
np.savez(os.path.join(HERE, 'work', 'face_bones.npz'), names=np.array(names), dom=dom)
print('FACEBONES', len(dom))
