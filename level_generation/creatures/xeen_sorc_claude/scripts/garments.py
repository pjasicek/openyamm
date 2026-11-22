"""Label every loose part of the sorceress body (piece attribute from step1_clean.py) by garment, for the weight rules:
0 body shell (P00: skin, halter, gloves and boots in one shell): Meshy weights + rules
1 hair (P01 mane and every curl/strand card round the head)
2 head hard surface (eyes P16/P17, lips P54, circlet P19/P23/P28, earrings P18/P30/P32): rigid head
3 front panel (P04): pelvis at the top -> left/right thigh mixture at the hem
4 shoulder caps (P07 right, P08 left) and their studs (small pieces beside them): copy the skin under them
5 neck and chest jewellery (choker P12 and its gem/ends, chest pieces P44/P51): copy the skin under them, no arm weight
6 girdle (P03) with its gems and studs: rigid per piece on the skin weights under it, no arm weight
7 back panel (P06): pelvis at the top -> left/right thigh mixture at the hem
Writes the 'garment' point attribute and work/garments.json; renders a coloured check. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
FIXED = {0: 0, 4: 3, 6: 7, 3: 6, 7: 4, 8: 4, 12: 5, 16: 2, 17: 2, 54: 2, 19: 2, 23: 2, 28: 2, 18: 2, 30: 2, 32: 2,
         44: 5, 51: 5}
lab = {}
for p in sorted(set(pv.tolist())):
    m = pv == p; c = co[m].mean(0); lo, hi = co[m].min(0), co[m].max(0); ext = hi - lo
    if p in FIXED:
        g = FIXED[p]
    elif 0.9 < c[2] < 1.12:
        g = 6                                              # girdle gems and studs
    elif 1.37 < c[2] < 1.41 and abs(c[0]) > 0.1:
        g = 4                                              # studs on the shoulder caps
    elif 1.36 < c[2] < 1.44 and abs(c[0]) < 0.12 and c[1] < -0.03:
        g = 5                                              # choker gem and ends
    elif c[2] > 1.40:
        g = 1                                              # curls and strands
    else:
        raise SystemExit(f'unlabelled piece {p} at {c}')
    lab[p] = g
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
by = {}
for p, g in lab.items():
    by.setdefault(g, []).append(p)
print('GARMENT pieces', {g: len(v) for g, v in sorted(by.items())}, 'verts', {g: int((gv == g).sum()) for g in range(8)})
print('GARMENT non-hair', {g: v for g, v in by.items() if g not in (0, 1)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(common.WORK, 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
cols = [(0.75, 0.6, 0.5), (0.3, 0.4, 0.95), (0.95, 0.75, 0.1), (0.2, 0.8, 0.3), (0.9, 0.2, 0.2), (0.9, 0.3, 0.8),
        (0.1, 0.9, 0.9), (0.2, 0.2, 0.2)]
ca = me.color_attributes.new('gcol', 'FLOAT_COLOR', 'POINT')
for i in range(nv):
    ca.data[i].color = (*cols[gv[i]], 1)
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'VERTEX'
common.render_views(os.path.join(common.REVIEW, 'garments'), 0.92, 1.95, views=('front', 'left', 'back'), resolution=(500, 800), distance=20)
