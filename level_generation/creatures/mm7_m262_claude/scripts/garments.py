"""Label every loose part of the m262 body (piece attribute, work/part_labels.json) by garment, for the weight rules:
0 skin (P00 torso, feathered hips/thighs and head; P01/P02 bird legs and feet; P03/P04 hands: Meshy weights),
1 rigid head (P13/P14 eyes),
3 copies the skin under it without arm or clavicle weight (hair shells and strands, gold waist band, crotch tuft),
7 tail feather cards: rigid on B_Pelvis,
8 copies the skin under it INCLUDING the arm (P09/P10 bracers).
The wings are a separate object (wings_rig.py). Writes the 'garment' point attribute and work/garments.json.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
LAB = json.load(open(os.path.join(common.WORK, 'part_labels.json')))
G = {'body': 0, 'legR': 0, 'legL': 0, 'handL': 0, 'handR': 0, 'eye': 1, 'hair': 3, 'band': 3, 'tuft': 3, 'tail': 7,
     'bracerL': 8, 'bracerR': 8}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data; nv = len(me.vertices)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
lab = {int(p): G[LAB[str(int(p))]] for p in sorted(set(pv.tolist()))}
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(9)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(common.WORK, 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
