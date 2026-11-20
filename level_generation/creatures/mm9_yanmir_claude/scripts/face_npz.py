"""Face shell and eyes in figure space, for the head-only voxel closure. Args: <head blend> <out npz>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
S, OY, OZ = 0.47, 0.027, 1.098
bpy.ops.wm.open_mainfile(filepath=HEAD)
co = []; tri = []; pa = []; o_ = 0
for nm, pid in (('Face', 10), ('Eyes', 13)):
    bm = bmesh.new(); bm.from_mesh(bpy.data.objects[nm].data); bmesh.ops.triangulate(bm, faces=bm.faces); bm.verts.ensure_lookup_table()
    c = np.array([v.co[:] for v in bm.verts]) * S + [0, OY, OZ]
    t = np.array([[v.index for v in f.verts] for f in bm.faces])
    co.append(c); tri.append(t + o_); pa.append(np.full(len(c), pid)); o_ += len(c); bm.free()
np.savez(OUT, co=np.vstack(co), tri=np.vstack(tri), part=np.concatenate(pa)); print('NPZ', o_)
