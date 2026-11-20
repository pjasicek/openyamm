"""Retexture upload of the reduced archer (export/mm6_arc1.glb): LOD0 body at rest, armature removed, the installed
atlas UVs (TEXCOORD_0) kept for enable_original_uv; head faces included so Meshy sees the whole figure (only body
texels are used). Saves work/retex.blend (object 'Archer', for the AO bake) and texturing/arc1_body_upload_g3r66.glb."""
import bpy, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'export', 'mm6_arc1.glb'))
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Archer')
for o in [o for o in bpy.data.objects if o != body]:
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(body.modifiers):
    body.modifiers.remove(m)
body.parent = None
body.vertex_groups.clear()
body.data.transform(body.matrix_world); body.matrix_world.identity()
for l in [l.name for l in body.data.uv_layers][1:]:
    body.data.uv_layers.remove(body.data.uv_layers[l])
mat = bpy.data.materials.new('Neutral'); mat.use_nodes = True
body.data.materials.clear(); body.data.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'retex.blend'))
body.select_set(True); bpy.context.view_layer.objects.active = body
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'arc1_body_upload_g3r66.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_animations=False, export_skins=False,
                          export_morph=False, export_attributes=False)
print('UPLOAD', len(body.data.polygons), 'faces', [l.name for l in body.data.uv_layers])
