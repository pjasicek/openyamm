"""Diagnostic: the source Wyrm's separate pieces (centre, size, material, dominant bone, triangles)."""
import os, bmesh, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source_snapshot.blend'))
o = bpy.data.objects['Wyrm']
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
names = {g.index: g.name for g in o.vertex_groups}
seen = set(); comps = []
for v in bm.verts:
    if v.index in seen: continue
    stack = [v]; comp = []; seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x)
        for e in x.link_edges:
            w = e.other_vert(x)
            if w.index not in seen: seen.add(w.index); stack.append(w)
    comps.append(comp)
comps.sort(key=len, reverse=True)
for i, comp in enumerate(comps):
    cs = [v.co for v in comp]
    lo = Vector([min(c[k] for c in cs) for k in range(3)]); hi = Vector([max(c[k] for c in cs) for k in range(3)])
    faces = {f for v in comp for f in v.link_faces}
    mats = {o.data.materials[f.material_index].name for f in faces}
    w = {}
    for v in comp:
        for g in o.data.vertices[v.index].groups:
            w[names[g.group]] = w.get(names[g.group], 0) + g.weight
    top = sorted(w.items(), key=lambda x: -x[1])[:2]
    print('PIECE', i, len(comp), 'verts', len(faces), 'faces', 'centre', [round(x, 3) for x in (lo + hi) / 2],
          'size', [round(x, 3) for x in hi - lo], mats, [(n, round(x, 1)) for n, x in top])
