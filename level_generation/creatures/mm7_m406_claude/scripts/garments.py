"""Label every loose part of the m406 body (piece attribute from step1_clean.py) by garment, for the weight rules:
0 skin (legs, torso + tabard, head, hands, arms: Meshy weights), 1 rigid head (helmet, eyes), 3 mail coif (copies the
skin, no arm weight), 4 small fittings (buckle, knee-cop studs: rigid on the dominant bone under them).
Writes the 'garment' point attribute and work/garments.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data; nv = len(me.vertices)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
FIXED = {3: 1, 9: 1, 10: 1, 8: 3, 11: 4, 12: 4, 13: 4, 14: 4, 15: 4}
lab = {p: FIXED.get(p, 0) for p in sorted(set(pv.tolist()))}
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(5)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(common.WORK, 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
