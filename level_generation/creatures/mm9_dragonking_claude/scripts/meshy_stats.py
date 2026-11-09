"""Meshy GLB stats: faces, verts, bounds, connected components (welded). Args: <glb>"""
import bpy, bmesh, sys, json
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
o = next(o for o in bpy.data.objects if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
seen = set(); comps = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; seen.add(v.index); c = []
    while st:
        x = st.pop(); c.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    lo = [min(p.co[i] for p in c) for i in range(3)]; hi = [max(p.co[i] for p in c) for i in range(3)]
    comps.append((len(c), [round(x, 3) for x in lo], [round(x, 3) for x in hi]))
comps.sort(key=lambda c: -c[0])
cs = [v.co for v in bm.verts]
print('STATS ' + json.dumps({'faces': len(bm.faces), 'verts': len(bm.verts),
      'min': [round(min(c[i] for c in cs), 3) for i in range(3)], 'max': [round(max(c[i] for c in cs), 3) for i in range(3)],
      'components': comps[:25], 'n_components': len(comps), 'nonmanifold_edges': sum(1 for e in bm.edges if not e.is_manifold)}))
