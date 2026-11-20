"""Import the Meshy detail source, normalise to 1.0 m height at origin, report and render textured turnaround."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
common.clear_scene()
src = os.path.join(common.PROJECT, 'meshy/detail_source_v1/model_urls_glb.glb')
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in bpy.context.scene.objects:
    print('OBJ', o.name, o.type, o.parent.name if o.parent else None, tuple(o.location), tuple(o.rotation_euler), tuple(o.scale))
for o in meshes:
    print('MESH', o.name, len(o.data.vertices), len(o.data.polygons), [m.name for m in o.data.materials], len(o.data.uv_layers))
lo, hi = common.world_bounds(meshes)
print('BOUNDS', tuple(lo), tuple(hi))
scene = bpy.context.scene
common.workbench_clay(scene, textured=True)
common.render_views(os.path.join(common.REVIEW, 'meshy_v1_tex'), (lo.z + hi.z) / 2, (hi.z - lo.z) * 1.08,
                    target=((lo.x + hi.x) / 2, (lo.y + hi.y) / 2))
common.workbench_clay(scene, textured=False)
common.render_views(os.path.join(common.REVIEW, 'meshy_v1_clay'), (lo.z + hi.z) / 2, (hi.z - lo.z) * 1.08,
                    target=((lo.x + hi.x) / 2, (lo.y + hi.y) / 2))
