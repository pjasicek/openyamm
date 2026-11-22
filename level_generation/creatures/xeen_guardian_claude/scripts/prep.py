"""Import the Smart Topology return, scale the skull to HEIGHT (cranium top to chin), centre x/y, ground it (min z 0),
forward -Y (the raw return already faces -Y). Lists the connected pieces with their boxes and saves the piece labels
(work/pieces.npy, vertex order of the saved mesh). Saves work/clean_v1.blend."""
import bpy, os, bmesh
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEIGHT = 0.80
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in mesh.data.vertices])
mn, mx = co.min(0), co.max(0)
k = HEIGHT / (mx[2] - mn[2])
off = Vector(((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]))
for v in mesh.data.vertices:
    v.co = (v.co - off) * k
mesh.name = mesh.data.name = 'Skull'
for p in mesh.data.polygons:
    p.use_smooth = True
mesh.data.materials.clear()
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
label = -np.ones(len(bm.verts), int); pieces = []
for v in bm.verts:
    if label[v.index] >= 0:
        continue
    stack = [v]; label[v.index] = len(pieces); idx = []
    while stack:
        x = stack.pop(); idx.append(x.index)
        for e in x.link_edges:
            o = e.other_vert(x)
            if label[o.index] < 0:
                label[o.index] = len(pieces); stack.append(o)
    pieces.append(idx)
co = np.array([tuple(v.co) for v in mesh.data.vertices])
order = sorted(range(len(pieces)), key=lambda i: -len(pieces[i]))
remap = np.empty(len(pieces), int); remap[order] = np.arange(len(pieces))
label = remap[label]
for i in range(len(pieces)):
    c = co[label == i]
    tri = sum(len(f.verts) - 2 for f in bm.faces if label[f.verts[0].index] == i)
    print(f'PIECE {i} verts {len(c)} tris {tri} min {np.round(c.min(0), 3).tolist()} max {np.round(c.max(0), 3).tolist()}')
np.save(os.path.join(HERE, 'work', 'pieces.npy'), label)
print('SIZE', np.round(co.max(0) - co.min(0), 3).tolist(), 'factor', round(k, 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
