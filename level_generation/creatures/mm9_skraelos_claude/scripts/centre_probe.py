"""Front/back extents (y) of MM9_Mesh and Body in 3 cm slices at given heights, |x| < 0.12. Args: <fit blend> <mm9 glb>"""
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
def V(o): M = np.array(o.matrix_world); c = np.array([v.co for v in o.data.vertices]); return c @ M[:3, :3].T + M[:3, 3]
b = V(bpy.data.objects['Body'])
old = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=a[1])
mm = max([o for o in bpy.data.objects if o not in old and o.type == 'MESH'], key=lambda o: len(o.data.vertices))
bpy.context.view_layer.update()
m = V(mm)
for z in [-0.1, -0.05, 0.0, 0.05, 0.1, 0.18, 0.25, 0.3, 0.36, 0.42, 0.45, 0.5, 0.56]:
    r = []
    for p in (m, b):
        s = p[(np.abs(p[:, 2] - z) < 0.03) & (np.abs(p[:, 0]) < 0.12)]
        r.append('%.3f..%.3f' % (s[:, 1].min(), s[:, 1].max()) if len(s) else '-')
    print('CPROBE z %.2f mm9 %s ours %s' % (z, r[0], r[1]))
