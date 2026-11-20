"""Gap of each helmet guard piece to the rest of the helmet at bind (all rigid on Bip01 Head). Args: <blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
me = bpy.data.objects['Parts'].data
pid = np.zeros(len(me.vertices), int); me.attributes['pid'].data.foreach_get('value', pid)
v = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('co', v); v = v.reshape(-1, 3)
G = [22, 26, 40, 54, 55, 63, 126, 140, 154, 155, 163]
for p in G:
    a = v[pid == p]; b = v[np.isin(pid, [21] + [g for g in G if g != p])]
    d = np.sqrt(((a[:, None] - b[None]) ** 2).sum(-1)).min(1)
    print('GAP', p, len(a), 'closest', round(float(d.min()) * 1000, 1), 'mm, median', round(float(np.median(d)) * 1000, 1), 'max', round(float(d.max()) * 1000, 1))
