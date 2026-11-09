"""Contact sheets of every native frame (x2 restored) of this batch's sprites, for review."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[5]
X2 = ROOT / 'assets_legacy/decorations_x2_20261016'
OUT = Path(__file__).resolve().parents[1] / 'review/sprites'

def sheet(name, files, scale=2, bg=(90, 110, 90)):
    ims = [Image.open(X2 / f).convert('RGBA') for f in files]
    w = max(i.width for i in ims) * scale
    h = max(i.height for i in ims) * scale
    s = Image.new('RGB', (w * len(ims), h + 14), bg)
    d = ImageDraw.Draw(s)
    for k, (f, im) in enumerate(zip(files, ims)):
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        s.paste(im, (k * w, h - im.height), im)
        d.text((k * w + 2, h), f.split('_')[0], fill=(255, 255, 255))
    s.save(OUT / f'{name}.png')

groups = {}
for f in sorted(p.name for p in X2.iterdir()):
    for g in ['dec6', 'dec7', '7dec33', 'torch02', '7dec24']:
        if f.startswith(g):
            base = f.split('_')[0]
            key = base[:-1] if base[-1] in 'abcdefghx' and base not in ('torch02',) else base
            groups.setdefault(key, []).append(f)
for k, fs in groups.items():
    sheet(k, fs, scale=2 if k not in ('7dec33',) else 1)
    print(k, len(fs))
