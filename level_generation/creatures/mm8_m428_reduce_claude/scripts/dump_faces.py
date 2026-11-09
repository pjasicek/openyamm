"""Per-face labels of the rest source (same order as dump_mesh.py): dominant bone name, mean u, connected piece ->
work/faces_info.npz. Usage: blender -b -P dump_faces.py"""
import os, bpy, collections, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
names = {g.index: g.name for g in o.vertex_groups}
vdom = []
for v in me.vertices:
    vdom.append({names[g.group]: g.weight for g in v.groups})
dom, umean = [], []
for t in me.loop_triangles:
    acc = collections.Counter()
    for vi in t.vertices:
        acc.update(vdom[vi])
    dom.append(acc.most_common(1)[0][0]); umean.append(np.mean([uv[l].uv[0] for l in t.loops]))
np.savez(os.path.join(HERE, 'work', 'faces_info.npz'), dom=np.array(dom), u=np.array(umean))
print('FACES', len(dom))
