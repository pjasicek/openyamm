"""Clean the female Meshy return before the fit: Meshy joined the right braid to the sleeve with a thin thread (part 10) and left
a 3-vertex speck. Faces of the braid part outside the braid's width go; the speck goes. Args: <in glb> <out glb>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
o = next(x for x in bpy.data.objects if x.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
comp = {}
parts = []
for v in bm.verts:
    if v.index in comp: continue
    st = [v]; comp[v.index] = len(parts); ps = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in comp:
                comp[y.index] = len(parts); st.append(y); ps.append(y)
    parts.append(ps)
M = o.matrix_world
drop = []
for ps in parts:
    co = np.array([tuple(M @ v.co) for v in ps])
    if len(ps) < 8:
        drop += ps
    elif co[:, 0].min() < -0.2 and co[:, 0].max() > -0.04 and co[:, 2].max() > 0.3 and len(ps) < 400:   # the braid with the thread
        d = [v for v, c in zip(ps, co) if c[0] < -0.05]
        print('CLEAN thread verts', len(d), 'of', len(ps))
        drop += d
bmesh.ops.delete(bm, geom=drop, context='VERTS')
bm.to_mesh(o.data); bm.free()
for x in bpy.data.objects:
    x.select_set(x == o)
bpy.context.view_layer.objects.active = o
o.data.materials.clear()
bpy.ops.export_scene.gltf(filepath=a[1], use_selection=True, export_format='GLB', export_yup=True, export_materials='NONE', export_animations=False, export_skins=False, export_normals=False, export_texcoords=False)
print('CLEAN done', len(o.data.vertices))
