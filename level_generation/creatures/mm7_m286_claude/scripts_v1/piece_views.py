"""Render a joined 'Body' (work/*.blend) coloured by its 'piece' attribute: four orthographic views for review.
Args: -- <blend> <out prefix> [center_z height]"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
cz, h = (float(a[2]), float(a[3])) if len(a) > 3 else (1.25, 2.6)
ob = bpy.data.objects['Body']
pv = np.zeros(len(ob.data.vertices), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pv)
cols = [(0.85, 0.45, 0.4), (0.3, 0.8, 0.3), (0.3, 0.5, 0.95), (0.95, 0.8, 0.2), (0.8, 0.3, 0.9), (0.2, 0.85, 0.85),
        (0.95, 0.55, 0.2), (0.6, 0.6, 0.6)]
ob.data.materials.clear()
for k, c in enumerate(cols):
    m = bpy.data.materials.new(f'c{k}'); m.diffuse_color = (*c, 1); ob.data.materials.append(m)
for p in ob.data.polygons:
    p.material_index = 0 if pv[p.vertices[0]] == 0 else 1 + pv[p.vertices[0]] % (len(cols) - 1)
    p.use_smooth = True
scene = bpy.context.scene
common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
common.render_views(os.path.abspath(a[1]), cz, h, views=('front', 'three_quarter', 'left', 'back'), resolution=(600, 900))
