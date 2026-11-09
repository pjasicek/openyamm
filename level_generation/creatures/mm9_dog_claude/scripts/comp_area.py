"""Connected components of a GLB mesh with vertex count, surface area, boundary edges and bounds. Args: <glb>"""
import bpy, bmesh, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.verts.ensure_lookup_table()
    seen, comps = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        c, st = [], [v]; seen.add(v.index)
        while st:
            x = st.pop(); c.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index); st.append(y)
        comps.append(c)
    comps.sort(key=len, reverse=True)
    for c in comps[:8]:
        cs = set(c)
        faces = {f for v in c for f in v.link_faces}
        area = sum(f.calc_area() for f in faces)
        bnd = sum(1 for e in {e for v in c for e in v.link_edges} if len(e.link_faces) == 1)
        print('COMP %s n=%d area=%.5f boundary=%d min %s max %s' % (o.name, len(c), area, bnd,
              [round(min(v.co[i] for v in c), 3) for i in range(3)], [round(max(v.co[i] for v in c), 3) for i in range(3)]))
