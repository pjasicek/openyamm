"""Top and underside views of the raw Smart Topology return (review/raw_top.png, raw_under.png) and the raw
pieces' boxes."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v2/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = 'Dillo'
C.render((0, 0, 5), (0, 0, 0), 1.15, os.path.join(HERE, 'review', 'raw2_top.png'), res=(700, 700), floor=False)
C.render((0, 0, -5), (0, 0, 0), 1.15, os.path.join(HERE, 'review', 'raw2_under.png'), res=(700, 700), floor=False)
C.render((-5, 0, 0), (0, 0, 0), 1.15, os.path.join(HERE, 'review', 'raw2_side2.png'), res=(700, 400), floor=False)
