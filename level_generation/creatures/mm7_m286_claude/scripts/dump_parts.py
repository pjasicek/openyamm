"""Dump a parts blend (examine_parts.py output, objects P00..) to npz: world vertex positions, triangles and part
index per vertex, for quick proportion checks before rigging. Args: -- <blend> <out npz>"""
import bpy, sys, os
import numpy as np
blend, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
co, tris, part = [], [], []
off = 0
for o in sorted((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: o.name):
    me = o.data; me.calc_loop_triangles()
    c = np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])
    co.append(c); part.append(np.full(len(c), int(o.name[1:]) if o.name[1:].isdigit() else -1))
    tris.append(np.array([tuple(t.vertices) for t in me.loop_triangles]) + off); off += len(c)
np.savez(out, co=np.vstack(co), tris=np.vstack(tris), part=np.concatenate(part))
print('DUMPPARTS', off)
