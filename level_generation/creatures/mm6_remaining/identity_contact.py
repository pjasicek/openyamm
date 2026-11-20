"""Review all identity-batch views even when the native standing action is front-only."""
import argparse
import json
from pathlib import Path
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'mm6_peasants'))
from prepare_family import load
from process_family import recolor

parser = argparse.ArgumentParser()
parser.add_argument('family')
root, config, inv = load(parser.parse_args().family)
reg = json.loads((root / 'registration.json').read_text())
vectors = {int(p): v for p, v in json.loads((root / 'recolor_vectors.json').read_text()).items()}
names = json.loads((root / 'batches.json').read_text())['standing']['frames']
cw, ch = inv['logical_canvas']
cw += 12
ch += 30
out = Image.new('RGB', (len(names) * cw, len(inv['variants']) * ch), (43, 45, 43))
draw = ImageDraw.Draw(out)
for row, palette in enumerate(inv['variants']):
    for col, name in enumerate(names):
        im = recolor(Image.open(root / f'aligned_2x/{name}.png'),
                     Image.open(root / f'masks_2x/{name}.png'), int(palette), config, vectors)
        im = im.convert('RGBa').resize((round(im.width / 2), round(im.height / 2)),
                                      Image.Resampling.LANCZOS).convert('RGBA')
        ox, oy = reg[name]['canvas_origin_px']
        out.paste(im, (col * cw + 6 + round(ox / 2), row * ch + 26 + round(oy / 2)), im)
        draw.text((col * cw + 4, row * ch + 5), f'{palette}: {name}', fill='white')
out.save(root / 'review/identity_variants.png')
