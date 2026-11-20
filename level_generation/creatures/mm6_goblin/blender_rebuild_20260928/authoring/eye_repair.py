"""Apply the localized imagegen repair and restore materials on the actual modeled eyes."""
import json

import bpy

from mesh_tools import ROOT


def apply():
    folder = ROOT / 'textures/eye_repair_20260928'
    replacements = {}
    for role in ['base_color', 'normal', 'metallic_roughness']:
        name = 'GB15 Eye repair ' + role
        image = bpy.data.images.get(name)
        if image is None:
            image = bpy.data.images.load(str(folder / (role + '.png')), check_existing=True)
        image.name = name
        image.colorspace_settings.name = 'sRGB' if role == 'base_color' else 'Non-Color'
        if not image.packed_file:
            image.pack()
        replacements[role] = image
    for material in bpy.data.materials:
        if material.get('gb_texture_revision') != 'meshy_20260928':
            continue
        for node in material.node_tree.nodes:
            if node.type != 'TEX_IMAGE' or node.image is None:
                continue
            role = next((r for r in replacements if node.image.name in
                         ['GB15 Meshy ' + r, 'GB15 Eye repair ' + r]), None)
            if role:
                node.image = replacements[role]
        material['gb_local_eye_repair'] = 'eye_repair_20260928'
    eyes = [('GB15 Eyes', 'GB15 Eyes'), ('GB15 Irises', 'GB15 Amber irises'), ('GB15 Pupils', 'GB15 Pupils')]
    for object_name, original in eyes:
        name = original + ' restored'
        material = bpy.data.materials.get(name)
        if material is None:
            material = bpy.data.materials[original].copy()
            material.name = name
        material['gb_eye_repair'] = 'Aligned modeled eye surface; no duplicate paint or skin normals'
        bpy.data.objects[object_name].data.materials[0] = material
    bpy.data.scenes['MM6 Goblin - Authored 15K']['gb_eye_feet_revision'] = 'eyes_feet_4'
    (folder / 'material_assignment.json').write_text(json.dumps({
        'maps': {role: image.filepath for role, image in replacements.items()},
        'eye_materials': {name: original + ' restored' for name, original in eyes},
        'eye_shading': 'Authored olive sclera, amber iris and dark pupil; separate aligned model surfaces.',
        'geometry_uvs_weights_unchanged': True}, indent=2) + '\n')
    print('Applied localized color/PBR cleanup and the three aligned eye materials.')
