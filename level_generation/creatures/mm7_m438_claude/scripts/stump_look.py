"""Close clay renders of the right-arm stump (pieces coloured; rest pose). Args: -- <blend> <out prefix>"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, outp = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
J = json.load(open(os.path.join(common.WORK, 'joints_final.json')))['joints']
body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
me.materials.clear()
for c in ((0.75, 0.72, 0.65, 1), (0.95, 0.9, 0.7, 1)):
    m = bpy.data.materials.new('m'); m.diffuse_color = c; me.materials.append(m)
for p in me.polygons:
    p.material_index = int(pv[p.vertices[0]] in (6, 7, 8, 9))
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
e = J['R_Forearm']
common.render_views(outp, e[2] - 0.05, 0.3, views=('front', 'three_quarter', 'right', 'back'), resolution=(500, 500), target=(e[0], e[1]))
