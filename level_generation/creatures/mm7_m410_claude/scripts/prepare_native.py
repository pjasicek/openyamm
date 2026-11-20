"""Decode the original MM7 indexed sprites with their real tier palettes into references_native/ sheets.

Usage: python3 scripts/prepare_native.py <native project name> <frame prefix> <tier palette ids A,B,C>
"""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib, json, sys
import numpy as np

P = Path(__file__).resolve().parents[1]
R = P.parents[2]
native_name, prefix, tiers = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
s = json.loads((P.parent / native_name / 'sources.json').read_text())
N = P / 'references_native'
N.mkdir(exist_ok=True)
palettes = {}
for pal in tiers:
    info = s['palette_sources'][pal]
    raw = (R / info['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == info['sha256'], pal
    palettes[pal] = np.frombuffer(raw[:768], np.uint8).reshape(256, 3)


def decode(info, pal):
    f = R / info['path']
    assert hashlib.sha256(f.read_bytes()).hexdigest() == info['sha256'], f
    idx = np.array(Image.open(f))
    rgb = palettes[pal][idx]
    alpha = np.where(idx == info.get('transparency_index', 0), 0, 255).astype(np.uint8)
    return Image.fromarray(np.concatenate([rgb, alpha[..., None]], axis=2))


for stem, info in s['sources'].items():
    decode(info, tiers[0]).save(N / f'{stem}.png')
(N / 'inventory.json').write_text(json.dumps(s, indent=2) + '\n')


def sheet(names, file, columns=5, scale=2, background=(65, 67, 70)):
    names = [n for n in names if (N / f'{n}.png').exists()]
    tile = 256 * scale
    rows = (len(names) + columns - 1) // columns
    out = Image.new('RGB', (columns * tile, rows * (tile + 26)), background)
    draw = ImageDraw.Draw(out)
    for i, stem in enumerate(names):
        im = Image.open(N / f'{stem}.png').resize((tile, tile), Image.Resampling.NEAREST)
        x = i % columns * tile
        y = i // columns * (tile + 26)
        out.paste(im, (x, y), im)
        draw.text((x + 6, y + tile + 5), stem, fill='white')
    out.save(N / file)


sheet([f'{prefix}sa{i}' for i in range(5)], 'standing.png')
sheet([f'{prefix}a{f}{v}' for v in [0, 2] for f in 'abcdefgh'], 'attack.png', 8, 2)
sheet([f'{prefix}{a}{f}0' for a, frames in [('w', 'abcdefgh'), ('f', 'abcde'), ('n', 'abcde'), ('d', 'abcd'), ('x', 'a')]
       for f in frames], 'motion.png', 8, 1)
preview = Image.new('RGB', (len(tiers) * 512, 560), (65, 67, 70))
draw = ImageDraw.Draw(preview)
for i, pal in enumerate(tiers):
    img = decode(s['sources'][f'{prefix}sa0'], pal)
    img.save(N / f'standing_{pal}.png')
    img = img.resize((512, 512), Image.Resampling.NEAREST)
    preview.paste(img, (i * 512, 0), img)
    draw.text((i * 512 + 10, 530), f'Tier {"ABC"[i]}: native palette {pal}', fill='white')
preview.save(N / 'tiers.png')
# native upright height of the standing front frame (pixels at SFT scale 1)
a = np.array(Image.open(N / f'{prefix}sa0.png'))[..., 3]
rows = np.where(a.max(axis=1) > 0)[0]
print('NATIVE', len(s['sources']), 'verified bitmaps,', len(palettes), 'palettes; standing front height px',
      rows.max() - rows.min() + 1)
