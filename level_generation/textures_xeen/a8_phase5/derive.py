"""A8 phase 5: textures derived from finished masters (run after `xtex.py finish`).
xaglyph   = the left half of xaglyphfull (the gate's left leaf; the right leaf shows it mirrored), 128 x 256.
xalavahdx = xalavahd with its lava gone dark (the Head after shutdown): warm bright pixels cooled to dull grey metal."""
from pathlib import Path
from PIL import Image
import numpy as np
F = Path(__file__).parent / 'finished'

def save(name, img):
    w, h = img.size
    img.save(F / f'{name}.png')
    img.resize((w // 2, h // 2), Image.LANCZOS).save(F / f'{name}_x2.png')
    img.resize((w // 4, h // 4), Image.LANCZOS).save(F / f'{name}_x1.png')

full = Image.open(F / 'xaglyphfull.png').convert('RGB')
w, h = full.size
save('xaglyph', full.crop((0, 0, w // 2, h)).resize((512, 1024), Image.LANCZOS))

lit = np.asarray(Image.open(F / 'xalavahd.png').convert('RGB')).astype(np.float32)
r, g, b = lit[..., 0], lit[..., 1], lit[..., 2]
luma = 0.299 * r + 0.587 * g + 0.114 * b
glow = np.clip(((r - b) - 60.0) / 80.0, 0, 1) * np.clip((r - 120.0) / 60.0, 0, 1)   # orange/yellow lava
dark = np.stack([luma * 0.18 + 14, luma * 0.17 + 13, luma * 0.17 + 14], -1)          # cold dark slag
out = lit * (1 - glow[..., None]) + dark * glow[..., None]
save('xalavahdx', Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)))
print('derived xaglyph', Image.open(F / 'xaglyph.png').size, 'xalavahdx', Image.open(F / 'xalavahdx.png').size)

# xvkban: `finish` cropped the 2:3 return to 1:2 (losing the side borders) and matched it to a cream tapestry's
# brightness (gain 4.5, the black field turned grey). Redone by hand: the whole return resized to 512 x 1024, gain 0.85.
# raw = Image.open('raw/xvkban_v1.png'); img = raw.resize((512, 1024)) * 0.85 -> finished/xvkban(.png, _x2, _x1)
