"""The enthroned Hierarch's throne as a D12 decoration (export/hes_hierarch_throne_deco.glb): the fitted throne
(work/hierarch/throne_fit.blend, body units in the Hierarch's model space) scaled by the Hierarch's binding scale into
metres (1 m = 100 world units: scale / 100), origin at the actor's feet, front as the actor's (Blender -Y), with its
LODs. Placed at the Hierarch's spot (D12: build_d12.py add_throne) with his facing minus 90 degrees (a decoration
model's 0 faces +Y, an actor's +X), it sits exactly where the attachment did.
Usage (Blender): throne_decoration.py [binding_scale=286]"""
import bpy, sys
from pathlib import Path
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
scale = float(args[0]) if args else 286.0
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/hierarch/throne_fit.blend'))
sc = bpy.context.scene
th = bpy.data.objects['Throne']
for o in list(sc.objects):
    if o != th:
        bpy.data.objects.remove(o, do_unlink=True)
th.name = 'hes_hierarch_throne_deco'
th.scale = (scale / 100,) * 3
bpy.context.view_layer.objects.active = th; th.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
n0 = len(th.data.polygons); last = n0; level = 1
for r in (0.5, 0.25, 0.12):
    o = th.copy(); o.data = th.data.copy(); o.name = f'{th.name}_LOD{level}'; sc.collection.objects.link(o)
    m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = r; m.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier='dec')
    if len(o.data.polygons) > 0.9 * last:
        bpy.data.objects.remove(o, do_unlink=True); break
    last = len(o.data.polygons); level += 1
for img in bpy.data.images:
    if img.file_format != 'PNG' and img.size[0] > 0:
        img.file_format = 'PNG'
for o in sc.objects:
    o.select_set(o.type == 'MESH')
bpy.ops.export_scene.gltf(filepath=str(P / 'work/hierarch/throne_deco_raw.glb'), export_format='GLB',
                          use_selection=True, export_animations=False, export_image_format='AUTO')
print('DECO', [(o.name, len(o.data.polygons)) for o in sc.objects if o.type == 'MESH'])
