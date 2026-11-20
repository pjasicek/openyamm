"""LOD chain for a static attachment GLB (weapon, throne): the mesh node `Name` gets decimated siblings
`Name_LOD1..3` (same transform, UVs and materials kept; a level that no longer shrinks ends the chain); the glTF
import/export round trip keeps the file's coordinates. Then run tools/link_static_model_lods.py on the result and
claude_shared/emission.py last (the round trip drops its extras).
Usage (Blender): attachment_lods.py <in.glb> <out.glb> [ratios=0.5,0.25,0.12]"""
import bpy, sys

args = sys.argv[sys.argv.index('--') + 1:]
src, out = args[0], args[1]
ratios = [float(x) for x in (args[2] if len(args) > 2 else '0.5,0.25,0.12').split(',')]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
base = next(o for o in sc.objects if o.type == 'MESH')
for o in sc.objects:
    o.select_set(False)
n0 = len(base.data.polygons); last = n0; level = 1
for r in ratios:
    o = base.copy(); o.data = base.data.copy(); o.name = f'{base.name}_LOD{level}'; sc.collection.objects.link(o)
    m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = r; m.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.modifier_apply(modifier='dec'); o.select_set(False)
    n = len(o.data.polygons)
    if n > 0.9 * last:          # the collapse cannot go lower (borders): keep the previous level as the last one
        bpy.data.objects.remove(o, do_unlink=True); break
    print('LOD', level, n, 'of', n0); last = n; level += 1
for o in sc.objects:
    o.select_set(o.type == 'MESH')
for img in bpy.data.images:          # the cook takes PNG only (Meshy textures can be JPEG)
    if img.file_format != 'PNG' and img.size[0] > 0:
        img.file_format = 'PNG'
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_yup=True,
                          export_animations=False, export_image_format='AUTO')
