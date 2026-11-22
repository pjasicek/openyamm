"""Import the raw Smart Topology return, report size/triangles/pieces and render four clay views (review/raw_*.png).
Forward of the raw Meshy model is +Z in glTF -> -Y in Blender after import."""
import bpy, os, sys, bmesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v2/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = 'Dillo'
co = [v.co for v in mesh.data.vertices]
mn = [min(c[i] for c in co) for i in range(3)]; mx = [max(c[i] for c in co) for i in range(3)]
bm = bmesh.new(); bm.from_mesh(mesh.data)
tris = sum(len(f.verts) - 2 for f in bm.faces)
# connected pieces
seen = set(); pieces = []
for v in bm.verts:
    if v.index in seen: continue
    stack = [v]; seen.add(v.index); n = 0
    while stack:
        x = stack.pop(); n += 1
        for e in x.link_edges:
            o = e.other_vert(x)
            if o.index not in seen: seen.add(o.index); stack.append(o)
    pieces.append(n)
print('RAW verts', len(bm.verts), 'tris', tris, 'min', [round(x, 3) for x in mn], 'max', [round(x, 3) for x in mx])
print('PIECES', sorted(pieces, reverse=True)[:12], 'count', len(pieces))
cx = (mn[0] + mx[0]) / 2; cy = (mn[1] + mx[1]) / 2; cz = (mn[2] + mx[2]) / 2
s = max(mx[0] - mn[0], mx[1] - mn[1]) * 1.15
for name, (loc, tgt) in {'front': ((cx, cy - 5, cz), (cx, cy, cz)), 'side': ((cx - 5, cy, cz), (cx, cy, cz)),
                         'top': ((cx, cy, cz + 5), (cx, cy, cz)), 'quarter': ((cx - 3, cy - 3.5, cz + 2), (cx, cy, cz)),
                         'back': ((cx, cy + 5, cz), (cx, cy, cz))}.items():
    C.render(loc, tgt, s, os.path.join(HERE, 'review', f'raw2_{name}.png'), res=(700, 500), floor=False)
