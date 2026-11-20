"""Dump a GLB's mesh to npz with component ids. Args: glb npz"""
import bpy, bmesh, sys
import numpy as np
glb, npz = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=glb)
ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
me = ob.data; me.transform(ob.matrix_world)
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bmesh.ops.triangulate(bm, faces=bm.faces); bm.verts.ensure_lookup_table(); bm.verts.index_update()
co = np.array([tuple(v.co) for v in bm.verts]); tri = np.array([[v.index for v in f.verts] for f in bm.faces])
cid = -np.ones(len(co), int); k = 0
for v in bm.verts:
    if cid[v.index] >= 0: continue
    st = [v]; cid[v.index] = k
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if cid[y.index] < 0: cid[y.index] = k; st.append(y)
    k += 1
bd = np.array([[e.verts[0].index, e.verts[1].index] for e in bm.edges if len(e.link_faces) != 2]).reshape(-1, 2)
np.savez(npz, co=co, tri=tri, cid=cid, bd=bd)
print('DUMP', len(co), len(tri), k, len(bd))
