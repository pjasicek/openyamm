"""Dump an object's vertices (world) and triangles to npz. Args: <blend> <object> <out npz>"""
import bpy, bmesh, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); o = bpy.data.objects[a[1]]
bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces); bm.verts.ensure_lookup_table()
M = np.array(o.matrix_world); V = np.array([v.co[:] for v in bm.verts]); V = V @ M[:3, :3].T + M[:3, 3]
T = np.array([[v.index for v in f.verts] for f in bm.faces]); np.savez(a[2], V=V, T=T); print('DUMP', len(V), len(T))
