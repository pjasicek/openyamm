"""Dominant bone per rest triangle of work/source.blend (same order as dump_mesh.py) -> work/face_bone.npy (names)."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data; me.calc_loop_triangles()
names = {g.index: g.name for g in o.vertex_groups}
vw = [{names[g.group]: g.weight for g in v.groups} for v in me.vertices]
out = []
for t in me.loop_triangles:
    acc = {}
    for vi in t.vertices:
        for k, w in vw[vi].items():
            acc[k] = acc.get(k, 0) + w
    out.append(max(acc, key=acc.get))
np.save(os.path.join(HERE, 'work', 'face_bone.npy'), np.array(out)); print('BONES', len(out))
