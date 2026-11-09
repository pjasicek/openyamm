#!/usr/bin/env python3
"""Export generated illustrations and code-authored control geometry; retain the supplied alpha."""
from pathlib import Path
import hashlib
import json
import subprocess

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUNTIME = REPO / 'assets_dev/engine/icons_x2'
ART = HERE / 'art'
SIZE = 256
receipts = []


def record(path, source):
    path.chmod(0o644)
    with Image.open(path) as image:
        assert image.mode == 'RGBA', path
        alpha = image.getchannel('A')
        assert alpha.getextrema()[0] == 0, path
        receipts.append({'path': str(path.relative_to(REPO)), 'source': source,
                         'size': list(image.size), 'alpha_bbox': alpha.getbbox(),
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})


for master in sorted((ART / 'raw').glob('*.png')):
    with Image.open(master) as image:
        assert image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] == 0, master
        bbox = image.getchannel('A').getbbox()
        assert bbox, master
        icon = image.crop(bbox)
        icon.thumbnail((224, 224), Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA', (SIZE, SIZE))
        canvas.alpha_composite(icon, ((SIZE-icon.width)//2, (SIZE-icon.height)//2))
        target = RUNTIME / f'obsidian_action_{master.stem}.png'
        canvas.save(target)
        record(target, str(master.relative_to(REPO)))


def vector(name, commands):
    # MVG is the editable source. Rasterize at 4x for clean subpixel edges and true alpha.
    source = ART / f'{name}.mvg'
    source.write_text('viewbox 0 0 256 256\n' + commands + '\n')
    target = RUNTIME / f'obsidian_{name}.png'
    subprocess.run(['magick', '-size', '1024x1024', 'xc:none', '-draw',
                    'scale 4,4 ' + commands, '-filter', 'Lanczos', '-resize', '256x256',
                    'PNG32:' + str(target)], check=True)
    record(target, str(source.relative_to(REPO)))


for state, edge, face in [('normal', '#9c8961', '#15231e'),
                          ('hover', '#e5d2a1', '#23352c'),
                          ('pressed', '#ae9663', '#09110e'),
                          ('active', '#efd39a', '#2b3526')]:
    vector('touch_' + state, f'''
fill '#080e0c' stroke '#4d4738' stroke-width 2 circle 128,128 128,8
fill '{face}' stroke '{edge}' stroke-width 3 circle 128,128 128,13
fill none stroke '#514d39' stroke-width 1 circle 128,128 128,20
stroke '#ffffff18' stroke-width 1 path 'M 40,71 C 75,13 164,8 209,61'
stroke '#00000070' stroke-width 2 path 'M 47,197 C 103,247 182,242 218,181'
''')

# Small abstract controls stay code-authored; illustrations above are generated separately.
shapes = {
    'pause': "roundrectangle 75,54 110,202 5,5 roundrectangle 146,54 181,202 5,5",
    'resume': "path 'M 83,49 L 204,128 L 83,207 Z'",
    'up': "path 'M 47,156 L 128,75 L 209,156 L 185,180 L 128,123 L 71,180 Z'",
    'down': "path 'M 47,100 L 128,181 L 209,100 L 185,76 L 128,133 L 71,76 Z'",
    'quickcast': "path 'M 139,27 L 63,141 L 115,141 L 94,232 L 201,103 L 148,103 L 169,27 Z'",
}
for name, shape in shapes.items():
    vector('action_' + name, "fill '#e4d6ac' stroke '#9e8457' stroke-width 3 " + shape)

vector('joystick_base', """
fill '#0b17117a' stroke '#a18f6777' stroke-width 3 circle 128,128 128,8
fill none stroke '#ddd0a33d' stroke-width 1 circle 128,128 128,23
stroke '#cabc8e55' stroke-width 3 path 'M 128,23 L 128,35 M 128,221 L 128,233 M 23,128 L 35,128 M 221,128 L 233,128'
""")
vector('joystick_knob', """
fill '#17251edf' stroke '#c4ae78bb' stroke-width 4 circle 128,128 128,12
fill '#354538cf' stroke '#657357b0' stroke-width 2 circle 128,128 128,30
""")
(HERE / 'export.json').write_text(json.dumps({'exports': receipts}, indent=2) + '\n')
print(f'Exported {len(receipts)} alpha assets to {RUNTIME}')
