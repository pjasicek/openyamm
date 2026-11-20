"""Blend 'Body' (rest pose) -> npz V, F (triangulated), part. Args: <blend> <out npz>"""
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); o = bpy.data.objects['Body']
bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces)
V = np.array([(o.matrix_world @ v.co)[:] for v in bm.verts]); F = np.array([[v.index for v in f.verts] for f in bm.faces])
pl = bm.verts.layers.int.get('part'); part = np.array([v[pl] for v in bm.verts]) if pl else np.zeros(len(V), int)
np.savez(a[1], V=V, F=F, part=part); print('DUMPED', V.shape, F.shape)
