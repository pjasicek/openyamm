"""Prepares the Xeen item icon pass from manifest.yml: per target items/<file>/style_reference.png (the family's four
MM6-MM8 x2 icons on grey) and briefs/<file>.md. An existing brief is never overwritten (it may carry corrections);
a target whose folder has paint_a.png is skipped.
Usage: python3 -I prep.py [<key> ...]"""
import os
import sys

import yaml
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ICONS = os.path.join(REPO, 'assets_dev/engine/icons_x2')


def style_sheet(names, path):
    images = [Image.open(os.path.join(ICONS, n.lower() + '.png')).convert('RGBA') for n in names]
    scale = min(2.0, 600 / max(i.height for i in images))
    images = [i.resize((round(i.width * scale), round(i.height * scale)), Image.LANCZOS) for i in images]
    w = sum(i.width for i in images) + 40 * (len(images) + 1)
    h = max(i.height for i in images) + 80
    sheet = Image.new('RGBA', (w, h), (96, 96, 96, 255))
    x = 40
    for i in images:
        sheet.alpha_composite(i, (x, 40 + (h - 80 - i.height) // 2))
        x += i.width + 40
    sheet.convert('RGB').save(path)


def canvas(box):
    return '1024x1536' if box[1] > box[0] * 1.6 else '1536x1024' if box[0] > box[1] * 1.6 else '1024x1024'


def main():
    manifest = yaml.safe_load(open(os.path.join(HERE, 'manifest.yml')))
    wanted = set(sys.argv[1:])
    for target in manifest['targets']:
        if wanted and target['key'] not in wanted:
            continue
        family = manifest['families'][target['family']]
        folder = os.path.join(HERE, 'items', target['file'])
        os.makedirs(folder, exist_ok=True)
        if os.path.exists(os.path.join(folder, 'paint_a.png')):
            continue
        style_sheet(family['style_refs'], os.path.join(folder, 'style_reference.png'))
        brief = os.path.join(HERE, 'briefs', f"{target['file']}.md")
        if os.path.exists(brief):
            continue
        lines = [f"# {target['name']} ({target['kind']}, {target['family']}). Folder: items/{target['file']}. "
                 f"Size {canvas(target['box_x2'])}.",
                 f"OBJECT: {target['draw']}.",
                 f"VIEW: {family['view']}",
                 'Setting: the fantasy world of Xeen (Might and Magic IV-V); the object is a real, handmade thing in '
                 'that world.']
        with open(brief, 'w') as stream:
            stream.write('\n'.join(lines) + '\n')
    print('prepared', len(manifest['targets']), 'targets')


main()
