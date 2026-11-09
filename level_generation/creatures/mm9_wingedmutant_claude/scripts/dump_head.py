"""Head texture set inputs for compose_head.py (rework 2026-10-30): per head triangle its HeadUV, rest-pose xyz, kind
(1 skin, 2 eye, 3 hair, 4 tooth; 0 = bridge/body ring vertices) and bridge flag; per body triangle that touches the
neck ring its UVMap and xyz (the body colour at the seam); every body triangle's UVMap and xyz (the neck fade). Also the neck frame (Bip01 Neck, the Neck -> Head line).
Args: -- <blend> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent
me = ob.data
me.calc_loop_triangles()
head = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', head)
bridge = np.zeros(len(me.polygons), np.int32); me.attributes['bridge'].data.foreach_get('value', bridge)
kind = np.zeros(len(me.vertices), np.int32); me.attributes['kind'].data.foreach_get('value', kind)
huv, buv = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
ring = set()
for p in me.polygons:
    if bridge[p.index]:
        ring |= {v for v in p.vertices if kind[v] == 0}
H = {'uv': [], 'xyz': [], 'kind': [], 'bridge': []}
Bd = {'uv': [], 'xyz': []}
BA = {'uv': [], 'xyz': []}
for t in me.loop_triangles:
    xyz = [tuple(ob.matrix_world @ me.vertices[v].co) for v in t.vertices]
    if head[t.polygon_index]:
        H['uv'].append([tuple(huv[l].uv) for l in t.loops]); H['xyz'].append(xyz)
        H['kind'].append(int(np.bincount([kind[v] for v in t.vertices], minlength=5).argmax()))
        H['bridge'].append(int(bridge[t.polygon_index]))
    else:
        if any(v in ring for v in t.vertices):
            Bd['uv'].append([tuple(buv[l].uv) for l in t.loops]); Bd['xyz'].append(xyz)
        BA['uv'].append([tuple(buv[l].uv) for l in t.loops]); BA['xyz'].append(xyz)
J = {b.name: np.array(b.head_local) for b in rig.data.bones}
np.savez(a[1], head_uv=np.array(H['uv'], np.float32), head_xyz=np.array(H['xyz'], np.float32),
         head_kind=np.array(H['kind'], np.int32), head_bridge=np.array(H['bridge'], np.int32),
         seam_uv=np.array(Bd['uv'], np.float32), seam_xyz=np.array(Bd['xyz'], np.float32),
         body_uv=np.array(BA['uv'], np.float32), body_xyz=np.array(BA['xyz'], np.float32),
         neck=J['Bip01 Neck'], head_joint=J['Bip01 Head'])
print('DUMPHEAD', len(H['uv']), 'head tris', len(Bd['uv']), 'seam body tris')
