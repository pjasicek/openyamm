"""Label every loose part of the m234 body (piece attribute from split_parts.py) by garment, for the weight rules:
0 skin (P00: the whole stone body; Meshy weights), 1 rigid head (P03/P04 eyes, P05 and P07..P22 teeth).
The wings and the tail are separate objects (wings_rig.py, tail_rig.py). Writes the 'garment' point attribute and
work/garments.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data; nv = len(me.vertices)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
FIXED = {p: 1 for p in [3, 4, 5] + list(range(7, 23))}
lab = {p: FIXED.get(p, 0) for p in sorted(set(pv.tolist()))}
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(8)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(common.WORK, 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
