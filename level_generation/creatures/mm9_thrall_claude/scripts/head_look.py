"""Diagnostics of the Meshy head parts: slices and normals. Args: <glb> <prefix>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
o = next(x for x in bpy.data.objects if x.type == 'MESH')
Mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = Mw
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = o.data
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
seen = set(); parts = []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen.add(v.index); ids = []
    while st:
        x = st.pop(); ids.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    parts.append(ids)
parts.sort(key=len, reverse=True)
for i, ids in enumerate(parts):
    s = set(ids)
    bd = sum(1 for e in bm.edges if e.is_boundary and e.verts[0].index in s)
    print('PART', i, len(ids), 'boundary', bd)
hair = set(parts[1]); skin = set(parts[0])
# slice the hair along x=0 and y=0: print profile of z vs y of hair verts near x=0
H = np.array([bm.verts[i].co[:] for i in parts[1]]); S = np.array([bm.verts[i].co[:] for i in parts[0]])
m = np.abs(H[:, 0]) < 0.02
o_ = np.argsort(H[m, 2])
print('HAIRX0', np.round(H[m][o_][::12], 3).tolist())
m = np.abs(S[:, 0]) < 0.02
o_ = np.argsort(S[m, 2])
print('SKINX0', np.round(S[m][o_][::14], 3).tolist())
