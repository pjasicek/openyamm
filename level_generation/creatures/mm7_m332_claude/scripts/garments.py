"""Label every loose part of the m222 body (piece attribute from step1_clean.py) by garment, for the weight rules:
0 skin (P00 body with hair and boots, P01/P02 arms with gauntlets and fingers), 1 helmet and eyes (rigid head),
2 right shoulder guard (copies the skin under it), 3 gold front panels (strips pelvis -> thigh), 4 green neck trim and
clasp (copies the skin, no arm weight), 5 belt chain links (rigid pelvis).
Writes the 'garment' point attribute and work/garments.json; renders a coloured check. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data; nv = len(me.vertices)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
lab = {}
for p in sorted(set(pv.tolist())):
    if p in (0, 1, 2):
        g = 0
    elif p in (3, 11, 12):
        g = 1
    elif p == 6:
        g = 2
    elif p in (7, 8):
        g = 3
    elif p in (9, 10, 13):
        g = 4
    else:
        g = 5
    lab[p] = g
gv = np.array([lab[p] for p in pv], np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {g: int((gv == g).sum()) for g in range(6)})
json.dump({str(p): int(g) for p, g in lab.items()}, open(os.path.join(common.WORK, 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
cols = [(0.75, 0.6, 0.5), (0.9, 0.85, 0.3), (0.95, 0.55, 0.1), (0.95, 0.8, 0.1), (0.1, 0.8, 0.3), (0.9, 0.2, 0.2)]
ca = me.color_attributes.new('gcol', 'FLOAT_COLOR', 'POINT')
for i in range(nv):
    ca.data[i].color = (*cols[gv[i]], 1)
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'VERTEX'
common.render_views(os.path.join(common.REVIEW, 'garments'), 0.85, 1.8, views=('front', 'left', 'back'), resolution=(500, 800), distance=20)
