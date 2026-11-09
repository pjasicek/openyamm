"""Head topology check of a runtime or export GLB (2026-10-30 face fix): positions welded (glTF splits vertices at
UV seams), then per loose part above the neck: open boundary loops (size and centre), non-manifold edges, and edges
whose two faces disagree in winding (a flipped face). Args: -- <glb> <neck z in GLB metres, y up> [json out]"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
glb, zc = a[0], float(a[1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
ob = max((o for o in bpy.data.objects if o.type == 'MESH' and 'LOD' not in o.name and 'Shadow' not in o.name),
         key=lambda o: len(o.data.polygons))
bm = bmesh.new(); bm.from_mesh(ob.data); bm.transform(ob.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = cid; st.append(y)
    cid += 1
rep = {'glb': glb, 'faces': len(bm.faces), 'parts': []}
for k in range(cid):
    vs = [v for v in bm.verts if comp[v.index] == k]
    z = np.array([v.co.z for v in vs])
    if np.median(z) < zc:
        continue
    es = [e for e in bm.edges if comp[e.verts[0].index] == k]
    bnd = [e for e in es if e.is_boundary]
    nonman = sum(1 for e in es if len(e.link_faces) > 2)
    flip = 0
    for e in es:
        if len(e.link_faces) != 2:
            continue
        d = []
        for f in e.link_faces:
            ids = [v.index for v in f.verts]; i = ids.index(e.verts[0].index)
            d.append(ids[(i + 1) % len(ids)] == e.verts[1].index)
        flip += d[0] == d[1]
    seen, loops = set(), []
    for e in bnd:
        if e.index in seen:
            continue
        lp, st = [], [e]
        while st:
            x = st.pop()
            if x.index in seen:
                continue
            seen.add(x.index); lp.append(x)
            for v in x.verts:
                st += [y for y in v.link_edges if y.is_boundary and y.index not in seen]
        c = np.mean([tuple(v.co) for x in lp for v in x.verts], 0)
        loops.append({'edges': len(lp), 'centre': [round(float(t), 3) for t in c]})
    rep['parts'].append({'part': k, 'faces': sum(1 for f in bm.faces if comp[f.verts[0].index] == k),
                         'boundary_loops': sorted(loops, key=lambda l: -l['edges']), 'nonmanifold_edges': nonman,
                         'flipped_edges': int(flip)})
print('HEADTOPO', json.dumps(rep))
if len(a) > 2:
    json.dump(rep, open(a[2], 'w'), indent=1)
