"""Overlay: base clay image + outline of one or more other renders (alpha edges) in colours. overlay.py out base a[:color] ..."""
import sys
import numpy as np
from PIL import Image, ImageFilter
out, base = sys.argv[1], Image.open(sys.argv[2]).convert('RGBA')
bg = Image.new('RGBA', base.size, (70, 70, 70, 255)); bg.alpha_composite(base)
img = np.array(bg.convert('RGB'))
cols = {'red': (255, 40, 40), 'cyan': (40, 230, 255), 'yellow': (255, 230, 0)}
for arg in sys.argv[3:]:
    path, col = (arg.split(':') + ['red'])[:2]
    a = np.array(Image.open(path).convert('RGBA'))[:, :, 3] > 128
    er = np.array(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3))) > 128
    edge = a & ~er
    img[edge] = cols[col]
Image.fromarray(img).save(out)
