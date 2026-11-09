"""List connected components of the Meshy eye: vertex count, centroid, principal axis endpoints."""
import bpy, bmesh, os, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
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
out = []
for k, idx in enumerate(comps):
    p = co[idx]; c = p.mean(0); u, s, vt = np.linalg.svd(p - c, full_matrices=False); ax = vt[0]
    t = (p - c) @ ax; a, b = c + ax * t.min(), c + ax * t.max()
    out.append({'k': k, 'n': len(idx), 'c': c.round(3).tolist(), 'a': a.round(3).tolist(), 'b': b.round(3).tolist(),
                'len': round(float(t.max() - t.min()), 3), 'thick': round(float(s[1] / np.sqrt(len(idx))), 3)})
np.save(os.path.join(HERE, 'work', 'component_labels.npy'), label)
json.dump({'zmin': float(zmin), 'components': out}, open(os.path.join(HERE, 'work', 'components.json'), 'w'), indent=1)
for o in sorted(out, key=lambda o: -o['n']):
    print('COMP', o)
