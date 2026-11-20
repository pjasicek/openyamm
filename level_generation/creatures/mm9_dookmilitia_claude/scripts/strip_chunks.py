"""Cut a strips sheet (strips.py: two 300 px rows per clip) into readable pieces of K clips. Args: <sheet png> <out prefix> [K]"""
import sys
from PIL import Image
im = Image.open(sys.argv[1]); K = int(sys.argv[3]) if len(sys.argv) > 3 else 3
H = 600 * K; n = (im.height + H - 1) // H
for i in range(n):
    im.crop((0, i * H, im.width, min(im.height, (i + 1) * H))).save(f'{sys.argv[2]}_{i}.png')
print('CHUNKS', n)
