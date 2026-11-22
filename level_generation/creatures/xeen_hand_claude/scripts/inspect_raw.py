"""Import the raw Smart Topology return, report size/triangles/pieces (with boxes) and render clay views
(review/raw_*.png). Forward of the raw Meshy model is +Z in glTF -> -Y in Blender after import."""
import bpy, os, sys, bmesh
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = 'Raw'
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
co = np.array([tuple(v.co) for v in bm.verts])
mn, mx = co.min(0), co.max(0)
tris = sum(len(f.verts) - 2 for f in bm.faces)
label = -np.ones(len(bm.verts), int); n = 0
for v in bm.verts:
    if label[v.index] >= 0: continue
    stack = [v]; label[v.index] = n
    while stack:
        x = stack.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if label[o.index] < 0: label[o.index] = n; stack.append(o)
    n += 1
print('RAW verts', len(bm.verts), 'tris', tris, 'min', np.round(mn, 3).tolist(), 'max', np.round(mx, 3).tolist())
sizes = np.bincount(label)
for i in np.argsort(-sizes)[:20]:
    c = co[label == i]
    print(f'PIECE {i} verts {len(c)} min {np.round(c.min(0), 3).tolist()} max {np.round(c.max(0), 3).tolist()}')
print('PIECES count', n)
bnd = sum(1 for e in bm.edges if e.is_boundary)
print('BOUNDARY edges', bnd)
c = (mn + mx) / 2; s = float((mx - mn).max()) * 1.15
for name, (d) in {'front': (0, -5, 0), 'side': (-5, 0, 0), 'top': (0, 0, 5), 'quarter': (-3, -3.5, 2),
                  'back': (0, 5, 0), 'under': (0, 0, -5), 'rside': (5, 0, 0)}.items():
    C.render(tuple(c + np.array(d)), tuple(c), s, os.path.join(HERE, 'review', f'raw_{name}.png'), res=(600, 450),
             floor=False)
