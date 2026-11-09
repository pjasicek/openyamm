"""Create review-only contacts; original three imagegen inputs remain untouched."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw

REPO = Path.cwd()
SESSION = REPO / 'level_generation/creatures/mm7_mm8_packed_outline/session_mm7_03'

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('job')
parser.add_argument('--families', nargs='+')
args = parser.parse_args()
for root in sorted(SESSION.glob('mm7_*')):
    if args.families and root.name not in args.families:
        continue
    job = next((j for j in json.loads((root / 'redo_2x/run.json').read_text())['jobs']
                if j['id'] == args.job), None)
    if job is None:
        continue
    images = [Image.open(root / f'redo_2x/references/{args.job}_{kind}.png').convert('RGBA')
              for kind in ('native', 'outline', 'detail')]
    # Full images at original size, except a 1600-pixel limit for a large full-cycle appearance contact.
    for image in images:
        image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    width = sum(im.width for im in images) + 40
    height = max(im.height for im in images) + 40
    contact = Image.new('RGB', (width, height), (45, 45, 45))
    draw = ImageDraw.Draw(contact)
    draw.text((4, 4), root.name + ' ' + args.job + ' / original colour | outline only | appearance', fill='white')
    x = 0
    for im in images:
        contact.paste(im, (x, 30), im)
        x += im.width + 16
    path = root / f'redo_2x/review/{args.job}_inputs.png'
    contact.save(path)
    print(path)
