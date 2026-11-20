"""Label every loose part of the m150 v2 body (piece attribute from step1_clean.py; labels from work/step1_labels.json)
by garment, for the weight rules:
0 skin (P00 torso + cuirass, arms, head, thighs; P04/P05 hands; the greaves P07/P09, sandals P08/P10, sandal straps
  P13/P14 and soles P17/P19, which are the lower legs and feet: Meshy weights + the armhole rule on P00),
1 rigid head (P15/P16 eyes),
2 copies the skin under it with all its weights (P11/P12 bracers),
3 copies the skin under it without arm or clavicle weight (the hair locks),

4 small fittings rigid on the bone that dominates the skin under them (buckle, belt studs and rings, knee and sandal
  studs: every remaining piece under 70 triangles that is not a tab),
6 skirt (P06: dress rule),
7 leather tabs (pieces between 0.6 and 1.1 m, at least 20 cm long: one strip each, one left/right mix per strip).
The wings are a separate object (wings_rig.py). Writes the 'garment' point attribute and work/garments.json.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data; nv = len(me.vertices)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
PARTS = {int(r['name'][1:]): r for r in json.load(open(os.path.join(common.WORK, 'st_v2_parts.json')))}
LAB = {int(k): v for k, v in json.load(open(os.path.join(common.WORK, 'step1_labels.json'))).items()}
FIXED = {0: 0, 4: 0, 5: 0, 15: 1, 16: 1, 6: 6, 3: 3}   # P03 straps: re-weighted with the clavicle on the master (strap_weights.py)
# the legs below the knee ARE the greaves and sandals (the skin shell stops at the greaves' top): Meshy's weights
for p in (7, 9, 8, 10, 13, 14, 17, 19):
    FIXED[p] = 0
for p in (11, 12):
    FIXED[p] = 2
for p in sorted(set(pv.tolist())):
    if p in FIXED:
        continue
    r = PARTS[p]; lo, hi = r['lo'], r['hi']
    if LAB[p] == 'hair':
        FIXED[p] = 3
    elif lo[2] > 0.6 and hi[2] < 1.1 and hi[2] - lo[2] > 0.2 and r['tris'] < 100:
        FIXED[p] = 7
    elif r['tris'] < 70:
        FIXED[p] = 4
lab = {p: FIXED.get(p, 0) for p in sorted(set(pv.tolist()))}
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(9)})
print('GARMENT pieces', {g: sorted(p for p, x in lab.items() if x == g) for g in range(9)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(common.WORK, 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
