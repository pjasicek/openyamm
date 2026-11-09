"""Label every loose part of the m154 body (piece attribute from step1_clean.py) by garment, for the weight rules:
0 skin (tunic, legs, head, hands, forearms: Meshy weights), 1 rigid head (helmet, horns, spike, eyes), 3 mail coif
(copies the skin, no arm weight), 4 small fittings (buckle: rigid on the dominant bone under it), 5 quiver and arrows
(rigid on the chest), 6 diagonal strap (copies the skin, no arm weight).
Writes the 'garment' point attribute and work/garments.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data; nv = len(me.vertices)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
FIXED = {6: 1, 11: 1, 12: 1, 13: 1, 14: 1, 17: 1, 7: 3, 15: 4, 10: 6, 5: 5, 16: 5, 18: 5, 19: 5, 20: 5, 21: 5, 22: 5, 23: 5, 24: 5}
lab = {p: FIXED.get(p, 0) for p in sorted(set(pv.tolist()))}
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(7)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(common.WORK, 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
