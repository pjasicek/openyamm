"""The missing ground-item placeholder -> work/missing_item/missing_item_export.glb.

An item lying on the ground whose icon has no model, or whose model fails to load, draws this instead of nothing or a
sprite (GROUND_ITEMS_3D_BEHAVIOUR.md section 2): a cube with a magenta and black checker on every face, unlit so it is
full-bright even in a dark dungeon. It must never pass for art. The game scales it to 40 units and turns it slowly.
Lowest point at 0, footprint centred (the item model contract). Install with
  python3 tools/install_model.py work/missing_item/missing_item_export.glb --world-items --name missing_item.glb
Usage: blender --background --factory-startup --python build_missing_item.py"""
import os

import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(HERE, 'work', 'missing_item', 'missing_item_export.glb')
TEXTURE = os.path.join(HERE, 'work', 'missing_item', 'missing_item_checker.png')
TEXTURE_SIZE = 64
CHECKS = 4
MAGENTA = (1.0, 0.0, 1.0)


def checker_image():
    """A 4 x 4 magenta and black checker, drawn without filtering."""
    cell = TEXTURE_SIZE // CHECKS
    y, x = np.mgrid[0:TEXTURE_SIZE, 0:TEXTURE_SIZE]
    magenta = ((x // cell + y // cell) % 2 == 0)
    pixels = np.zeros((TEXTURE_SIZE, TEXTURE_SIZE, 4), dtype=np.float32)
    pixels[magenta, 0:3] = MAGENTA
    pixels[..., 3] = 1.0
    image = bpy.data.images.new('missing_item_checker', TEXTURE_SIZE, TEXTURE_SIZE, alpha=False)
    image.pixels = pixels.ravel()
    image.filepath_raw = TEXTURE
    image.file_format = 'PNG'
    image.save()
    return image


def checker_material(image):
    """Unlit (KHR_materials_unlit, from a Background shader), so the checker is full-bright in any light."""
    material = bpy.data.materials.new('missing_item')
    material.use_nodes = True
    # A closed cube: single-sided.
    material.use_backface_culling = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.remove(nodes['Principled BSDF'])
    shader = nodes.new('ShaderNodeBackground')
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = image
    texture.interpolation = 'Closest'
    links.new(texture.outputs['Color'], shader.inputs['Color'])
    links.new(shader.outputs['Background'], nodes['Material Output'].inputs['Surface'])
    return material


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    # A unit cube from z = 0 to 2 (Blender Z up; glTF Y up after export), each face carrying the whole checker.
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 1.0))
    cube = bpy.context.active_object
    cube.name = 'missing_item'
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.reset()
    bpy.ops.object.mode_set(mode='OBJECT')
    cube.data.materials.append(checker_material(checker_image()))
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT,
        export_format='GLB',
        use_selection=False,
        export_yup=True,
        export_apply=True,
        export_normals=True,
        export_texcoords=True,
        export_materials='EXPORT',
        export_animations=False,
    )
    print(f'wrote {OUTPUT}')


if __name__ == '__main__':
    main()
