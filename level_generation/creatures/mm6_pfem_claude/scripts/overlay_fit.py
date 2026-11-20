"""Overlay MPFB body silhouette on the Meshy detail mesh (same ortho cameras) for proportion fitting."""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
body_blend = args[0] if args else os.path.join(common.WORK, 'body_v1.blend')
tag = args[1] if len(args) > 1 else 'v1'
bpy.ops.wm.open_mainfile(filepath=body_blend)
body = [o for o in bpy.data.objects if o.type == 'MESH']
blo, bhi = common.world_bounds(body)
bpy.ops.import_scene.gltf(filepath=os.path.join(common.PROJECT, 'meshy/detail_source_v1/model_urls_glb.glb'))
meshy = bpy.data.objects['Mesh_0']
mlo, mhi = common.world_bounds([meshy])
# Meshy: shoe sole ~1.5 cm below bare sole, hair ~1.5 cm above skull.
s = (bhi.z - blo.z + 0.03) / (mhi.z - mlo.z)
meshy.scale = (s, s, s)
meshy.location = (-(mlo.x + mhi.x) / 2 * s, -(mlo.y + mhi.y) / 2 * s + (blo.y + bhi.y) / 2 * 0, -mlo.z * s - 0.015)
bpy.context.view_layer.update()
mlo, mhi = common.world_bounds([meshy])
print('MESHY_FIT', s, tuple(mlo), tuple(mhi), 'BODY', tuple(blo), tuple(bhi))
scene = bpy.context.scene
common.workbench_clay(scene)
scene.display.shading.color_type = 'OBJECT'
scene.render.film_transparent = True
cz, hh = (mlo.z + mhi.z) / 2, (mhi.z - mlo.z) * 1.06
for o in body: o.hide_render = True
common.render_views(os.path.join(common.REVIEW, f'fit_{tag}_meshy'), cz, hh)
for o in body: o.hide_render = False
meshy.hide_render = True
common.render_views(os.path.join(common.REVIEW, f'fit_{tag}_body'), cz, hh)
