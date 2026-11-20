"""Make an unrigged neutral upload with the selected topology, UVs and independent eye regions."""
import hashlib
import json
from pathlib import Path

import bpy

stage = Path(__file__).resolve().parent
master = stage.parent / 'attack_windup_20261006/mm6_demon_animation_master.blend'
bpy.ops.wm.open_mainfile(filepath=str(master))
body = next(o for o in bpy.context.scene.objects if o.type == 'MESH' and o.get('material_role') == 'body')
scene = bpy.data.scenes.new('Demon_Neutral_Texture_Upload')
bpy.context.window.scene = scene
upload = bpy.data.objects.new('Demon_Neutral_Texture_Upload', body.data.copy())
scene.collection.objects.link(upload)
upload.matrix_world = body.matrix_world.copy()
original_slots = [m.name for m in upload.data.materials]
for index, original in enumerate(list(upload.data.materials)):
    material = bpy.data.materials.new(original.name.replace('Red_Iris', 'Iris') + '_Neutral_Upload')
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    color = (0.002, 0.002, 0.002, 1) if 'Pupil' in original.name else (0.6, 0.6, 0.6, 1)
    shader.inputs['Base Color'].default_value = color
    shader.inputs['Roughness'].default_value = .22 if 'Iris' in original.name else .8
    material.diffuse_color = color
    upload.data.materials[index] = material
bpy.context.view_layer.objects.active = upload
upload.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(stage / 'demon_neutral_upload.glb'), export_format='GLB',
    use_selection=True, use_active_scene=True, export_animations=False, export_skins=False,
    export_morph=False, export_texcoords=True, export_normals=True, export_cameras=False, export_lights=False)
(stage / 'upload.json').write_text(json.dumps({'master': str(master),
    'master_sha256': hashlib.sha256(master.read_bytes()).hexdigest(), 'material_regions': original_slots,
    'triangles': sum(len(p.vertices) - 2 for p in upload.data.polygons),
    'uv_layers': [u.name for u in upload.data.uv_layers],
    'upload_sha256': hashlib.sha256((stage / 'demon_neutral_upload.glb').read_bytes()).hexdigest(),
    'note': 'Neutral irises and separate black pupils; returned eye paint will not override variant iris materials.'},
    indent=2) + '\n')
print('Neutral body-only upload exported with independent irises/pupils; current animated master preserved.')
