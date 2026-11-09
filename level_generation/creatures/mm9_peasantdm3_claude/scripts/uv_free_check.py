import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me = bpy.data.objects['Body'].data
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
uv = me.uv_layers['HeadUV'].data
occ = np.zeros((64, 64), bool)
for f in me.polygons:
    if not (hd[f.index] or hn[f.index]): continue
    p = np.array([tuple(uv[l].uv) for l in f.loop_indices])
    lo, hi = np.floor(p.min(0) * 64).astype(int), np.ceil(p.max(0) * 64).astype(int)
    occ[max(lo[1],0):min(hi[1],64), max(lo[0],0):min(hi[0],64)] = True
# print free cells in u 0.8..1, v 0..0.6 (blender uv)
free = [(round((i + 0.5) / 64, 3), round((j + 0.5) / 64, 3)) for j in range(0, 38) for i in range(52, 64) if not occ[j, i]]
print('FREE', len(free), free[:10])
