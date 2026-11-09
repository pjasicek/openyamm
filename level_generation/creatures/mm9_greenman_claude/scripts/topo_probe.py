"""Boundary / non-manifold edge counts and loose parts of 'Body' in blends. Args: <blend> ..."""
import bpy, bmesh, sys
for f in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.open_mainfile(filepath=f)
    bm = bmesh.new(); bm.from_mesh(bpy.data.objects['Body'].data)
    bnd = sum(1 for e in bm.edges if e.is_boundary); nm = sum(1 for e in bm.edges if not e.is_manifold)
    seen = set(); parts = 0
    for v in bm.verts:
        if v in seen: continue
        parts += 1; st = [v]; seen.add(v)
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y not in seen: seen.add(y); st.append(y)
    print('TOPO', f.split('/')[-1], 'tris', sum(len(p.verts) - 2 for p in bm.faces), 'boundary', bnd, 'nonmanifold', nm, 'parts', parts)
