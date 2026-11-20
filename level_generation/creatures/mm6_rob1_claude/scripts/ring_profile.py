"""Per-angle top/bottom edge heights of the two Meshy rings (k4 upper, k3 lower) and the lips k0/k6."""
import bpy, os, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
m = next(o for o in bpy.data.objects if o.type == 'MESH')
co = np.array([tuple(m.matrix_world @ v.co) for v in m.data.vertices]); co[:, 2] -= co[:, 2].min()
lab = np.load(os.path.join(HERE, 'work', 'component_labels.npy'))
phi = np.degrees(np.arctan2(co[:, 0], -co[:, 1]))  # 0 = front (-Y), +-180 = back
r = np.hypot(co[:, 0], co[:, 1])
for k in (4, 3, 0, 6, 1, 11, 12):
    s = lab == k
    print('K', k, 'z', co[s, 2].min().round(3), co[s, 2].max().round(3), 'r', r[s].min().round(3), r[s].max().round(3))
    rows = []
    for a in range(-180, 180, 15):
        b = s & (phi >= a) & (phi < a + 15)
        if b.any():
            rows.append(f'{a:4d}:{co[b,2].min():.3f}-{co[b,2].max():.3f}')
    print('   ', ' '.join(rows))
