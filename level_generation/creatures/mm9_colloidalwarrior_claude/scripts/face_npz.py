"""Face shell in figure space, for the head-only voxel closure (colloidal warrior, from mm9_bigfoot_claude). Scale S, the back half pressed
(BACK) so the throat cylinder stays inside the hunched back, offset (0, OY, OZ): head top at MM9's 1.0 m, eye width MM9's.
Args: <head blend> <out npz>"""
import bpy, bmesh, sys, os
import numpy as np
HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
S, OY, OZ, BACK = [float(os.environ.get(k, d)) for k, d in (('S', 0.8), ('OY', 0.04), ('OZ', 0.654), ('BACK', 0.75))]
bpy.ops.wm.open_mainfile(filepath=HEAD)
bm = bmesh.new(); bm.from_mesh(bpy.data.objects['Face'].data); bmesh.ops.triangulate(bm, faces=bm.faces); bm.verts.ensure_lookup_table()
c = np.array([v.co[:] for v in bm.verts])
c[:, 1] = np.where(c[:, 1] > 0, c[:, 1] * BACK, c[:, 1])
c = c * S + [0, OY, OZ]
t = np.array([[v.index for v in f.verts] for f in bm.faces])
np.savez(OUT, co=c, tri=t, part=np.full(len(c), 10)); print('NPZ', len(c), c.min(0).round(3), c.max(0).round(3))
