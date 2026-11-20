"""Connected components of a GLB mesh with bboxes (Blender coords). Args: <glb>"""
import bpy, bmesh, sys
import numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
o = next(x for x in bpy.data.objects if x.type == 'MESH')
bpy.context.view_layer.objects.active = o; o.select_set(True)
o.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.verts.ensure_lookup_table()
seen = set(); out = []
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cur = []
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y)
    q = np.array([x.co[:] for x in cur]); out.append((len(cur), q.min(0).round(3), q.max(0).round(3), sum(1 for x in cur for e in x.link_edges if e.is_boundary) // 2))
for r in sorted(out, key=lambda r: -r[0]): print('COMP', r[0], r[1], r[2], 'boundary edges', r[3])
