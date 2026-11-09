"""Per-face labels for the region budgets, in dump_mesh.py triangle order (loop_triangles of work/source.blend Body):
dominant bone per face -> work/face_bone.json, rest-pose face centres -> work/face_centre.npy."""
import os, bpy, json, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects['Body']; me = src.data; me.calc_loop_triangles()
names = {g.index: g.name for g in src.vertex_groups}
acc = []
for t in me.loop_triangles:
    w = {}
    for vi in t.vertices:
        for g in me.vertices[vi].groups:
            w[g.group] = w.get(g.group, 0) + g.weight
    acc.append(names[max(w, key=w.get)] if w else '')
cen = np.array([sum((me.vertices[v].co for v in t.vertices), me.vertices[0].co * 0) / 3 for t in me.loop_triangles])
json.dump(acc, open(os.path.join(HERE, 'work/face_bone.json'), 'w'))
np.save(os.path.join(HERE, 'work/face_centre.npy'), cen)
from collections import Counter
print('BONES', Counter(n.split('_')[0] if n.startswith('Feather') else n for n in acc).most_common())
