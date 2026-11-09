"""Label every loose part of the m226 body (piece attribute from step1_clean.py) by garment, for the weight rules:
0 skin (P00 body, P01 head, P03/P04 hands), 1 rigid head (P05 hair, P33/P36 face strands, P39/P41 eyes), 2 shoulder
yoke (P02, copies the skin), 3 ponytail (P06/P11/P14/P18: head -> neck -> chest by height), 4 belt/straps (copy the
skin, no arm weight: the large accessories), 5 back scabbard (P08, rigid on the chest), 6 dagger + sheath (P07/P10,
rigid on the pelvis), 7 small fittings (< 120 triangles: studs, spikes, buckles; rigid on the bone that dominates the
skin under them). Writes the 'garment' point attribute and work/garments.json; renders a coloured check.
Args: -- <in blend> <out blend>"""
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
FIXED = {0: 0, 1: 0, 3: 0, 4: 0, 5: 1, 33: 1, 36: 1, 39: 1, 41: 1, 2: 2, 6: 3, 11: 3, 14: 3, 18: 3, 8: 5, 7: 6, 10: 6}
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
