"""Label every piece of the m430 body (piece attribute: Smart Topology parts P00..P05) by class, for the weight rules,
the texture classes and the reduction: 0 robe + head + hair (one connected piece P00), 2 hands (P01 left, P02 right),
3 waist cord strands (P03, P04), 4 inner hem (P05, the robe's underside at the floor).
Writes the 'garment' point attribute and work/garments.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
me = bpy.data.objects['Body'].data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
FIX = {0: 0, 1: 2, 2: 2, 3: 3, 4: 3, 5: 4}
lab = {}
for p in sorted(set(pv.tolist())):
    n = int((pv == p).sum())
    if p in FIX:
        lab[p] = FIX[p]
    elif p >= 100:
        lab[p] = 7
    elif n >= 40:
        lab[p] = 0
    else:
        lab[p] = 8
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(5)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
