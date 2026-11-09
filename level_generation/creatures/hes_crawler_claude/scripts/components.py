"""List connected components of the Meshy crawler: vertex count, centroid, principal axis endpoints, bbox.
Args: -- <glb relative to the project> (default meshy/smart_topology_v1/model_urls_glb.glb).
Writes work/components.json and work/component_labels.npy (labels per vertex of the imported, grounded mesh)."""
import bpy, bmesh, os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
src = os.path.join(HERE, args[0] if args else 'meshy/smart_topology_v1/model_urls_glb.glb')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
co = np.array([tuple(mesh.matrix_world @ v.co) for v in mesh.data.vertices]); zmin = co[:, 2].min(); co[:, 2] -= zmin
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
label = -np.ones(len(bm.verts), int); comps = []
for v in bm.verts:
    if label[v.index] >= 0: continue
    k = len(comps); st = [v]; label[v.index] = k; idx = []
    while st:
        x = st.pop(); idx.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if label[w.index] < 0: label[w.index] = k; st.append(w)
    comps.append(idx)
mesh.data.calc_loop_triangles()
tri = np.bincount(label[[t.vertices[0] for t in mesh.data.loop_triangles]], minlength=len(comps))
out = []
for k, idx in enumerate(comps):
    p = co[idx]; c = p.mean(0); u, s, vt = np.linalg.svd(p - c, full_matrices=False); ax = vt[0]
    t = (p - c) @ ax; a, b = c + ax * t.min(), c + ax * t.max()
    out.append({'k': k, 'n': len(idx), 'tris': int(tri[k]), 'c': c.round(3).tolist(), 'a': a.round(3).tolist(),
                'b': b.round(3).tolist(), 'min': p.min(0).round(3).tolist(), 'max': p.max(0).round(3).tolist(),
                'len': round(float(t.max() - t.min()), 3)})
os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
np.save(os.path.join(HERE, 'work', 'component_labels.npy'), label)
np.save(os.path.join(HERE, 'work', 'component_co.npy'), co)
json.dump({'zmin': float(zmin), 'bbox': [co.min(0).tolist(), co.max(0).tolist()], 'tris': int(tri.sum()),
           'components': out}, open(os.path.join(HERE, 'work', 'components.json'), 'w'), indent=1)
print('BBOX', co.min(0).round(3), co.max(0).round(3), 'TRIS', tri.sum(), 'COMPONENTS', len(comps))
for o in sorted(out, key=lambda o: -o['n']):
    print('COMP', o['k'], o['n'], o['tris'], o['c'], o['min'], o['max'])
