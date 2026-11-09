"""Label every loose part of the m238 body (piece attribute from step1_clean.py) by garment, for the weight rules:
0 skin (P00: torso, arms, head, ponytail; its core below the hips is reweighted onto the vortex chain by vortex.py),
1 rigid head (P02 circlet, P03/P04 earrings, P05/P06 eyes, P07/P09 forehead jewel, P08 lips sliver),
5 vortex shell (P01: weighted by vortex.py onto the Vortex chain).
Writes the 'garment' point attribute and work/garments.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data; nv = len(me.vertices)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
FIXED = {2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 1: 5}
lab = {p: FIXED.get(p, 0) for p in sorted(set(pv.tolist()))}
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(6)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(common.WORK, 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
