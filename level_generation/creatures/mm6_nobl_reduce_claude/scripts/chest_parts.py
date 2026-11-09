"""List the connected pieces of the source mesh and the reduced pick in the chest/capelet area (clasp, studs, necklace):
triangles, bounding box, dominant bones. Usage: blender -b -P chest_parts.py"""
import os, bpy, bmesh
from collections import Counter
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_facecape.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
for name in ('Body', 'Cand_62'):
    o = bpy.data.objects[name]; mw = o.matrix_world; names = {g.index: g.name for g in o.vertex_groups}
    bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    seen, parts = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            x = stack.pop(); comp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index); stack.append(y)
        parts.append(comp)
    print('PIECES', name, len(parts))
    for comp in sorted(parts, key=len, reverse=True):
        pts = [mw @ x.co for x in comp]
        lo = [min(p[k] for p in pts) for k in range(3)]; hi = [max(p[k] for p in pts) for k in range(3)]
        if hi[2] < 1.15 or lo[2] > 1.5 or len(comp) > 3000:
            continue
        faces = {f.index for x in comp for f in x.link_faces}
        bones = Counter(names[max(o.data.vertices[x.index].groups, key=lambda g: g.weight).group]
                        for x in comp if o.data.vertices[x.index].groups)
        print('PART', name, len(comp), 'v', len(faces), 'f', [round(c, 3) for c in lo], [round(c, 3) for c in hi], bones.most_common(3))
