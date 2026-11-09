"""Label every loose part of the m362 body (piece attribute from step1_clean.py) by garment, for the weight rules:
0 skin (P00 head/neck/chest, P01/P02 hands (left/right), P03 breeches, P04 doublet, P05/P06 boots, P10/P11 shirt
sleeves, P27/P30 shirt cuffs: Meshy weights), 1 rigid head (P16/P18 eyes, P29 mouth, P45), 2 shoulder rolls (P08/P09:
copy the skin, arm share capped), 3 hair (P07 and the strands: head -> neck -> chest by height), 4 copy-the-skin
without arm weight (P12 doublet skirt, P14 shirt collar, P15 belt, P21/P22 boot cuffs), 6 sheathed rapier (P13 hilt,
P17 scabbard, P24/P25/P31/P32 hilt parts: rigid on B_Pelvis), 7 small fittings (< 120 triangles: chest laces, belt
studs; rigid on the dominant bone). Writes the 'garment' point attribute and work/garments.json; renders a coloured
check. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data; nv = len(me.vertices)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
tris = {}
for p in me.polygons:
    k = int(pv[p.vertices[0]]); tris[k] = tris.get(k, 0) + len(p.vertices) - 2
FIXED = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 10: 0, 11: 0, 27: 0, 30: 0, 16: 1, 18: 1, 29: 1, 45: 1, 8: 2, 9: 2, 7: 3, 19: 3, 20: 3, 23: 3, 26: 3, 28: 3, 33: 3, 34: 3, 35: 3, 36: 3, 39: 3, 40: 3, 12: 4, 14: 4, 15: 4, 21: 4, 22: 4, 13: 6, 17: 6, 24: 6, 25: 6, 31: 6, 32: 6}
lab = {p: FIXED.get(p, 7 if tris[p] < 120 else 4) for p in sorted(set(pv.tolist()))}
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(8)}, 'large accessories', [p for p, g in lab.items() if g == 4])
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(common.WORK, 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
cols = [(0.75, 0.6, 0.5), (0.2, 0.2, 0.2), (0.3, 0.4, 0.95), (0.95, 0.6, 0.1), (0.1, 0.8, 0.3), (0.9, 0.2, 0.2),
        (0.9, 0.85, 0.2), (0.9, 0.3, 0.9)]
ca = me.color_attributes.new('gcol', 'FLOAT_COLOR', 'POINT')
for i in range(nv):
    ca.data[i].color = (*cols[gv[i]], 1)
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'VERTEX'
common.render_views(os.path.join(common.REVIEW, 'garments'), 0.85, 1.8, views=('front', 'left', 'back'), resolution=(500, 800), distance=20)
