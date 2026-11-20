"""Row/grid contact sheet. Args: out.png cols size img1 img2 ..."""
import sys
from PIL import Image
out, cols, sz = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); fs = sys.argv[4:]
rows = (len(fs) + cols - 1) // cols
s = Image.new('RGB', (cols * sz, rows * sz), (40, 40, 40))
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGB'); im.thumbnail((sz, sz)); s.paste(im, ((i % cols) * sz, (i // cols) * sz))
s.save(out)
