"""Raw Smart Topology returns: size, triangles, pieces and clay views. Usage: inspect_raw.py <job> <name>"""
import bpy, os, sys, bmesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
job, name = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, f'meshy/{job}/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh: bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = 'Raw'
co = [v.co for v in mesh.data.vertices]
mn = [min(c[i] for c in co) for i in range(3)]; mx = [max(c[i] for c in co) for i in range(3)]
bm = bmesh.new(); bm.from_mesh(mesh.data)
seen = set(); pieces = []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen.add(v.index); n = 0
    while st:
        x = st.pop(); n += 1
        for e in x.link_edges:
            o = e.other_vert(x)
            if o.index not in seen: seen.add(o.index); st.append(o)
    pieces.append(n)
print('RAW', name, 'tris', sum(len(f.verts) - 2 for f in bm.faces), 'min', [round(x, 3) for x in mn], 'max', [round(x, 3) for x in mx])
print('PIECES', name, sorted(pieces, reverse=True)[:14], 'count', len(pieces))
cx = (mn[0] + mx[0]) / 2; cy = (mn[1] + mx[1]) / 2; cz = (mn[2] + mx[2]) / 2
s = max(mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]) * 1.1
for v, (loc, tgt) in {'front': ((cx, cy - 5, cz), (cx, cy, cz)), 'side': ((cx + 5, cy, cz), (cx, cy, cz)),
                      'top': ((cx, cy, cz + 5), (cx, cy, cz)), 'quarter': ((cx - 3, cy - 3.5, cz + 2), (cx, cy, cz))}.items():
    C.render(loc, tgt, s, os.path.join(HERE, 'review', f'raw_{name}_{v}.png'), res=(500, 400), floor=False)
