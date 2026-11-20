"""Raw Meshy return: connected components (vertex count, bbox, centroid) and workbench views along the axes.
Writes work/raw_components.json and review/raw/<view>.png."""
import bpy, bmesh, os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_hdr as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/geometry_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH'); mesh.name = 'Raw'
co = np.array([tuple(mesh.matrix_world @ v.co) for v in mesh.data.vertices])
print('TRIS', sum(len(p.vertices) - 2 for p in mesh.data.polygons), 'VERTS', len(co))
print('BBOX', co.min(0).round(3).tolist(), co.max(0).round(3).tolist())
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
label = -np.ones(len(bm.verts), int); comps = []
for v in bm.verts:
    if label[v.index] >= 0:
        continue
    k = len(comps); st = [v]; label[v.index] = k; idx = []
    while st:
        x = st.pop(); idx.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if label[w.index] < 0:
                label[w.index] = k; st.append(w)
    comps.append(idx)
out = []
for k, idx in enumerate(comps):
    p = co[idx]
    out.append({'k': k, 'n': len(idx), 'min': p.min(0).round(3).tolist(), 'max': p.max(0).round(3).tolist(),
                'c': p.mean(0).round(3).tolist()})
os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
np.save(os.path.join(HERE, 'work', 'raw_labels.npy'), label)
json.dump(out, open(os.path.join(HERE, 'work', 'raw_components.json'), 'w'), indent=1)
for o in sorted(out, key=lambda o: -o['n'])[:40]:
    print('COMP', o)
c = (co.min(0) + co.max(0)) / 2; s = float((co.max(0) - co.min(0)).max()) * 1.15
os.makedirs(os.path.join(HERE, 'review', 'raw'), exist_ok=True)
for name, d in (('px', (1, 0, 0)), ('nx', (-1, 0, 0)), ('py', (0, 1, 0)), ('ny', (0, -1, 0)), ('pz', (0, 0, 1)),
                ('nz', (0, 0, -1)), ('q', (0.6, -0.6, 0.5))):
    loc = c + np.array(d) * 3
    C.render_ortho(loc.tolist(), c.tolist(), s, os.path.join(HERE, 'review', 'raw', name + '.png'), res=(600, 450))
