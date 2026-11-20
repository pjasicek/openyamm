"""Keep the selected animation master and update only packed material images and normal strength."""
from pathlib import Path
import bpy

stage = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(stage.parent / 'expression_20261006/mm6_demon_expression_master.blend'))
names = ('Demon_Meshy_Body', 'demon_b_Meshy_Body', 'demon_c_Meshy_Body', 'Demon_White_Claws')
for name in names:
    material = bpy.data.materials[name]
    shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    for slot, suffix, color_space in [('Base Color', 'base', 'sRGB'), ('Roughness', 'roughness', 'Non-Color')]:
        if name == 'Demon_White_Claws' and slot == 'Base Color':
            continue
        path = stage / f'{name}_{suffix}.png'
        image = bpy.data.images.load(str(path), check_existing=False)
        image.colorspace_settings.name = color_space
        image.pack()
        links = shader.inputs[slot].links
        node = links[0].from_node if links and links[0].from_node.type == 'TEX_IMAGE' else None
        if node is None:
            for link in list(links):
                material.node_tree.links.remove(link)
            node = material.node_tree.nodes.new('ShaderNodeTexImage')
            material.node_tree.links.new(node.outputs['Color'], shader.inputs[slot])
        node.image = image
    if name != 'Demon_White_Claws':
        next(node for node in material.node_tree.nodes if node.type == 'NORMAL_MAP').inputs['Strength'].default_value = .75
    print(name, 'updated packed maps')
# Remove superseded image datablocks only if nothing in the master uses them.
for image in list(bpy.data.images):
    if image.users == 0:
        bpy.data.images.remove(image)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'mm6_demon_materials_master.blend'), compress=True)
print('Saved material master with the selected mesh, rig, UVs, sockets and all animation curves intact.')
