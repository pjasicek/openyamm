import bpy, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
m = next(o for o in bpy.data.objects if o.type == 'MESH')
co = np.array([tuple(m.matrix_world @ v.co) for v in m.data.vertices]); co[:, 2] -= co[:, 2].min()
lab = np.load(os.path.join(HERE, 'work', 'component_labels.npy'))
phi = np.degrees(np.arctan2(co[:, 0], -co[:, 1]))
r = np.hypot(co[:, 0], co[:, 1])
for k, f in ((4, 'max'), (3, 'min'), (0, 'max'), (6, 'min')):
    s = lab == k
    for centre in (0, 180):
        rows = []
        for a in range(-45, 46, 3):
            ang = ((phi - centre - a + 180) % 360) - 180
            b = s & (np.abs(ang) < 1.5) & (r > 0.3)
            if b.any():
                rows.append(f'{a}:{getattr(co[b,2], f)():.3f}')
        print('K', k, centre, ' '.join(rows))
# what is k0 near the axis
s = (lab == 0) & (r < 0.3); print('k0 inner', s.sum(), co[s, 2].min(), co[s, 2].max())
s = (lab == 6) & (r < 0.3); print('k6 inner', s.sum(), co[s, 2].min(), co[s, 2].max())
