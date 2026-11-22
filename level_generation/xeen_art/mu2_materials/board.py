#!/usr/bin/env python3
"""MU-2 material boards (devdocs/xeen/PRODUCTION.md §4): per Xeen surface map the proposed ground materials (the
engine's terrain material library), the dressing (shipped decorations, from the reference maps' own counts in
dressing.json) and in-game views of the shipped reference maps (capture.py), with Xeen's native surface and wall
sprites beside them as references only. Writes board_mu2.png and choices.yml (the same choices as data for the map
lanes' terrain_materials and decoration passes)."""
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
XEEN = ROOT / 'reference/mm4_5_world_of_xeen/unpacked/sprites'
LIB = ROOT / 'assets_source/engine/terrain_materials'
HESPER_ONLY = {'slag_crust', 'slag_molten', 'glass_obsidian', 'resin_paving'}

# key, name, biome words, native refs (face/sprite), reference maps, layers (library, role, tint), dressing, gaps
MAPS = [
    ('X1', 'Vertigo Meadows', 'green meadow, orchards, river delta, a dead forest in the south-west, rim cliffs east',
     ['xeen/grass.srf', 'xeen/dirt.srf', 'xeen/road.srf', 'xeen/ltree.wal', 'xeen/dedltree.wal'],
     ['mm7/7out02.odm', 'mm7/out11.odm'],
     [('grass_meadow', 'meadow', None), ('grass_patchy', 'pasture', None), ('soil', 'fields, lanes', None),
      ('road_pebbles', 'roads', None), ('swamp', 'Toad Meadow', None), ('rock_cliff', 'cliffs, rim', None)],
     ['7tree16', '7tree13', '7tree22', 'tree38 (fruit)', 'flower01', 'flower02', 'flower06', '7rock09', '7rock01',
      'tree41, tree42 (dead forest)'],
     'Rim cliff face below the meadow: rock_cliff tinted pale (white cliffs).'),
    ('X2', 'Rivercity and Lake Darzog', 'broad river and lake, farmland north, fairy woods south, rim south',
     ['xeen/grass.srf', 'xeen/water.srf', 'xeen/road.srf', 'xeen/ltree.wal'],
     ['mm7/7out03.odm'],
     [('grass_meadow', 'meadow', None), ('soil', 'farmland', None), ('road_flagstone', 'city streets', None),
      ('road_pebbles', 'roads', None), ('sand_ripples', 'river banks', None), ('rock_cliff', 'cliffs, rim', None)],
     ['7tree19', '7tree28', '7tree25', 'flower03', 'flower04', 'flower05', 'flower08', 'flower11', '7rock08',
      '7rock09'], 'Fairy woods: denser 7tree28 and flower clusters, no new art.'),
    ('X3', 'Lifeforce Lagoon', 'swamp and lagoon, marsh woods, mist over Nightshadow',
     ['xeen/swamp.srf', 'xeen/grass.srf', 'xeen/dwater.srf', 'xeen/dtree.wal'],
     ['mm7/7out13.odm#6', 'mm7/7out13.odm#2'],
     [('swamp', 'marsh', None), ('mud_cracked', 'mud flats', [0.8, 0.85, 0.75]), ('grass_patchy', 'rises', None),
      ('soil', 'paths', None), ('road_pebbles', 'Nightshadow streets', None), ('rock_cliff', 'cliffs', None)],
     ['swptree1', 'swptree2', 'tree60', '7tree63', 'tree65', 'tree41 (dead)', 'reeds (plants_v4 cells 4-9)'],
     'Tatalia counts tree33/tree36 too, which X1 found to be snowy firs: leave them out here.'),
    ('X4', 'Burlock Savannah', 'dry golden savannah, jousting fields, red dwarf hills, bare Gargoyle peaks north',
     ['xeen/grass.srf', 'xeen/dirt.srf', 'xeen/mount.wal', 'xeen/ltree.wal'],
     ['mm8/out03.odm'],
     [('grass_patchy', 'savannah', [1.1, 1.0, 0.75]), ('soil', 'tracks, fields', None),
      ('dirt_cracked', 'dry hollows', None), ('rock_red', 'red dwarf hills', None),
      ('rock_layered', 'Gargoyle Range', None), ('road_pebbles', 'roads', None)],
     ['tree29', 'tree30', 'tree10', 'tree11', 'tree12', 'plant26', 'plant27', 'plant22', 'plant23', 'rock17'],
     'Lava fields at the north-east edge borrow X7\'s gravel_volcanic.'),
    ('X5', 'Winterkill Tundra', 'snowfields, frozen lakes, snowy troll forest, glacier at the south-west rim',
     ['xeen/snow.srf', 'xeen/snotree.wal', 'xeen/snomnt.wal'],
     ['mm7/7out13.odm#4', 'mm7/out10.odm#1'],
     [('snow', 'snowfields', None), ('rock_ground', 'wind-scoured ground', [0.9, 0.95, 1.05]),
      ('soil_stony', 'tracks', None), ('road_pebbles', 'Winterkill streets', None), ('rock_cliff', 'glacier, rim', None)],
     ['tree33', 'tree36 (MM7 snowy firs, seen here)', '6tree17', 'snotre01', 'snotre03', '6rock03', '6rock07'],
     'Frozen lakes: the water shader with an ice tint, or an ice ground material (not in the library).'),
    ('X6', 'Desert of the Sphinx', 'dunes and red mesas, the Barbaric Mountains, dunes pouring over the west rim',
     ['xeen/desert.srf', 'xeen/palm.wal', 'xeen/mount.wal'],
     ['mm7/7out06.odm', 'mm8/out04.odm'],
     [('sand_ripples', 'dunes', None), ('sand_flat', 'pans, oasis rim', None), ('rock_red', 'mesas', None),
      ('dirt_cracked', 'bone fields', None), ('road_pebbles', 'caravan road', None)],
     ['bush13', 'bush14', 'bush15', 'bush16', '7rock08', '7rock09', 'plant50', 'plant54', 'rock07', 'rock09',
      'palms (6tree21) at the oasis'], 'Sand streaming off the rim: particles (weather), not a material.'),
    ('X7', 'Mount Firestone', 'volcanic badlands, lava rivers, ash; mild southern slopes; lava falls at the north rim',
     ['xeen/lava.srf', 'xeen/scortch.srf', 'xeen/lavamnt.wal'],
     ['mm7/out10.odm', 'mm6/outb1.odm'],
     [('gravel_volcanic', 'ash plains', None), ('ground_crust', 'lava crust', None),
      ('rock_cliff', 'cliffs', [0.6, 0.55, 0.55]), ('soil_stony', 'southern slopes', None),
      ('slag_crust', 'cooled flows (Hesper source)', None)],
     ['7rock01', '7rock02', '7rock03', '7rock04', '7rock07', 'tree41, tree42 (burnt)', 'dead bushes'],
     'slag_crust is a Hesper material, not in the engine library: add it or keep to ground_crust.'),
    ('D1', 'Castleview Vale', 'river vale, desaturated grassland, the Dark Grove, an acid pond, melon fields',
     ['dark/grass.srf', 'dark/road.srf', 'dark/dtree.wal', 'dark/grass.wal'],
     ['mm7/out11.odm#3', 'mm7/out11.odm#5'],
     [('grass_meadow', 'vale', [0.85, 0.9, 0.85]), ('grass_patchy', 'pasture', [0.9, 0.9, 0.85]),
      ('soil', 'melon fields, lanes', None), ('road_flagstone', 'Castleview', None), ('mud_cracked', 'acid pond rim', None),
      ('rock_cliff', 'cliffs', None)],
     ['tree41', 'tree42 (Dark Grove)', '7tree19', '7tree04', '7tree25', 'flower16', '7rock08', '7rock09'],
     'The Dark Grove\'s great tree with the rope is a new model (S lane).'),
    ('D2', 'Sprite Forest and Ogre Pass', 'enchanted dark forest, glowing fungus, the great tree, gemstone foothills',
     ['dark/grass.srf', 'dark/dirt.srf', 'dark/dtree.wal', 'dark/dmount.wal'],
     ['mm8/out07.odm'],
     [('grass_meadow', 'forest floor', [0.75, 0.85, 0.75]), ('soil', 'paths', None),
      ('rock_layered', 'gemstone foothills', None), ('soil_stony', 'Ogre Pass', None), ('rock_cliff', 'cliffs', None)],
     ['tree12', 'tree62a', 'tree10', 'tree18', 'tree11', 'tree25', 'rock16', 'plant47'],
     'Glowing mushrooms and crystal accents: new decorations (S lane); nothing shipped glows.'),
    ('D3', 'Sandcaster and the Aging Forest', 'sandstone city at the desert edge, the Crossroads, autumn forest, river',
     ['dark/desert.srf', 'dark/grass.srf', 'dark/croad.srf', 'dark/ltree.wal'],
     ['mm6/outb3.odm', 'mm7/7out04.odm'],
     [('sand_flat', 'desert edge', None), ('dirt_cracked', 'dry ground', None), ('grass_patchy', 'Aging Forest', [1.1, 0.95, 0.75]),
      ('road_flagstone', 'Sandcaster, Crossroads', None), ('soil', 'tracks', None), ('rock_cliff', 'rim', None)],
     ['6tree21', 'cac3', 'cac16', 'cac24', 'cac25', 'autumn variants of 7tree19 / 7tree28 (trees_seasonal)',
      'flower16'], 'Leaves falling all year in the Aging Forest: particles.'),
    ('D4', 'Lakeside and Blackfang', 'great dark lake and island, snow river rapids north, the Forest of Peril',
     ['dark/water.srf', 'dark/grass.srf', 'dark/snow.srf', 'dark/dsnotree.wal'],
     ['mm7/out09.odm'],
     [('grass_meadow', 'shore meadow', [0.8, 0.88, 0.9]), ('soil', 'lanes', None), ('sand_ripples', 'shore', None),
      ('snow', 'north rapids', None), ('rock_cliff', 'Blackfang crag', [0.7, 0.7, 0.75]), ('road_pebbles', 'Lakeside', None)],
     ['bush03', 'flower16', 'tree41', 'tree42', '7rock01', '7rock03', '7rock04', '7rock05', 'snotre01 (north)'],
     ''),
    ('D5', 'Desert of Doom', 'pale dunes, the Great Pyramid, the Quivering Forest, the Parabolic Barrier, snowy north',
     ['dark/desert.srf', 'dark/snow.srf', 'dark/dmount.wal'],
     ['mm8/out08.odm', 'mm8/out04.odm'],
     [('sand_ripples', 'dunes', [1.05, 1.0, 0.9]), ('dirt_cracked', 'Perishing Sands', None), ('rock_red', 'highland edge', None),
      ('snow', 'northern highlands', None), ('soil_stony', 'tracks', None)],
     ['tree62c', 'tree63b', 'tree28', 'rock10', 'rock14', 'rock24', 'plant50', 'plant54'],
     'The Parabolic Barrier is a BModel with an energy texture (ancient kit).'),
    ('D6', 'The Forbidden Zone', 'volcanic waste, Ancient ruins, crashed pods in lava, Necropolis, Castle Alamar, ash',
     ['dark/lava.srf', 'dark/scortch.srf', 'dark/tflr.srf', 'dark/dedltree.wal'],
     ['mm6/outb1.odm', 'mm8/out06.odm'],
     [('gravel_volcanic', 'ash waste', None), ('ground_crust', 'lava crust', None), ('mud_cracked', 'Necropolis grounds', [0.8, 0.8, 0.8]),
      ('rock_cliff', 'cliffs', [0.6, 0.55, 0.55]), ('road_flagstone', 'Necropolis, Alamar approach', [0.8, 0.8, 0.85]),
      ('slag_crust', 'pod scars (Hesper source)', None)],
     ['dec05', 'dec17', 'tree28', 'dec15', 'dec13', 'rock22', 'rock52', 'rock56', 'plant48'],
     'Ancient floor around the pods (Xeen tflr): a BModel apron with the ancient kit, not ground.'),
]


def font(size):
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/TTF/DejaVuSans.ttf'):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def bold(size):
    return ImageFont.truetype(str(Path(font(10).path).with_name('DejaVuSans-Bold.ttf')), size)


def native(ref, size):
    folder = XEEN / ref
    frames = sorted(folder.glob('frame_*.png'))
    if not frames:
        return None
    image = Image.open(frames[0]).convert('RGBA')
    back = Image.new('RGBA', image.size, (40, 40, 48, 255))
    back.alpha_composite(image)
    scale = size / max(image.size)
    return back.convert('RGB').resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.NEAREST)


def swatch(name, tint, size):
    image = Image.open(LIB / name / 'albedo_height.png').convert('RGB')
    side = min(image.size)
    image = image.crop((0, 0, side // 2, side // 2)).resize((size, size), Image.LANCZOS)
    if tint:
        r, g, b = image.split()
        image = Image.merge('RGB', [c.point(lambda v, f=f: min(255, int(v * f))) for c, f in zip((r, g, b), tint)])
    return image


def shot(ref, index):
    world, stem = ref.split('/')
    path = sorted((HERE / 'views' / f'{world}_{stem[:-4]}').glob(f'0{index}-*.png'))
    if not path:
        return None
    image = Image.open(path[0]).convert('RGB')
    w, h = image.size
    # Keep the middle band: the HUD sits at the top and the party portraits at the bottom.
    return image.crop((int(w * 0.03), int(h * 0.14), int(w * 0.84), int(h * 0.72)))


def wrap(text, width):
    lines, line = [], ''
    for word in text.split():
        if len(line) + len(word) + 1 > width:
            lines.append(line)
            line = word
        else:
            line = (line + ' ' + word).strip()
    return lines + [line] if line else lines


def main():
    width, row_h = 2400, 300
    board = Image.new('RGB', (width, 90 + row_h * len(MAPS)), (18, 18, 24))
    d = ImageDraw.Draw(board)
    d.text((16, 14), 'MU-2 material boards: ground materials, dressing and reference views per Xeen surface map',
           font=bold(30), fill='white')
    d.text((16, 54), 'Columns: Xeen native surface and wall sprites (references only) | proposed engine terrain materials '
                     '(tinted) | in-game views of the shipped maps the ground and dressing come from', font=font(18),
           fill=(200, 200, 210))
    choices = {}
    for i, (key, name, biome, natives, refs, layers, dressing, gap) in enumerate(MAPS):
        y = 90 + i * row_h
        d.rectangle((0, y, width, y + row_h - 6), fill=(28, 28, 36))
        d.text((12, y + 8), f'{key} {name}', font=bold(22), fill='white')
        ty = y + 40
        for line in wrap(biome, 46):
            d.text((12, ty), line, font=font(15), fill=(220, 210, 180))
            ty += 19
        ty += 4
        for line in wrap('Dressing: ' + ', '.join(dressing), 50):
            d.text((12, ty), line, font=font(14), fill=(190, 220, 190))
            ty += 18
        if gap:
            for line in wrap('Gap: ' + gap, 50):
                d.text((12, ty), line, font=font(14), fill=(240, 180, 140))
                ty += 18
        x = 470
        for ref in natives:
            image = native(ref, 82)
            if image:
                board.paste(image, (x, y + 30))
                d.text((x, y + 116), ref.split('/')[1], font=font(12), fill=(170, 170, 180))
                x += 92
        x = 470
        for j, (lib, role, tint) in enumerate(layers):
            sx = x + j * 118
            board.paste(swatch(lib, tint, 108), (sx, y + 140))
            mark = ' *' if lib in HESPER_ONLY else ''
            d.text((sx, y + 252), lib + mark, font=font(12), fill='white')
            d.text((sx, y + 268), role[:17], font=font(12), fill=(170, 170, 180))
        x = 1200
        refs_shots = []
        for k, ref in enumerate(refs if len(refs) > 1 else refs * 2):
            name, _, index = ref.partition('#')
            refs_shots.append((name, int(index) if index else (3 if k == 0 else 4)))
        for k, (ref, index) in enumerate(refs_shots):
            image = shot(ref, index)
            if image:
                image = image.resize((580, int(580 * image.height / image.width)), Image.LANCZOS)
                board.paste(image.crop((0, 0, 580, min(image.height, 262))), (x + k * 596, y + 8))
                d.text((x + k * 596 + 6, y + 272), ref, font=font(13), fill=(170, 200, 230))
        choices[key] = {'name': name, 'reference_maps': sorted({r.partition('#')[0] for r in refs}),
                        'layers': [{'library': lib, 'role': role, 'tint': tint} for lib, role, tint in layers],
                        'dressing': dressing, 'native_refs': natives, 'gap': gap}
    d.text((width - 520, 60), '* a Hesper material, not in the engine library', font=font(16), fill=(240, 180, 140))
    board.save(HERE / 'board_mu2.png')
    board.resize((width // 2, board.height // 2), Image.LANCZOS).save(HERE / 'board_mu2_small.png')
    (HERE / 'choices.yml').write_text('# MU-2 choices per Xeen surface map (board.py writes this; edit MAPS there).\n'
                                      + yaml.safe_dump(choices, sort_keys=False, width=110))
    print(board.size)


if __name__ == '__main__':
    main()
