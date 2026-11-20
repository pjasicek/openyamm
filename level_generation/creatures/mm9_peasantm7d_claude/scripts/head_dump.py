"""Blender: every head-set face (head=1, hand=0) of a master: per triangle corner HeadUV and rest position (for texel
position rasters). Args: <blend> <out npz>"""
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
uv = me.uv_layers['HeadUV'].data
UV, P = [], []
for p in me.polygons:
    if hd[p.index] and not hn[p.index]:
        l = list(p.loop_indices)
        for k in range(1, len(l) - 1):
            t = [l[0], l[k], l[k + 1]]
            UV.append([uv[i].uv[:] for i in t]); P.append([me.vertices[me.loops[i].vertex_index].co[:] for i in t])
np.savez(a[1], UV=np.array(UV), P=np.array(P))
print('HEAD_DUMP', len(UV))
