"""Clay renders of the Body in a blend, coloured by 'piece'. Args: -- <blend> <out prefix> <centre z> <height> [views]"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
cz, h = float(a[2]), float(a[3])
views = tuple(a[4].split(',')) if len(a) > 4 else ('front', 'three_quarter', 'right', 'back')
for o in list(bpy.data.objects):
    if o.type not in ('MESH', 'ARMATURE'):
        bpy.data.objects.remove(o, do_unlink=True)
body = bpy.data.objects['Body']
cols = [(0.85, 0.55, 0.5, 1), (0.4, 0.6, 0.35, 1), (0.4, 0.5, 0.9, 1), (0.9, 0.8, 0.3, 1), (0.8, 0.4, 0.9, 1), (0.3, 0.85, 0.85, 1),
        (0.95, 0.95, 0.85, 1), (0.6, 0.6, 0.6, 1)]
if 'piece' in body.data.attributes:
    pv = np.zeros(len(body.data.vertices), np.int32); body.data.attributes['piece'].data.foreach_get('value', pv)
    body.data.materials.clear()
    for i in range(int(pv.max()) + 1):
        m = bpy.data.materials.new(f'p{i}'); m.diffuse_color = cols[i % len(cols)]; body.data.materials.append(m)
    for p in body.data.polygons:
        p.material_index = int(pv[p.vertices[0]])
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
common.render_views(a[1], cz, h, views=views, resolution=(600, 900) if h > 1 else (600, 600))
