"""Blender: dump the ear faces of a master (face attribute `ear` 1/2): per triangle corner HeadUV and rest position.
Args: <blend> <out npz>"""
import bpy, sys, numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
me = bpy.data.objects['Body'].data
ear = np.zeros(len(me.polygons), np.int32); me.attributes['ear'].data.foreach_get('value', ear)
uv = me.uv_layers['HeadUV'].data
UV, P, E = [], [], []
for p in me.polygons:
    if ear[p.index]:
        l = list(p.loop_indices)
        for k in range(1, len(l) - 1):
            tri = [l[0], l[k], l[k + 1]]
            UV.append([uv[i].uv[:] for i in tri]); P.append([me.vertices[me.loops[i].vertex_index].co[:] for i in tri]); E.append(ear[p.index])
np.savez(a[1], UV=np.array(UV), P=np.array(P), E=np.array(E))
print('EAR_DUMP', len(E))
