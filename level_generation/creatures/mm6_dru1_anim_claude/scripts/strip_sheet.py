"""Compose (frames at the glTF importer's 24 fps) work/strip_<view>_<frame>.png into review/<label>_strip.png. Args: <label> <frame> [...]"""
import sys
from PIL import Image, ImageDraw
label, frames = sys.argv[1], [int(f) for f in sys.argv[2:]]
views = ['front', 'q34', 'side']
s = Image.new('RGB', (300 * len(frames), 420 * len(views))); d = ImageDraw.Draw(s)
for j, v in enumerate(views):
    for i, f in enumerate(frames):
        s.paste(Image.open(f'work/strip_{v}_{f}.png').convert('RGB'), (i * 300, j * 420))
        d.text((i * 300 + 4, j * 420 + 4), f'{v} f{f} {f / 24:.2f}s', fill=(255, 255, 255))
s.save(f'review/{label}_strip.png')
