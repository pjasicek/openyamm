"""Real belt loops with separate hardware; the misclassified gem item211 is a closed spellbook.

blender --background --python build_belts_book.py -- [icon ...]
"""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_jewellery as j
from surface_detail import engrave, trim_material

PROJECT = j.PROJECT
BELTS = {
    '7item100': ('brown', 'silver', 'buckle', 'round', .22),
    '7item101': ('tan', 'gold', 'buckle', 'cross', .20),
    '7item102': ('brown', 'silver', 'buckle_square', 'diamond', .24),
    '7item103': ('black', 'silver', 'panels', 'silver', .20),
    '7item104': ('tan', 'gold', 'medallions', 'gold', .22),
    '7item324': ('brown', 'gold', 'skull', 'blue', .24),
    'belt1a': ('brown', 'silver', 'buckle', 'round', .22),
    'belt2a': ('green', 'silver', 'sun', 'bars', .24),
    'belt3a': ('red', 'gold', 'gem', 'yellow', .22),
    'belt4a': ('pink', 'gold', 'gem', 'bars', .22),
    'belt5a': ('blue', 'silver', 'gems', 'blue', .24),
    'item117': ('brown', 'silver', 'coin', 'round', .15),
    'item118': ('brown', 'gold', 'buckle_square', 'round', .23),
    'item119': ('black', 'silver', 'wyvern', 'diamond', .23),
    'item120': ('black', 'gold', 'star', 'diamond', .15),
    'item121': ('black', 'gold', 'skull', 'silver', .20),
    'item259': ('brown', 'gold', 'panels', 'red', .24),
    'item339': ('black', 'gold', 'skull', 'silver', .20),
}


def texture_material(name, path, rough=.7, colour='dark'):
    mat = j.material(colour).copy()
    mat.name = name
    shader = mat.node_tree.nodes['Principled BSDF']
    shader.inputs['Metallic'].default_value = 0
    shader.inputs['Roughness'].default_value = rough
    texture = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(str(path), check_existing=True)
    mat.node_tree.links.new(texture.outputs['Color'], shader.inputs['Base Color'])
    return mat


def transform_group(before, matrix):
    bpy.context.view_layer.update()
    for obj in list(bpy.context.scene.objects):
        if obj.name not in before:
            obj.matrix_world = matrix @ obj.matrix_world


def belt(icon):
    lining, metal, style, detail, height = BELTS[icon]
    strap = j.hoop('Solid leather strap', .51, .36, height / 2, .018, height, 'dark')
    strap.data.materials.clear()
    exterior = 'black' if lining == 'black' else ('tan' if icon == '7item101' else 'brown')
    strap.data.materials.append(texture_material('Leather exterior', PROJECT / f'textures/leather_{exterior}.png'))
    strap.data.materials.append(texture_material('Lining ' + lining, PROJECT / f'textures/leather_{lining}.png'))
    pattern = {'7item104': 0, '7item324': 2, 'belt3a': 2, 'belt5a': 3, 'item121': 1, 'item339': 1}.get(icon)
    if pattern is not None:
        strap.data.materials.append(trim_material(pattern, band=True))
    uv = strap.data.uv_layers.new(name='Unrolled strap')
    for face in strap.data.polygons:
        indices = list(face.vertices)
        sections = [index // 8 for index in indices]
        seam = max(sections) - min(sections) > 16
        for loop_index in face.loop_indices:
            index = strap.data.loops[loop_index].vertex_index
            section, profile = divmod(index, 8)
            u = (32 if seam and section == 0 else section) / 32
            point = strap.data.vertices[index].co
            uv.data[loop_index].uv = (.01 + .98 * u, .02 + .96 * point.z / height)
        # The inner wall has negative radial profile offsets; edge leather remains brown.
        face.material_index = 1 if all(index % 8 in (0, 5, 6, 7) for index in indices) else 0
        if pattern is not None and all(index % 8 in (1, 2, 3, 4) for index in indices):
            face.material_index = 2
    if icon in {'7item101', '7item104', '7item324', 'belt4a', 'belt5a', 'item120', 'item121', 'item339'}:
        for z in (.015, height - .015):
            j.hoop('Edge piping', .523, .373, z, .009, .018, metal, 24)
    # Decorations live in their own local XY plane; turn them outward onto the strap.
    count = 6 if style == 'medallions' else (8 if style in {'panels', 'gems'} else 1)
    for i in range(count):
        a = -math.pi / 2 + j.TAU * i / count
        before = {o.name for o in bpy.context.scene.objects}
        if style in {'buckle', 'buckle_square'}:
            if style == 'buckle':
                j.hoop('Open buckle', .085, .12, .025, .014, .027, metal, 16)
            else:
                for x in ((-.08,) if icon == 'item118' else (-.08, .08)):
                    j.box('Buckle upright', (x, 0, .025), (.025, .22, .028), metal, .007)
                for y in (-.10, .10):
                    j.box('Buckle rail', (0, y, .025), (.17, .024, .028), metal, .007)
            j.box('Buckle tongue', (.02, 0, .045), (.12, .016, .018), metal, .005)
            if icon == '7item102':
                j.plate('Loose leather tail', [(-.06, .04), (-.015, .06), (.02, -.08),
                                              (-.035, -.12), (-.01, -.06)], .048, .018, 'bronze')
        elif style in {'panels', 'medallions'}:
            shape = 'emerald' if style == 'panels' else 'octagon'
            plaque = j.stone('Metal plaque', (0, 0, 0), (.26, height * 1.08, .045), metal, shape)
            engrave(plaque, 6 if style == 'medallions' else (5 if icon == '7item103' else 4))
            if icon == 'item259':
                j.setting(0, 0, .04, .11, height * .65, detail, metal)
            if style == 'medallions':
                j.hoop('Medallion rim', .123, height * .50, .04, .006, .012, metal, 12)
        elif style in {'skull', 'wyvern'}:
            j.stone('Skull backing', (0, 0, -.01), (.25, .24, .035), metal, 'round')
            j.skull(.025, metal, style == 'wyvern')
        elif style == 'sun':
            j.stone('Round silver buckle', (0, 0, 0), (.25, .25, .035), metal)
            star = [(math.cos(j.TAU * k / 16) * (.095 if k % 2 == 0 else .035),
                     math.sin(j.TAU * k / 16) * (.095 if k % 2 == 0 else .035)) for k in range(16)]
            j.plate('Compass emblem', star, .04, .015, 'gold')
        elif style in {'gem', 'gems'}:
            colour = 'cyan' if icon == 'belt4a' else ('green' if icon == 'belt3a' else 'blue')
            j.stone('Diamond bezel', (0, 0, 0), (.17, .29, .04), metal, 'square')
            j.stone('Diamond jewel', (0, 0, .035), (.12, .23, .045), colour, 'square')
        elif style == 'coin':
            j.stone('Silver coin clasp', (0, 0, 0), (.17, .17, .04), metal)
            j.stone('Coin emboss', (0, 0, .04), (.08, .10, .025), metal, 'hexagon')
        elif style == 'star':
            j.plate('Pointed steel clasp', [(-.25, 0), (-.15, .055), (0, .16), (.15, .055),
                                           (.25, 0), (.15, -.055), (0, -.16), (-.15, -.055)], 0, .03, 'dark')
            star = [(math.cos(j.TAU * k / 16) * (.14 if k % 2 == 0 else .024),
                     math.sin(j.TAU * k / 16) * (.14 if k % 2 == 0 else .024)) for k in range(16)]
            j.plate('Eight-point star', star, .032, .015, metal)
        centre = Vector((.54 * math.cos(a), .39 * math.sin(a), height / 2))
        matrix = Matrix.Translation(centre) @ Matrix.Rotation(a + math.pi / 2, 4, 'Z')
        matrix @= Matrix.Rotation(math.pi / 2, 4, 'X')
        transform_group(before, matrix)
    if count == 1:
        for i in range(12):
            a = -math.pi / 2 + j.TAU * (i + 1) / 13
            before = {o.name for o in bpy.context.scene.objects}
            if detail == 'diamond':
                j.stone('Diamond stud', (0, 0, 0), (.055, .075, .025), metal, 'square')
            elif detail == 'cross':
                j.box('Cross horizontal', (0, 0, .012), (.065, .018, .018), 'dark', .003)
                j.box('Cross vertical', (0, 0, .012), (.018, .075, .018), 'dark', .003)
            elif detail == 'bars':
                j.box('Metal bar', (0, 0, .01), (.025, .15, .028), metal, .006)
            elif detail in {'blue', 'silver'}:
                j.stone('Band inlay', (0, 0, .01), (.075, .08, .025), detail, 'square')
            else:
                for y in (-height * .28, height * .28):
                    j.ball('Rivet', (0, y, .014), (.021, .021, .016), metal, 1)
            matrix = Matrix.Translation((.535 * math.cos(a), .385 * math.sin(a), height / 2))
            matrix @= Matrix.Rotation(a + math.pi / 2, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'X')
            transform_group(before, matrix)
    if icon == 'belt5a':
        # The Sovereign icon has broad silver chevrons, rather than a plain strap between its sapphires.
        for i in range(8):
            a = -math.pi / 2 + j.TAU * (i + .5) / 8
            before = {o.name for o in bpy.context.scene.objects}
            for side in (-1, 1):
                j.tube('Silver chevron', [(-.11, side * .06, .01), (0, side * .025, .025),
                                         (.11, side * .06, .01)], .016, 'silver')
            matrix = Matrix.Translation((.54 * math.cos(a), .39 * math.sin(a), height / 2))
            matrix @= Matrix.Rotation(a + math.pi / 2, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'X')
            transform_group(before, matrix)
    return Matrix.Identity(4)


def book():
    j.PALETTE['book_leather'] = ('442067', 0, .72)
    cover = texture_material('Painted purple cover', PROJECT / 'textures/jewellery_item211_cover.png')
    packed = cover.node_tree.nodes.new('ShaderNodeTexImage')
    packed.image = bpy.data.images.load(str(PROJECT / 'textures/jewellery_item211_mr.png'))
    packed.image.colorspace_settings.name = 'Non-Color'
    channels = cover.node_tree.nodes.new('ShaderNodeSeparateColor')
    shader = cover.node_tree.nodes['Principled BSDF']
    cover.node_tree.links.new(packed.outputs['Color'], channels.inputs['Color'])
    cover.node_tree.links.new(channels.outputs['Green'], shader.inputs['Roughness'])
    cover.node_tree.links.new(channels.outputs['Blue'], shader.inputs['Metallic'])
    for z in (.018, .215):
        board = j.box('Purple cover board', (0, 0, z), (.78, 1, .036), 'book_leather', .008)
        board.data.materials.append(cover)
        uv = board.data.uv_layers.active
        for face in board.data.polygons:
            if face.normal.z > .9:
                face.material_index = 1
                for loop_index in face.loop_indices:
                    v = board.data.vertices[board.data.loops[loop_index].vertex_index].co
                    uv.data[loop_index].uv = (v.x / .78 + .5, v.y + .5)
    pages = j.box('Page block', (.008, 0, .116), (.72, .95, .16), 'pearl', .008)
    pages.data.materials.clear()
    pages.data.materials.append(texture_material('Ivory page edges', PROJECT / 'textures/jewellery_pages.png', .85))
    # Height drives page lines on every visible page-block side.
    uv = pages.data.uv_layers.active
    for face in pages.data.polygons:
        for loop_index in face.loop_indices:
            point = pages.data.vertices[pages.data.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv = ((point.x / .72 + .5) if abs(face.normal.y) > .5 else point.y / .95 + .5,
                                    point.z / .16 + .5)
    j.box('Rounded purple spine', (-.38, 0, .116), (.06, 1, .23), 'book_leather', .025)
    return Matrix.Identity(4)


args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
only = set(args)
receipts = PROJECT / 'work/build_receipts.json'
records = json.loads(receipts.read_text()) if receipts.exists() else {}
for row in json.loads((PROJECT / 'ownership.json').read_text()):
    icon = row['icon']
    if (only and icon not in only) or (row['family'] != 'belts' and icon != 'item211'):
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    j.MATERIALS.clear()
    rotation = book() if icon == 'item211' else belt(icon)
    records[icon] = j.finish(row, rotation)
    receipts.write_text(json.dumps(records, indent=2) + '\n')
    print('BUILT', icon, records[icon]['triangles'], flush=True)
