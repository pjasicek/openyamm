"""Import the Smart Topology return, scale to the Giant Toad's size (head top 0.85 m sitting), ground it (min z 0),
centre x/y, forward -Y. Lists the connected pieces with their boxes. Saves work/clean_v1.blend."""
import bpy, os, bmesh
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEIGHT = 0.85
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = [v.co.copy() for v in mesh.data.vertices]
mn = Vector([min(c[i] for c in co) for i in range(3)]); mx = Vector([max(c[i] for c in co) for i in range(3)])
k = HEIGHT / (mx.z - mn.z)
off = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
for v in mesh.data.vertices:
    v.co = (v.co - off) * k
mesh.name = mesh.data.name = 'Toad'
for p in mesh.data.polygons:
    p.use_smooth = True
mesh.data.materials.clear()
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
seen = set(); pieces = []
for v in bm.verts:
    if v.index in seen: continue
    stack = [v]; seen.add(v.index); idx = []
    while stack:
        x = stack.pop(); idx.append(x.index)
        for e in x.link_edges:
            o = e.other_vert(x)
            if o.index not in seen: seen.add(o.index); stack.append(o)
    pieces.append(idx)
pieces.sort(key=len, reverse=True)
for i, idx in enumerate(pieces):
    c = [bm.verts[j].co for j in idx]
    a = [round(min(p[d] for p in c), 3) for d in range(3)]; b = [round(max(p[d] for p in c), 3) for d in range(3)]
    print(f'PIECE {i} verts {len(idx)} min {a} max {b}')
print('SIZE', [round((mx[i] - mn[i]) * k, 3) for i in range(3)], 'factor', round(k, 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
