"""Clay render of the 'Body' of a blend coloured by its 'piece' attribute (rest pose): review/<tag>_<view>.png.
Args: -- <blend> <tag> [views comma list]"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, tag = a[0], a[1]
views = tuple(a[2].split(',')) if len(a) > 2 else ('front', 'three_quarter', 'left', 'back')
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
for o in bpy.data.objects:
    if o.type == 'ARMATURE' and o.animation_data:
        o.animation_data.action = None
        for pb in o.pose.bones:
            pb.matrix_basis.identity()
body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
me.materials.clear()
rng = np.random.default_rng(3)
pieces = sorted(set(pv.tolist()))
idx = {p: i for i, p in enumerate(pieces)}
for p in pieces:
    m = bpy.data.materials.new(f'p{p}')
    m.diffuse_color = (0.78, 0.62, 0.55, 1) if p == 0 else tuple(rng.uniform(0.25, 0.95, 3)) + (1,)
    me.materials.append(m)
for poly in me.polygons:
    poly.material_index = idx[pv[poly.vertices[0]]]
    poly.use_smooth = True
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'MATERIAL'
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
H = float(co[:, 2].max())
common.render_views(os.path.join(common.REVIEW, tag), H / 2, H * 1.05, views=views, resolution=(600, 900))
