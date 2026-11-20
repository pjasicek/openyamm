"""Rest bounds of every armour object (Arm_*) and the outermost top point of the pauldrons. Args: -- <blend>"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
for o in sorted([o for o in bpy.data.objects if o.name.startswith('Arm_')], key=lambda o: o.name):
    co = np.array([o.matrix_world @ v.co for v in o.data.vertices])
    print('BOUNDS', o.name, 'min', np.round(co.min(0), 3).tolist(), 'max', np.round(co.max(0), 3).tolist(), 'tris', len(o.data.polygons))
    if 'pauldron_' in o.name and '2' not in o.name:
        k = int(np.argmax(co[:, 2])); print('TOP', o.name, np.round(co[k], 3).tolist())
        for frac in (0.25, 0.5, 0.75):
            x0, x1 = co[:, 0].min(), co[:, 0].max(); xs = x0 + (x1 - x0) * frac
            m = np.abs(co[:, 0] - xs) < 0.02
            if m.any(): k = np.argmax(np.where(m, co[:, 2], -9)); print('TOPAT', o.name, round(float(xs), 3), np.round(co[k], 3).tolist())
