"""List vertices whose weight on bones matching a key exceeds a threshold, outside an x/z box (rest positions):
piece, garment, rest position, top weights. Args: -- <blend> <bone key> <threshold> [max |x|]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
body = bpy.data.objects['Body']; me = body.data; names = [g.name for g in body.vertex_groups]
key, thr = a[1], float(a[2]); xmax = float(a[3]) if len(a) > 3 else 9
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
n = 0; pieces = {}
for v in me.vertices:
    w = sum(e.weight for e in v.groups if key in names[e.group])
    if w > thr and abs(v.co.x) < xmax:
        n += 1; pieces[int(pv[v.index])] = pieces.get(int(pv[v.index]), 0) + 1
        if n <= 8:
            top = sorted(((e.weight, names[e.group]) for e in v.groups), reverse=True)[:3]
            print('WPROBE', v.index, 'piece', pv[v.index], [round(x, 3) for x in v.co], [(round(w_, 2), nm) for w_, nm in top])
print('WPROBE count', n, 'by piece', pieces)
