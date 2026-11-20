"""Small isolated Blender bake/export check; these synthetic fixtures are never installed."""
import json
from pathlib import Path
import sys

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codex_texture as texture

assert texture.registration_ok(461, 485)
assert texture.registration_ok(58, 61)
assert not texture.registration_ok(100, 106)
assert not texture.registration_ok(890, 956)

project = Path(__file__).resolve().parents[1]
root = project / 'work' / 'mask_selfcheck'
root.mkdir(parents=True, exist_ok=True)
texture.WORK = str(root)
texture.PAINT = str(root / 'paint')
texture.TEXTURE = 64
name = 'equipment_mask_selfcheck'
texture.DESIGNS[name] = {'unseen_material': 'leather', 'normal': 0.0}
folder = Path(texture.PAINT) / name
folder.mkdir(parents=True, exist_ok=True)
# Class masks are data: sRGB decoding would turn an antialiased red/blue boundary into an invalid dark colour.
bpy.ops.wm.read_factory_settings(use_empty=True)
edge = np.full((8, 8, 3), [0.5, 0.0, 0.5], np.float32)
edge_path = folder / 'mask_edge.png'
texture.save_png(edge, str(edge_path), 'Non-Color')
loaded_edge = texture.load_rgba(str(edge_path), non_color=True)
assert np.max(np.abs(loaded_edge[..., :3] - edge)) < 0.005
texture.masks.classify(loaded_edge[..., :3].reshape(-1, 3))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
obj = bpy.context.object
obj.name = name
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.uv.smart_project(island_margin=0.05)
bpy.ops.object.mode_set(mode='OBJECT')
(folder / 'views.json').write_text(json.dumps({'centre': [0, 0, 0.5], 'scale': 1.15, 'size': 64}))
for view in texture.VIEWS:
    colour = np.full((64, 64, 3), 0.25, np.float32)
    texture.save_png(colour, str(folder / f'guide_{view}.png'))
    texture.save_png(colour, str(folder / f'paint_{view}.png'))
    mask = np.zeros((64, 64, 3), np.float32)
    mask[..., 0 if view in ('front', 'top') else 1] = 1
    texture.save_png(mask, str(folder / f'mask_{view}.png'), 'Non-Color')
bpy.ops.wm.save_as_mainfile(filepath=str(root / f'{name}.blend'))
texture.bake(name)
image = bpy.data.images.load(str(root / 'textures' / f'{name}_mr.png'), check_existing=False)
image.colorspace_settings.name = 'Non-Color'
pixels = np.asarray(image.pixels[:]).reshape(64, 64, 4)
assert np.any(pixels[..., 2] > 0.99), 'Metal disappeared from the bake'
assert np.any(pixels[..., 2] < 0.01), 'Leather became metal'
assert np.any(np.abs(pixels[..., 1] - 0.35) < 0.01), 'Metal roughness was lost'
assert np.any(np.abs(pixels[..., 1] - 0.6) < 0.01), 'Leather roughness was lost'
export = root / f'{name}_export.glb'
assert export.is_file()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(export))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
assert len(meshes) == 1 and meshes[0].data.uv_layers
meshes[0].data.calc_loop_triangles()
assert len(meshes[0].data.loop_triangles) == 12
print('MASK_BAKE_SELF_CHECK_PASSED: metal/leather channels, roughness, GLB re-import, UVs and 12 triangles.')

from thicken_trial import thicken
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_plane_add(size=1)
plane = bpy.context.object
metal = bpy.data.materials.new('outer_metal')
metal.use_nodes = True
plane.data.materials.append(metal)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.uv.smart_project()
bpy.ops.object.mode_set(mode='OBJECT')
plane = thicken(plane, 0.004, {'kind': 'cloth', 'colour': [0.04, 0.03, 0.02]})
assert len(plane.data.materials) == 2
assert {face.material_index for face in plane.data.polygons} == {0, 1}
lining_shader = next(node for node in plane.data.materials[1].node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
assert lining_shader.inputs['Metallic'].default_value == 0
assert abs(lining_shader.inputs['Roughness'].default_value - 0.85) < 0.001
print('PHYSICAL_LINING_SELF_CHECK_PASSED: real shell with separate cloth material.')

bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new('triangle_texel_domain')
mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
obj = bpy.data.objects.new('triangle_texel_domain', mesh)
bpy.context.scene.collection.objects.link(obj)
uv = mesh.uv_layers.new()
for loop, coordinate in zip(uv.data, [(0, 0), (1, 0), (0, 1)]):
    loop.uv = coordinate
pixels, positions, normals = texture.texels(obj)
assert len(pixels) > 100
assert positions[:, :2].min() >= -1e-8
assert np.max(positions[:, 0] + positions[:, 1]) <= 1 + 1e-8
print('TEXEL_DOMAIN_SELF_CHECK_PASSED: samples stay inside the mesh triangle; no projected gutter points.')
labels = mesh.attributes.new(name='ground_material_class', type='INT', domain='FACE')
labels.data[0].value = 2
_, _, _, classes = texture.texels(obj, with_classes=True)
assert np.all(classes == 2)
obj.data.materials.append(bpy.data.materials.new('cloth_surface'))
obj = thicken(obj, 0.004)
assert obj.data.attributes.get('ground_material_class')
assert {label.value for label in obj.data.attributes['ground_material_class'].data} == {2}
print('MESH_MATERIAL_SELF_CHECK_PASSED: per-face cloth IDs survive physical thickness and texel sampling.')
