"""Label every piece of the m418 troglodyte by class, for the weight rules, the texture classes and the reduction:
0 skin (P00: one closed body with the hood, the back spines, the arms with their claws, the legs and the tail),
1 teeth (the small pieces in the maw, y < -1.0 at the working scale), 2 tail spines (the small pieces on the tail).
Writes the 'garment' point attribute and work/garments.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
me = bpy.data.objects['Body'].data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
FIX = {0: 0}
co = np.array([tuple(v.co) for v in me.vertices])
lab = {}
for p in sorted(set(pv.tolist())):
    n = int((pv == p).sum())
    if p in FIX:
        lab[p] = FIX[p]
    else:
        lab[p] = 1 if co[pv == p, 1].mean() < -1.0 else 2
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(3)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
