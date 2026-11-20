"""Label every loose part of the pman v3 body (piece attribute from step1_clean.py; parts after graft_head_parts.py,
work/graft.json) by garment, for the weight rules (weights_fix.py): 0 skin (P00 tunic, P01 trousers with boots, P02
the old neck's V of chest skin, P03/P04 right/left arms with hands, P09 the grafted head: face, ears, hair), 4 the
belt (P05: copies the skin under it, no arm weight), 7 small fittings (buckle P06, belt rings P07/P08: rigid on the
bone that dominates the skin under them). Writes the 'garment' point attribute and work/garments.json; renders a
coloured check. Args: -- <in blend> <out blend>"""
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
FIXED = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 9: 0, 5: 4, 6: 7, 7: 7, 8: 7}
lab = {p: FIXED[p] for p in sorted(set(pv.tolist()))}
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
