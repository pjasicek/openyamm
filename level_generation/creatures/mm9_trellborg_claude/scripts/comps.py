"""Components of a Meshy GLB, Blender axes. Args: <glb>"""
import bpy, bmesh, sys
import numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
for o in [x for x in bpy.data.objects if x.type == 'MESH']:
    M = o.matrix_world
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    print('OBJ', o.name, len(bm.verts), len(bm.faces), 'boundary', sum(1 for e in bm.edges if e.is_boundary), 'nonman', sum(1 for e in bm.edges if not e.is_manifold))
    seen = set(); comps = []
    for v in bm.verts:
        if v in seen: continue
        st = [v]; seen.add(v); cc = [v]
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y not in seen: seen.add(y); st.append(y); cc.append(y)
        comps.append(cc)
    comps.sort(key=len, reverse=True)
    for i, c in enumerate(comps[:40]):
        q = np.array([(M @ v.co)[:] for v in c])
        print('COMP', i, len(c), np.round(q.mean(0), 3).tolist(), np.round(q.min(0), 3).tolist(), np.round(q.max(0), 3).tolist())
