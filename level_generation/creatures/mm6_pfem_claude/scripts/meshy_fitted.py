"""Save the Meshy detail source transformed into the body frame (work/meshy_fitted.blend) + gridded renders."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
common.clear_scene()
bpy.ops.import_scene.gltf(filepath=os.path.join(common.PROJECT, 'meshy/detail_source_v1/model_urls_glb.glb'))
m = bpy.data.objects['Mesh_0']; m.name = 'MeshyDetail'
lo, hi = common.world_bounds([m])
H_BODY = 1.5590388774871826
s = (H_BODY + 0.03) / (hi.z - lo.z)
m.scale = (s, s, s)
m.location = (-(lo.x + hi.x) / 2 * s, -(lo.y + hi.y) / 2 * s, -lo.z * s - 0.015)
bpy.context.view_layer.objects.active = m
m.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
print('FIT_SCALE', s)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'meshy_fitted.blend'))
scene = bpy.context.scene
common.workbench_clay(scene, textured=True)
common.render_views(os.path.join(common.REVIEW, 'meshy_fitted'), 0.8, 1.7, views=('front', 'left', 'back'),
                    resolution=(1024, 1024))
