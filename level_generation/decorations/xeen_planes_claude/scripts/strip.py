"""Side-by-side strip of images. Usage: strip.py <out> <img> [<img> ...]"""
import sys
from PIL import Image
ims = [Image.open(p).convert('RGB') for p in sys.argv[2:]]
h = max(i.size[1] for i in ims)
s = Image.new('RGB', (sum(i.size[0] for i in ims), h))
x = 0
for i in ims:
    s.paste(i, (x, 0)); x += i.size[0]
s.save(sys.argv[1])
