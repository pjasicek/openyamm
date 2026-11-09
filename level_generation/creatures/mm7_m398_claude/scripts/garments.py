"""Label every piece of the m398 body (piece attribute: Smart Topology parts P00.., head parts 100+) by class, for the
weight rules, the texture classes and the head split:
0 bone (spine column, ribs, clavicle ring, pelvis bones, limb bones, shoulder balls, elbow knobs, kneecaps), 1 cuirass,
2 gauntlet, 3 breeches, 4 boot, 5 skull (head model P00), 6 helmet (head model P01), 7 teeth and helmet rivets of the
head model, 8 small rivets/studs of the body (copy the piece they sit on).
Writes the 'garment' point attribute and work/garments.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
me = bpy.data.objects['Body'].data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
FIX = {0: 1, 1: 2, 2: 2, 4: 3, 5: 4, 6: 4, 100: 5, 101: 6}
# small bones (fibulas, pelvis crests, lower back ribs) are bones, not studs
FIX.update({p: 0 for p in (28, 29, 30, 31, 32, 33, 34, 38, 47, 51)})
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
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(9)}, 'pieces', {g: sorted(p for p, x in lab.items() if x == g) for g in (0, 8)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
