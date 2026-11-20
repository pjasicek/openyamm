"""Per-triangle UVs of 'Body' for compose_v2.py (2026-10-30 rework): uv (UVMap), huv (HeadUV), head, piece (max of the
triangle's vertices), pos (bind-pose corner positions). Args: <uv blend> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
head = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', head)
piece = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', piece)
U, H, P = me.uv_layers['UVMap'].data, me.uv_layers['HeadUV'].data, []
uv, huv, hd, pc, pos = [], [], [], [], []
for p in me.polygons:
    li = list(p.loop_indices)
    uv.append([U[i].uv[:] for i in li]); huv.append([H[i].uv[:] for i in li])
    hd.append(head[p.index]); pc.append(piece[list(p.vertices)].max()); pos.append([me.vertices[v].co[:] for v in p.vertices])
np.savez(a[1], uv=np.array(uv, np.float32), huv=np.array(huv, np.float32), head=np.array(hd), piece=np.array(pc),
         pos=np.array(pos, np.float32))
print('DUMPED', len(uv))
