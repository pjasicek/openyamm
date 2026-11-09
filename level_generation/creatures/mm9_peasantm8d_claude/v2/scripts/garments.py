"""Label every loose part of the hvm body (piece attribute from step1_clean.py) by garment, for the weight rules:
0 skin (P00 coat with the belt, P01 head and neck, P02 trousers, P03/P04 left/right hands, P06/P07 shoes), 1 rigid
head (P09/P10 eyes), 3 hair (the ~100 hair cards whose lowest point is above z 1.47: head -> neck by height), 4 the
pouch on his left hip (P05: copies the skin under it, no arm weight), 7 small fittings (the pin P12/P15 and the
coat's gold clasps: rigid on the bone that dominates the skin under them). Writes the 'garment' point attribute and
work/garments.json; renders a coloured check. Args: -- <in blend> <out blend>"""
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
FIXED = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 6: 0, 7: 0, 9: 1, 10: 1, 5: 4}
PARTS = {int(r['name'][1:]): r for r in json.load(open(os.path.join(common.WORK, 'st_v1_parts.json')))}
lab = {p: FIXED.get(p, 3 if PARTS[p]['lo'][2] > 1.47 else 7) for p in sorted(set(pv.tolist()))}
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
