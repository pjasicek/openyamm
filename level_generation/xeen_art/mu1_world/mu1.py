#!/usr/bin/env python3
"""MU-1 world boards for Xeen (devdocs/xeen/PRODUCTION.md §4): a painted map of each face with the rim and the sky
layer, beside the region schematic of WORLD_DESIGN §3.1.

  mu1.py guides            layout guides (guide_<face>.png): the face's regions in their biome colours, landmarks,
                           the rim and the sky islands, at the canvas size the painting is made at
  mu1.py paint FACE [--note TEXT]   one `codex exec` image call (raw/<face>_vN.png, prompt beside it)
  mu1.py board [--pick cloudside=N darkside=N]   board_mu1.png: both paintings with labels, beside the schematics

The painting is Codex image generation only, one call per image, with the layout guide and the stitched native map
of the face (the original game's outdoor squares, a reference for geography only) as reference images.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W, H = 1536, 1024
# The face occupies this box of the canvas; the rest is the starfield beyond the rim.
FX0, FY0, FX1, FY1 = 96, 112, 1440, 944
COLS, ROWS = 6, 4

# Regions: key, name, columns [c0, c1), rows [r0, r1) on the 6 x 4 source grid (north row 0), biome colour, biome words.
FACES = {
    'cloudside': {
        'title': 'Cloudside, the bright face',
        'light': 'bright warm daylight, MM6/MM7 brightness, a high sun',
        'regions': [
            ('X6', 'Desert of the Sphinx', (0, 2), (0, 2), (214, 180, 96),
             'ochre sand dunes and red mesas, the Barbaric Mountains, Castle Basenji on a cliff, the Sphinx, '
             'the Warzone arena; dunes pour over the west rim with sand streaming off into space'),
            ('X4', 'Burlock Savannah', (2, 4), (0, 2), (176, 164, 92),
             'golden rolling savannah and jousting fields, the river\'s upper reach, red dwarf hills, the grey bare '
             'peaks of the Gargoyle Range in the north, Castle Burlock of white stone with a small walled village, '
             'the small town of Asp'),
            ('X7', 'Mount Firestone', (4, 6), (0, 2), (120, 72, 56),
             'volcanic badlands of dark rock, a smoking volcano, orange lava rivers and a lava lake, ash in the air; '
             'mild green-brown southern slopes; lava falls over the north rim into space'),
            ('X5', 'Winterkill Tundra', (0, 2), (2, 4), (226, 232, 238),
             'white snowfields, frozen blue lakes, a snowy pine forest, the ghost town Winterkill, a monastery, '
             'the Land of the Giants in the south-west, a glacier ending at the rim'),
            ('X3', 'Lifeforce Lagoon', (2, 3), (2, 4), (92, 112, 72),
             'dark green swamp and lagoon, marsh woods, the ruined Newcastle on a rise, the vampire town '
             'Nightshadow in a patch of grey mist'),
            ('X2', 'Rivercity and Lake Darzog', (3, 4), (2, 4), (96, 140, 88),
             'a broad blue river and a lake with a wooded island and a dark tower on it, Rivercity built across '
             'the river on a great bridge, farmland to the north, fairy woods to the south'),
            ('X1', 'Vertigo Meadows', (4, 6), (2, 4), (112, 168, 80),
             'bright green meadows, orchards and a river delta, the walled river town Vertigo with a bridge, '
             'a black witch tower in the south-east, dwarf mine hills in the north, a small pyramid on a knoll; '
             'the east edge is a white cliff dropping into the stars'),
        ],
        'landmarks': [
            ('Vertigo', 4.55, 2.75, 'town'), ('Witch Tower', 5.5, 3.6, 'tower'), ('pyramid', 5.0, 2.45, 'pyramid'),
            ('Rivercity', 3.5, 2.7, 'town'), ("Darzog's Tower", 3.35, 3.35, 'tower'),
            ('Nightshadow', 2.45, 3.4, 'town'), ('Newcastle', 2.6, 2.55, 'castle'),
            ('Castle Burlock', 3.0, 1.35, 'castle'), ('Asp', 2.4, 1.6, 'town'),
            ('Winterkill', 1.1, 2.9, 'town'), ('Castle Basenji', 0.6, 0.7, 'castle'), ('Sphinx', 1.4, 1.2, 'pyramid'),
            ('Volcano', 5.0, 0.8, 'peak'),
        ],
        'sky': [
            ('X8 Cloudreach', 3.3, 3.25, 1.7, 0.75, 'cloud islands with harpy nests and an observatory'),
            ('X9 Clouds of Xeen', 3.6, 1.95, 1.3, 0.6, "cloud islands holding Lord Xeen's castle and a carnival"),
        ],
    },
    'darkside': {
        'title': 'Darkside, the shadowed face',
        'light': 'amber daylight under a low amber-gold cloud band and a pale small sun, desaturated colours',
        'regions': [
            ('D6', 'The Forbidden Zone', (0, 2), (0, 2), (96, 64, 56),
             'volcanic waste with lava, grey Ancient ruins, two crashed metal escape pods (one in a lava lake), '
             'the walled city of the dead Necropolis, Castle Alamar, a fortress of metal and stone with glowing '
             'energy fields'),
            ('D5', 'Desert of Doom', (2, 4), (0, 2), (196, 164, 104),
             'pale dunes of the Desert of Doom, the Great Pyramid rising from the sand, a dark quivering forest on '
             'the highland edge, the Parabolic Barrier, a long shimmering Ancient energy wall in the north, snowy '
             'highlands at the north edge'),
            ('D4', 'Lakeside and Blackfang', (4, 6), (0, 2), (84, 108, 120),
             'a great dark lake with an island, snowy river rapids in the north, a gloomy forest, the small town '
             'Lakeside on the shore, Castle Blackfang on a crag wrapped in a storm of bats'),
            ('D1', 'Castleview Vale', (0, 2), (2, 4), (104, 128, 84),
             'a river vale of desaturated green grassland, a walled stone-and-slate town Castleview, a dark grove '
             'whose tallest tree carries a rope up into the sky, a pale translucent ghost of a castle to the '
             'south-west, a small pyramid outside the north gate'),
            ('D2', 'Sprite Forest and Ogre Pass', (2, 4), (2, 4), (72, 100, 70),
             'an enchanted dark forest with glowing blue-green mushrooms and one giant ancient tree, rocky '
             'gemstone foothills, a mountain pass with two crude ogre forts'),
            ('D3', 'Sandcaster and the Aging Forest', (4, 6), (2, 4), (170, 140, 92),
             'a sandstone city Sandcaster with domes and towers at the desert edge, a crossroads market where six '
             'roads meet, an autumn forest, a winding river; above the east rim the bright glow of the other face'),
        ],
        'landmarks': [
            ('Castleview', 1.0, 2.8, 'town'), ('Castle Kalindra', 0.5, 3.5, 'ghost'), ('pyramid', 1.0, 2.35, 'pyramid'),
            ('Dark Grove', 1.6, 3.3, 'tree'), ('Temple of Bark', 2.7, 3.2, 'tree'),
            ('Sandcaster', 4.6, 3.0, 'town'), ('Crossroads', 5.3, 2.5, 'town'),
            ('Lakeside', 4.6, 1.4, 'town'), ('Castle Blackfang', 5.3, 0.9, 'castle'),
            ('Great Pyramid', 3.0, 1.0, 'pyramid'), ('Necropolis', 1.3, 1.5, 'town'), ('Castle Alamar', 0.6, 0.6, 'castle'),
        ],
        # D-23 (2026-11-20): rules every Darkside map follows, shown under the schematic
        'rules': ["Rivers: each map's river rises and falls inside it (D-23); none crosses a map edge."],
        'sky': [
            ('D7 The Skyroads', 3.0, 1.75, 3.2, 0.7, 'cloud roads linking floating stops and the marble city Olympus'),
        ],
    },
}

GUIDE_PROMPT = """Asset: a painted world map for a new Might and Magic VI-VIII style game world, the art of a fantasy RPG's map screen.
The world is flat: an artificial square continent floating in space, so the land ends on every side in a sheer cliff
edge (the "world rim") that drops into a black starfield. Paint {title}: a top-down map, seen almost straight from above
(a slight tilt so the rim cliffs and the mountains read as relief), hand-painted, warm and slightly stylised, like the
painted maps of Might and Magic VI-VIII, {light}.

Reference 1 is the layout guide: keep its arrangement exactly. The land fills exactly the coloured rectangle; each
coloured block is one region, at the same position and size, in roughly the given colour; the small white symbols are
landmarks at those positions (circles: towns, squares: castles, triangles: pyramids or peaks, bars: towers, a tree, a
ghost outline: a castle out of phase). Blend the regions into one natural landscape with soft biome transitions; roads
link the towns. The translucent white shapes with a dashed outline are the sky layer: islands of cloud floating high
above the land, casting soft shadows; paint them as luminous floating cloud islands. Everything outside the rectangle
is the starfield beyond the rim, with the cliff faces visible along the land's edges.

Reference 2 is the original 1990s game's map of this face (blocky, low resolution), for the geography only: rivers,
lakes, deserts, snow and lava where it puts them. Do not copy its pixels, grid or colours.

The regions, west to east, north row first:
{regions}

No text, no labels, no letters, no compass, no frame, no legend. Even soft lighting, rich painted detail.
"""

WORKER = """You are an image-generation worker. Do exactly this and nothing else:
1. Call the built-in image_gen tool ONCE using the attached image(s) as reference images and the IMAGE PROMPT below.
   Output size: 1536x1024 (landscape).
2. Copy the generated PNG file unchanged to {target}.
3. Reply with only the absolute path of the copied file.
Do not read other files, do not inspect, edit, resize or retry the result.

IMAGE PROMPT:
{prompt}
"""


def cell(c, r):
    return FX0 + (FX1 - FX0) * c / COLS, FY0 + (FY1 - FY0) * r / ROWS


def guide(face):
    data = FACES[face]
    image = Image.new('RGB', (W, H), (10, 10, 24))
    draw = ImageDraw.Draw(image, 'RGBA')
    for x, y in [((i * 7919) % W, (i * 104729) % H) for i in range(400)]:
        draw.point((x, y), fill=(200, 200, 230))
    for key, name, (c0, c1), (r0, r1), colour, words in data['regions']:
        x0, y0 = cell(c0, r0)
        x1, y1 = cell(c1, r1)
        draw.rectangle((x0, y0, x1, y1), fill=colour)
    for name, c, r, kind in data['landmarks']:
        x, y = cell(c, r)
        s = 9
        if kind == 'town':
            draw.ellipse((x - s, y - s, x + s, y + s), outline='white', width=3)
        elif kind in ('castle',):
            draw.rectangle((x - s, y - s, x + s, y + s), outline='white', width=3)
        elif kind in ('pyramid', 'peak'):
            draw.polygon((x, y - s - 3, x + s + 2, y + s, x - s - 2, y + s), outline='white', width=3)
        elif kind == 'tower':
            draw.rectangle((x - 4, y - s - 6, x + 4, y + s), fill='white')
        elif kind == 'tree':
            draw.ellipse((x - s, y - s - 6, x + s, y + 4), fill='white')
            draw.rectangle((x - 2, y, x + 2, y + s), fill='white')
        elif kind == 'ghost':
            draw.rectangle((x - s - 3, y - s, x + s + 3, y + s), outline=(255, 255, 255, 140), width=2)
    for name, c, r, w, h, words in data['sky']:
        x, y = cell(c, r)
        dx, dy = (FX1 - FX0) * w / COLS / 2, (FY1 - FY0) * h / ROWS / 2
        draw.ellipse((x - dx, y - dy, x + dx, y + dy), fill=(255, 255, 255, 110))
        for t in range(0, 360, 12):
            import math
            a0, a1 = math.radians(t), math.radians(t + 6)
            draw.line((x + dx * math.cos(a0), y + dy * math.sin(a0), x + dx * math.cos(a1), y + dy * math.sin(a1)),
                      fill='white', width=2)
    out = HERE / f'guide_{face}.png'
    image.save(out)
    return out


def prompt_for(face):
    data = FACES[face]
    lines = []
    for key, name, cols, rows, colour, words in data['regions']:
        lines.append(f'- {name}: {words}.')
    for name, c, r, w, h, words in data['sky']:
        lines.append(f'- Sky layer, {name.split(" ", 1)[1]}: {words}.')
    return GUIDE_PROMPT.format(title=data['title'], light=data['light'], regions='\n'.join(lines))


def cmd_paint(args):
    face = args.face
    raw = HERE / 'raw'
    raw.mkdir(exist_ok=True)
    version = 1 + len(list(raw.glob(f'{face}_v*.png')))
    target = raw / f'{face}_v{version}.png'
    prompt = prompt_for(face)
    if args.note:
        prompt += '\nCorrection for this attempt: ' + args.note
    (raw / f'{face}_v{version}.txt').write_text(prompt + '\n')
    refs = [guide(face), HERE / f'{"xeen" if face == "cloudside" else "dark"}_native_mosaic.png']
    command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(HERE), '--skip-git-repo-check']
    for ref in refs:
        command += ['-i', str(ref)]
    started = time.time()
    with open(target.with_suffix('.log'), 'w') as stream:
        result = subprocess.run(command, input=WORKER.format(prompt=prompt, target=target), text=True,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=900)
    print(face, version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
          round(time.time() - started), 's')


def font(size):
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf'):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def land_box(image):
    """The painted face's bounding box: rows and columns that are mostly brighter than the starfield."""
    import numpy as np
    grey = np.asarray(image.convert('L'), float)
    rows = np.where((grey > 45).mean(axis=1) > 0.5)[0]
    cols = np.where((grey > 45).mean(axis=0) > 0.5)[0]
    return cols[0], rows[0], cols[-1], rows[-1]


def labelled_painting(face, version):
    """The painting with its region grid fitted to the painted land; landmarks are listed beside it, since the
    painter places them freely inside their region."""
    data = FACES[face]
    image = Image.open(HERE / 'raw' / f'{face}_v{version}.png').convert('RGB').resize((W, H), Image.LANCZOS)
    x0b, y0b, x1b, y1b = land_box(image)
    draw = ImageDraw.Draw(image, 'RGBA')
    big, small = font(30), font(17)
    for key, name, (c0, c1), (r0, r1), colour, words in data['regions']:
        x0 = x0b + (x1b - x0b) * c0 / COLS
        x1 = x0b + (x1b - x0b) * c1 / COLS
        y0 = y0b + (y1b - y0b) * r0 / ROWS
        y1 = y0b + (y1b - y0b) * r1 / ROWS
        draw.rectangle((x0, y0, x1, y1), outline=(255, 255, 255, 70), width=2)
        draw.text((x0 + 10, y0 + 8), key, font=big, fill='white', stroke_width=3, stroke_fill='black')
    return image


def schematic(face, width):
    data = FACES[face]
    height = int(width * 0.62)
    image = Image.new('RGB', (width, height), (24, 24, 32))
    draw = ImageDraw.Draw(image)
    m = 20
    gw, gh = (width - 2 * m) / COLS, (height - 2 * m) / ROWS
    big, small = font(26), font(15)
    for key, name, (c0, c1), (r0, r1), colour, words in data['regions']:
        box = (m + c0 * gw, m + r0 * gh, m + c1 * gw, m + r1 * gh)
        draw.rectangle(box, fill=tuple(int(v * 0.75) for v in colour), outline='white', width=2)
        draw.text((box[0] + 8, box[1] + 6), key, font=big, fill='white', stroke_width=2, stroke_fill='black')
        words_ = name.split(' ')
        lines, line = [], ''
        for word in words_:
            if len(line) + len(word) > max(8, int((box[2] - box[0]) / 9)):
                lines.append(line)
                line = word
            else:
                line = (line + ' ' + word).strip()
        lines.append(line)
        for i, text in enumerate(lines):
            draw.text((box[0] + 8, box[1] + 38 + 18 * i), text, font=small, fill='white', stroke_width=2,
                      stroke_fill='black')
    draw.rectangle((m, m, width - m, height - m), outline=(255, 200, 120), width=4)
    return image


def schematic_svg(face):
    """The same schematic as an SVG for the review page."""
    data = FACES[face]
    gw, gh, m = 130, 110, 20
    width, height = 2 * m + COLS * gw, 2 * m + ROWS * gh + 30
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" font-family="sans-serif">',
             f'<rect width="{width}" height="{height}" fill="#181820"/>']
    for key, name, (c0, c1), (r0, r1), colour, words in data['regions']:
        x, y, w, h = m + c0 * gw, m + r0 * gh, (c1 - c0) * gw, (r1 - r0) * gh
        fill = '#%02x%02x%02x' % tuple(int(v * 0.75) for v in colour)
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#fff" stroke-width="2"/>')
        parts.append(f'<text x="{x + 8}" y="{y + 26}" fill="#fff" font-size="22" font-weight="bold">{key}</text>')
        parts.append(f'<text x="{x + 8}" y="{y + 46}" fill="#fff" font-size="12">{name}</text>')
    for name, c, r, w, h, words in data['sky']:
        cx, cy = m + c * gw, m + r * gh
        parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{w * gw / 2}" ry="{h * gh / 2}" fill="#ffffff33" '
                     f'stroke="#fff" stroke-dasharray="6 4"/>')
        parts.append(f'<text x="{cx}" y="{cy + 4}" fill="#dff" font-size="12" text-anchor="middle">{name}</text>')
    parts.append(f'<rect x="{m}" y="{m}" width="{COLS * gw}" height="{ROWS * gh}" fill="none" stroke="#ffc878" '
                 f'stroke-width="4"/>')
    parts.append(f'<text x="{m}" y="{height - 10}" fill="#ffc878" font-size="12">{data["title"]}; orange: the world '
                 f'rim on every outer edge; dashed: the sky layer</text></svg>')
    out = HERE / f'schematic_{face}.svg'
    out.write_text('\n'.join(parts) + '\n')
    return out


def cmd_board(args):
    for face in FACES:
        schematic_svg(face)
    picks = dict(p.split('=') for p in args.pick)
    title = font(40)
    panels = []
    for face in ('cloudside', 'darkside'):
        version = int(picks.get(face, 1))
        painting = labelled_painting(face, version)
        side = schematic(face, 760)
        notes = ['WORLD_DESIGN §3.1 schematic (north up, A-F west to east).',
                 'Orange: the world rim, a cliff above the stars, on every outer edge.',
                 'Landmarks per region (the painter places them inside it):', '']
        for key, name, cols, rows, colour, words in FACES[face]['regions']:
            notes.append(f'{key} {name}:')
            text = words[0].upper() + words[1:]
            line = '   '
            for word in text.split(' '):
                if len(line) + len(word) > 78:
                    notes.append(line)
                    line = '   '
                line += word + ' '
            notes.append(line)
        for name, c, r, w, h, words in FACES[face]['sky']:
            notes.append(f'Sky layer {name}:')
            notes.append(f'   {words[0].upper() + words[1:]}')
        for rule in FACES[face].get('rules', []):
            notes.append(rule)
        height = max(H + 70, 70 + side.height + 40 + 21 * len(notes))
        panel = Image.new('RGB', (W + 40 + side.width, height), (16, 16, 22))
        d = ImageDraw.Draw(panel)
        d.text((10, 10), FACES[face]['title'], font=title, fill='white')
        panel.paste(painting, (0, 70))
        panel.paste(side, (W + 40, 70))
        y = 70 + side.height + 20
        for line in notes:
            d.text((W + 40, y), line, font=font(16), fill=(220, 220, 230))
            y += 21
        panels.append(panel)
    board = Image.new('RGB', (panels[0].width, sum(p.height for p in panels) + 40), (16, 16, 22))
    y = 0
    for panel in panels:
        board.paste(panel, (0, y))
        y += panel.height + 40
    board.save(HERE / 'board_mu1.png')
    board.resize((board.width // 2, board.height // 2), Image.LANCZOS).save(HERE / 'board_mu1_small.png')
    print('board', board.size)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('guides')
    paint = sub.add_parser('paint')
    paint.add_argument('face', choices=list(FACES))
    paint.add_argument('--note', default='')
    board = sub.add_parser('board')
    board.add_argument('--pick', nargs='*', default=[])
    args = parser.parse_args()
    if args.command == 'guides':
        for face in FACES:
            print(guide(face))
    elif args.command == 'paint':
        cmd_paint(args)
    else:
        cmd_board(args)


if __name__ == '__main__':
    main()
