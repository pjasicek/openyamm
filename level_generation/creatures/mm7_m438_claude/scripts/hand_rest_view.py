"""Clay close-ups of both hand shells at rest (the step1 mesh). Args: -- <blend> <out prefix>"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scene = bpy.context.scene; common.workbench_clay(scene)
ob = bpy.data.objects['Body']
pv = np.zeros(len(ob.data.vertices), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices])
for p, n in ((4, 'L'), (5, 'R')):
    c = co[pv == p].mean(0)
    common.render_views(f'{out}_{n}', c[2], 0.22, views=('front', 'left', 'right', 'back'), resolution=(400, 400), target=(c[0], c[1]))
