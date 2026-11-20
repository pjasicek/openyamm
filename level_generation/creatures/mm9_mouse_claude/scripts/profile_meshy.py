"""Meshy mouse profile along its length: per 0.01 y bin, x/z extents of the largest component (Meshy units).
Args: <glb>"""
import bpy, bmesh, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
o = next(o for o in bpy.data.objects if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.verts.ensure_lookup_table()
seen = set(); comps = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; seen.add(v.index); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
P = np.array([tuple(bm.verts[i].co) for i in comps[0]])
print('PROFILE zmin %.4f zmax %.4f' % (P[:, 2].min(), P[:, 2].max()))
for y in np.arange(P[:, 1].min(), P[:, 1].max(), 0.02):
    s = P[(P[:, 1] >= y) & (P[:, 1] < y + 0.02)]
    if len(s):
        print('PROFILE y %.3f n %4d x %.4f..%.4f z %.4f..%.4f' % (y, len(s), s[:, 0].min(), s[:, 0].max(), s[:, 2].min(), s[:, 2].max()))
