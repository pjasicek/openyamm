"""Soften PM8's waistband lip (M4 has no belt): Laplacian smoothing of positions in the waist band only (positions only).
Usage: blender -b --python belt_smooth.py -- in.blend out.blend z_lo z_hi iterations"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
src, dst = argv[0], argv[1]; zlo, zhi, it = float(argv[2]), float(argv[3]), int(argv[4])
bpy.ops.wm.open_mainfile(filepath=src)
o = bpy.data.objects['Body']; me = o.data
co = np.array([v.co for v in me.vertices])
z = co[:, 2]
fade = np.clip(np.minimum(z - zlo, zhi - z) / 0.03, 0, 1) * (np.abs(co[:, 0]) < 0.30)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
nbrs = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
p = co.copy()
for _ in range(it):
    q = p.copy()
    for i, nb in enumerate(nbrs):
        if fade[i] <= 0 or not nb:
            continue
        q[i] = p[i] + 0.5 * fade[i] * (p[nb].mean(0) - p[i])
    p = q
for v in me.vertices:
    v.co = Vector(p[v.index])
me.update(); bpy.ops.wm.save_as_mainfile(filepath=dst)
m = np.linalg.norm(p - co, axis=1); print('BELT', int((m > 1e-4).sum()), 'moved, max cm', round(float(m.max() * 100), 2))
np.save(dst.replace('.blend', '_move.npy'), np.concatenate([co, p - co], 1))
