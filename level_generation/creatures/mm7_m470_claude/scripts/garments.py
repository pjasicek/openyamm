"""Label every piece of the m470 body by class, for the weight rules, the texture classes and the reduction:
0 skin (P00: one closed body; the overalls, bracers and lacing are painted on it), 1 hair (P01), 2 teeth (P02, P03,
P11), 3 eyes (P04, P05), 4 chest lacing bars (P06-P10), 5 eyelet studs (every other small piece). Writes the
'garment' point attribute and work/garments.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
me = bpy.data.objects['Body'].data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
FIX = {0: 0, 1: 1, 2: 2, 3: 2, 11: 2, 4: 3, 5: 3, 6: 4, 7: 4, 8: 4, 9: 4, 10: 4}
lab = {}
for p in sorted(set(pv.tolist())):
    n = int((pv == p).sum())
    if p in FIX:
        lab[p] = FIX[p]
    else:
        lab[p] = 5
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(6)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
