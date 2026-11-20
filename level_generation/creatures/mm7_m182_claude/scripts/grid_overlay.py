"""Draw a labelled 5 cm grid over grid_render.py output (camera right = up x back:
side +Y, top +X, front +X, back -X)."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
out = Path(sys.argv[1]); m = json.loads((out / 'render_mapping.json').read_text()); PX = m['pixels_per_metre']; c = m['center']
# (image-right axis, sign, image-up axis, sign) per view, from the camera basis in grid_render.py
basis = {'side': (1, 1, 2, 1), 'top': (0, 1, 1, 1), 'front': (0, 1, 2, 1), 'back': (0, -1, 2, 1)}
for name, (ra, rs, ua, us) in basis.items():
    im = Image.open(out / f'render_{name}.png').convert('RGBA'); w, h = im.size
    bg = Image.new('RGBA', im.size, (25, 25, 30, 255)); d = ImageDraw.Draw(bg)
    for k in range(-40, 41):
        v = k * .05
        x = w / 2 + rs * (v - c[ra]) * PX; y = h / 2 - us * (v - c[ua]) * PX
        col = (150, 60, 60, 255) if k == 0 else ((90, 90, 120, 255) if k % 2 == 0 else (55, 55, 70, 255))
        if 0 <= x < w: d.line([(x, 0), (x, h)], fill=col); d.text((x + 2, 2), f'{"xyz"[ra]}{v:+.2f}', fill=(220, 220, 120, 255))
        if 0 <= y < h: d.line([(0, y), (w, y)], fill=col); d.text((2, y + 2), f'{"xyz"[ua]}{v:+.2f}', fill=(220, 220, 120, 255))
    bg.alpha_composite(im); bg.convert('RGB').save(out / f'grid_{name}.png')
