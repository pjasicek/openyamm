"""Import a Smart Topology return, scale it (largest extent -> <size> m), ground it (min z 0), centre x/y, list its
connected pieces (box, size, flatness) and save work/<name>_clean.blend + work/<name>_pieces.npz.
Usage: pieces.py <job> <name> <largest extent m>"""
import bpy, os, sys, bmesh
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
job, name, size = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, f'meshy/{job}/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh: bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([v.co[:] for v in mesh.data.vertices])
mn, mx = co.min(0), co.max(0)
k = float(size) / (mx - mn).max()
off = np.array([(mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]])
for v in mesh.data.vertices:
    v.co = Vector((np.array(v.co[:]) - off) * k)
mesh.name = mesh.data.name = name.capitalize()
mesh.data.materials.clear()
for p in mesh.data.polygons: p.use_smooth = True
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
label = -np.ones(len(bm.verts), int); n = 0
for v in bm.verts:
    if label[v.index] >= 0: continue
    st = [v]; label[v.index] = n
    while st:
        x = st.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if label[o.index] < 0: label[o.index] = n; st.append(o)
    n += 1
co = np.array([v.co[:] for v in bm.verts])
order = np.argsort([-(label == i).sum() for i in range(n)])
remap = np.empty(n, int); remap[order] = np.arange(n); label = remap[label]
for i in range(n):
    c = co[label == i]
    ext = c.max(0) - c.min(0)
    sv = np.linalg.svd(c - c.mean(0), compute_uv=False) if len(c) > 3 else np.zeros(3)
    print(f'PIECE {i:2d} n {len(c):4d} c ({c.mean(0)[0]:+.3f},{c.mean(0)[1]:+.3f},{c.mean(0)[2]:.3f}) '
          f'ext ({ext[0]:.3f},{ext[1]:.3f},{ext[2]:.3f}) flat {sv[2] / max(sv[0], 1e-9):.3f}')
np.savez(os.path.join(HERE, 'work', f'{name}_pieces.npz'), co=co, label=label)
print('SIZE', name, (co.max(0) - co.min(0)).round(3), 'factor', round(k, 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', f'{name}_clean.blend'))
