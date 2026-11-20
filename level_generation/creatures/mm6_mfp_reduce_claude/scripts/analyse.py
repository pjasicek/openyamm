"""Source body analysis: bones, faces per dominant bone, connected components (welded mesh), UV range per region."""
import bpy, numpy as np, collections
src = bpy.data.objects['Body']; me = src.data; me.calc_loop_triangles()
names = {g.index: g.name for g in src.vertex_groups}
print('BONES', sorted(names.values()))
dom = []
for t in me.loop_triangles:
    acc = collections.Counter()
    for vi in t.vertices:
        for g in me.vertices[vi].groups: acc[names[g.group]] += g.weight
    dom.append(acc.most_common(1)[0][0])
print('FACES/BONE', collections.Counter(dom).most_common())
# components
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
comp = -np.ones(len(bm.faces), int); c = 0
for f in bm.faces:
    if comp[f.index] >= 0: continue
    st = [f]; comp[f.index] = c
    while st:
        g = st.pop()
        for e in g.edges:
            for h in e.link_faces:
                if comp[h.index] < 0: comp[h.index] = c; st.append(h)
    c += 1
sizes = np.bincount(comp)
print('COMPONENTS', c, 'sizes desc', sorted(sizes.tolist(), reverse=True)[:40])
uv = me.uv_layers.active.data
for k in range(c):
    fs = np.where(comp == k)[0]
    if len(fs) < 3: continue
    ctr = np.mean([bm.faces[i].calc_center_median()[:] for i in fs], axis=0)
    bones = collections.Counter(dom[i] for i in fs).most_common(2)
    print(f'  comp {k} faces {len(fs)} centre {np.round(ctr,3)} bones {bones}')
np.save('work/comp.npy', comp); np.save('work/dom.npy', np.array(dom))
