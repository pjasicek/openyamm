"""Side-by-side sheet of <prefix>_<view>.png. Usage: sheet4.py <prefix> <out> view [view ...]"""
import sys
from PIL import Image
pre, out, views = sys.argv[1], sys.argv[2], sys.argv[3:]
ims = [Image.open(f'{pre}_{v}.png').convert('RGB') for v in views]
s = Image.new('RGB', (sum(i.size[0] for i in ims), max(i.size[1] for i in ims)))
x = 0
for i in ims:
    s.paste(i, (x, 0)); x += i.size[0]
s.save(out)
