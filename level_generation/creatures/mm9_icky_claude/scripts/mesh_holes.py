"""Report boundary loops and non-manifold edges of an object. Args: blend object"""
import bpy, bmesh, sys, json
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
o = bpy.data.objects[argv[1]]
bm = bmesh.new(); bm.from_mesh(o.data)
be = [e for e in bm.edges if e.is_boundary]
seen = set(); loops = []
for e in be:
    if e.index in seen:
        continue
    st = [e]; seen.add(e.index); comp = []
    while st:
        x = st.pop(); comp.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y.index not in seen:
                    seen.add(y.index); st.append(y)
    vs = {v for x in comp for v in x.verts}
    c = sum((v.co for v in vs), type(next(iter(vs)).co)()) / len(vs)
    loops.append((len(comp), [round(x, 3) for x in c]))
nm = [e for e in bm.edges if len(e.link_faces) > 2]
print('HOLES ' + json.dumps({'loops': sorted(loops, reverse=True)[:30], 'nonmanifold': [[round(x, 3) for x in (e.verts[0].co)] for e in nm][:10]}))
