import bpy, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
m = next(o for o in bpy.data.objects if o.type == 'MESH')
co = np.array([tuple(m.matrix_world @ v.co) for v in m.data.vertices]); co[:, 2] -= co[:, 2].min()
lab = np.load(os.path.join(HERE, 'work', 'component_labels.npy'))
c = np.array([0, 0, 0.4239]); d = co - c; dist = np.linalg.norm(d, axis=1)
el = np.degrees(np.arcsin(d[:, 2] / dist)); back = np.degrees(np.arctan2(co[:, 0], co[:, 1]))
side = (np.abs(back) > 50) & (np.abs(back) < 130)
for k in (1, 4, 0, 3, 6, 2):
    s = (lab == k) & (side if k != 2 else True)
    print('K', k, 'n', s.sum())
    for e in range(-90, 91, 3):
        b = s & (el >= e) & (el < e + 3)
        if b.sum():
            print(f'   el {e:4d}: dist {dist[b].min():.4f}-{dist[b].max():.4f} n {b.sum()}')
