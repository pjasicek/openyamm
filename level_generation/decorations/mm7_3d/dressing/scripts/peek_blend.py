"""Report objects of a .blend: name, triangles, loose pieces, materials and images, bounds (map units).
Usage: blender -b <file.blend> --python peek_blend.py"""
import bpy
import bmesh
from mathutils import Vector
for o in bpy.data.objects:
    if o.type != 'MESH':
        print('OBJ', o.name, o.type); continue
    bm = bmesh.new(); bm.from_mesh(o.data)
    bm.verts.ensure_lookup_table()
    seen = set(); pieces = 0
    for v in bm.verts:
        if v.index in seen: continue
        pieces += 1; stack = [v]; seen.add(v.index)
        while stack:
            w = stack.pop()
            for e in w.link_edges:
                x = e.other_vert(w)
                if x.index not in seen: seen.add(x.index); stack.append(x)
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = [min(p[i] for p in pts) * 81.7 for i in range(3)]; hi = [max(p[i] for p in pts) * 81.7 for i in range(3)]
    imgs = []
    for m in o.data.materials:
        if m and m.node_tree:
            imgs += [n.image.filepath for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
    print('OBJ', o.name, 'tris', tris, 'pieces', pieces, 'mats', [m.name for m in o.data.materials if m], imgs,
          'uv', [l.name for l in o.data.uv_layers], 'bounds', [round(x, 1) for x in lo], [round(x, 1) for x in hi])
