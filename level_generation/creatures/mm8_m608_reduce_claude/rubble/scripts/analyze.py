"""Rest-pose structure of work/source.blend Body: sharp faces, connected pieces with their dominant bones and sizes."""
import os, bpy, bmesh, numpy as np, collections
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data
sh = me.attributes.get('sharp_face'); sharp = np.array([d.value for d in sh.data]) if sh else np.zeros(len(me.polygons), bool)
print('faces', len(me.polygons), 'sharp', int(sharp.sum()))
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
seen = set(); comps = []
for f in bm.faces:
    if f.index in seen: continue
    stack = [f]; seen.add(f.index); cf = []
    while stack:
        g = stack.pop(); cf.append(g.index)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen: seen.add(h.index); stack.append(h)
    comps.append(cf)
names = [g.name for g in o.vertex_groups]
def dom(fs):
    c = collections.Counter()
    for fi in fs:
        for vi in me.polygons[fi].vertices:
            for g in me.vertices[vi].groups:
                if g.weight > 1e-4: c[names[g.group]] += g.weight
    return c.most_common(3)
comps.sort(key=len, reverse=True)
print('components', len(comps))
for cf in comps[:25]:
    vs = {vi for fi in cf for vi in me.polygons[fi].vertices}; co = np.array([me.vertices[v].co[:] for v in vs])
    print(len(cf), 'sharp', int(sharp[cf].sum()), 'z %.2f-%.2f x %.2f..%.2f' % (co[:,2].min(), co[:,2].max(), co[:,0].min(), co[:,0].max()), [(n, round(w, 1)) for n, w in dom(cf)])
sizes = collections.Counter(min(len(c), 999) // 50 * 50 for c in comps[25:]); print('small comps by size bin', sorted(sizes.items()))
# mixed arm/torso faces
arm = ('UpperArm_', 'Forearm_', 'Hand_'); torso = {'Chest', 'Waist', 'Neck', 'Head'}
mixed = 0
for p in me.polygons:
    ns = {names[g.group] for vi in p.vertices for g in me.vertices[vi].groups if g.weight > 1e-6}
    if any(n.startswith(arm) for n in ns) and ns & torso: mixed += 1
print('arm-torso mixed faces', mixed)
print('groups', names)
