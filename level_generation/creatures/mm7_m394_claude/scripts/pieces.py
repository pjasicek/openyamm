"""List the loose pieces of work/step1.blend (count, bounds, centre) and render them coloured (front, side, top,
three-quarter) to review/pieces_*.png. Args: -- <blend>"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[-1]))
ob = bpy.data.objects['Body']; me = ob.data
co = np.array([tuple(v.co) for v in me.vertices]); pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
for p in range(pv.max() + 1):
    c = co[pv == p]
    print('PIECE', p, len(c), 'lo', np.round(c.min(0), 3).tolist(), 'hi', np.round(c.max(0), 3).tolist())
cols = [(0.8, 0.8, 0.8, 1), (0.9, 0.2, 0.2, 1), (0.2, 0.8, 0.2, 1), (0.2, 0.4, 0.95, 1), (0.95, 0.8, 0.2, 1), (0.8, 0.3, 0.9, 1), (0.2, 0.85, 0.85, 1)]
mats = []
for i, c in enumerate(cols):
    m = bpy.data.materials.new(f'c{i}'); m.diffuse_color = c; me.materials.append(m)
fp = np.array([pv[p.vertices[0]] for p in me.polygons])
me.polygons.foreach_set('material_index', [0 if x == 0 else 1 + (x % 6) for x in fp])
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'MATERIAL'
common.render_views(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'review', 'pieces'), 0.3, 1.3,
                    views=('front', 'left', 'three_quarter', 'back'), resolution=(900, 600))
