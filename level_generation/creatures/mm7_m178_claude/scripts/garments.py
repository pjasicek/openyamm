"""Label every piece of the m178 devil by class, for the weight rules, the texture classes and the reduction:
0 skin (P00: one closed body with the head, ears, all head/shoulder/forearm spikes, hands with claws, feet and the
tail), 1 teeth (small pieces in the mouth, y < -0.8 and z 1.36-1.41), 3 eyes (the two shells at eye height z ~1.45),
2 tail spikes (the small pieces along the tail's upper curve and the lower back).
Writes the 'garment' point attribute and work/garments.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
me = bpy.data.objects['Body'].data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(v.co) for v in me.vertices])
lab = {}
for p in sorted(set(pv.tolist())):
    c = co[pv == p].mean(0)
    if p == 0:
        lab[p] = 0
    elif c[1] < -0.78 and c[2] > 1.43:
        lab[p] = 3
    elif c[1] < -0.78:
        lab[p] = 1
    else:
        lab[p] = 2
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT pieces per class', {g: sum(1 for v in lab.values() if v == g) for g in range(4)},
      'vertices', {g: int((gv == g).sum()) for g in range(4)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
