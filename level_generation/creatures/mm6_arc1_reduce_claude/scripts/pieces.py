"""Connected components of the welded source body (work/source.blend) with face count, dominant bone and centre;
-> work/components.npy (component id per face). Prints components up to 400 faces and the large ones."""
import bpy, bmesh, numpy as np
from collections import Counter
src = bpy.data.objects['Body']; me = src.data
names = {g.index: g.name for g in src.vertex_groups}
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
comp = -np.ones(len(bm.faces), int); c = 0
for f in bm.faces:
    if comp[f.index] >= 0: continue
    stack = [f]; comp[f.index] = c
    while stack:
        g = stack.pop()
        for e in g.edges:
            for h in e.link_faces:
                if comp[h.index] < 0: comp[h.index] = c; stack.append(h)
    c += 1
np.save('work/components.npy', comp)
dom = []
for v in me.vertices:
    dom.append(names[max(v.groups, key=lambda g: g.weight).group] if len(v.groups) else '-')
for k in range(c):
    fs = np.where(comp == k)[0]
    vs = {i for p in fs for i in me.polygons[p].vertices}
    bone = Counter(dom[i] for i in vs).most_common(2)
    ctr = np.mean([me.vertices[i].co for i in vs], axis=0)
    print('COMP', k, len(fs), bone, np.round(ctr, 3).tolist())
