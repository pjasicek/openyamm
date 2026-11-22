"""Grid sheet: sheet.py <out> <cols> <img> [img ...] (each image scaled to the first one's size)."""
import sys
from PIL import Image
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f).convert('RGB') for f in files]
w, h = ims[0].size
s = Image.new('RGB', (w * min(cols, len(ims)), h * ((len(ims) + cols - 1) // cols)))
for i, im in enumerate(ims):
    s.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
s.save(out)
