"""Label every piece of the m270 body by class, for the weight rules, the texture classes and the reduction:
0 head (the grafted skull, crown and coif, ids 100+), 1 plate (breastplate P07, abdomen P11, pauldrons P08/P09, wrist
cuffs P12/P13), 2 arms (P01/P02: chain sleeve + bony hand), 3 chain skirt (P05), 4 legs and shoes (P04), 5 gold belt
(P14, buckle P15, band P21), 6 chain shoulder caps (P19/P20). Writes the 'garment' point attribute and
work/garments.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
me = bpy.data.objects['Body'].data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
FIX = {7: 1, 11: 1, 8: 1, 9: 1, 12: 1, 13: 1, 1: 2, 2: 2, 5: 3, 4: 4, 14: 5, 15: 5, 21: 5, 19: 6, 20: 6}
lab = {}
for p in sorted(set(pv.tolist())):
    n = int((pv == p).sum())
    if p in FIX:
        lab[p] = FIX[p]
    elif p >= 100:
        lab[p] = 0
    elif n >= 40:
        lab[p] = 0
    else:
        lab[p] = 8
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(9)}, 'unlabelled pieces', sorted(p for p, x in lab.items() if x == 8))
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
