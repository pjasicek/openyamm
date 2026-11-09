"""Label every loose part of the m246 body (piece attribute from step1_clean.py) by garment, for the weight rules:
0 skin (P00 body, P04/P05 hands: Meshy weights), 1 rigid head (crest, helmet, eyes, cheek pieces, goatee, crest base,
helmet spikes), 2 hip panels (strip rule), 3 hair (copies the skin, no arm or clavicle weight), 4 spikes and studs
(<= 40 triangles below the helmet: one uniform weight set from the parts under them), 5 vest, strap, belt (copy the
skin, no arm weight), 6 bracers, upper-arm plate, shin guards (copy the skin as is), 7 pauldron (copies the skin,
arm share <= 0.5). Writes the 'garment' point attribute and work/garments.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data; nv = len(me.vertices)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(v.co) for v in me.vertices])
FIXED = {0: 0, 4: 0, 5: 0, 1: 1, 6: 1, 12: 1, 13: 1, 20: 1, 22: 1, 23: 1, 30: 1, 31: 1, 32: 1,
         15: 2, 16: 2, 18: 2, 19: 2, 24: 2, 25: 2, 26: 2, 27: 2, 28: 2, 29: 2, 2: 3,
         3: 5, 9: 5, 14: 5, 7: 6, 8: 6, 11: 6, 17: 6, 21: 6, 10: 7}
lab = {}
for p in sorted(set(pv.tolist())):
    if p in FIXED:
        lab[p] = FIXED[p]
    else:   # spikes and studs: on the helmet -> rigid head, elsewhere -> uniform copy
        lab[p] = 1 if co[pv == p, 2].mean() > 1.45 else 4
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(8)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(common.WORK, 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
