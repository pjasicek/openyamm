"""Label every loose part of the m150 body (piece attribute from step1_clean.py) by garment, for the weight rules:
0 skin (P00 torso, upper arms, neck and face; P02 legs and greaves; P04/P05 forearms, bracers and hands: Meshy weights),
1 rigid head (P13 crest, P23 helmet back plate, P25/P32 temple wing ornaments, P39/P40 eyes),
3 copies the skin under it without arm or clavicle weight (P03 helmet bowl, cheek guards and hair; P14/P15 breastplate
  straps; P16 belt; P09/P10 sandals, P26/P28 soles, P31/P33/P34/P35 sandal straps; P27/P29 knee plates),
4 small fittings rigid on the bone that dominates the skin under them (P24 buckle, P38, P41-P53 belt rings and studs,
  P54-P57 sandal studs),
6 skirt (P08: dress rule, pelvis at the belt -> thighs at the hem with a smooth left/right mix),
7 leather tabs (P17-P22, P30, P36, P37: one strip each, pelvis at the belt -> its thigh at the tip, ONE left/right mix
  per strip from its centre).
The wings are a separate object (wings.py). Writes the 'garment' point attribute and work/garments.json.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data; nv = len(me.vertices)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
FIXED = {}
for p in (13, 23, 25, 32, 39, 40):
    FIXED[p] = 1
for p in (3, 14, 15, 16, 9, 10, 26, 28, 31, 33, 34, 35, 27, 29):
    FIXED[p] = 3
for p in [24, 38] + list(range(41, 54)) + [54, 55, 56, 57]:
    FIXED[p] = 4
FIXED[8] = 6
for p in (17, 18, 19, 20, 21, 22, 30, 36, 37):
    FIXED[p] = 7
lab = {p: FIXED.get(p, 0) for p in sorted(set(pv.tolist()))}
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(8)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(common.WORK, 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
