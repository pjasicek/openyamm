import bpy, sys, json, bmesh
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    vs = [v.co for v in bm.verts]
    mn = [min(v[i] for v in vs) for i in range(3)]; mx = [max(v[i] for v in vs) for i in range(3)]
    # components
    seen = set(); comps = []
    for v in bm.verts:
        if v.index in seen: continue
        stack = [v]; seen.add(v.index); c = []
        while stack:
            x = stack.pop(); c.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index); stack.append(y)
        cm = [sum(p.co[i] for p in c) / len(c) for i in range(3)]
        comps.append((len(c), [round(t, 3) for t in cm]))
    comps.sort(reverse=True)
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    print('STATS', o.name, 'verts', len(bm.verts), 'tris', tris, 'min', [round(x, 3) for x in mn], 'max',
          [round(x, 3) for x in mx], 'components', len(comps), comps[:12], 'nonmanifold_edges', nonman,
          'uv', len(o.data.uv_layers), 'mats', [m.name for m in o.data.materials if m])
