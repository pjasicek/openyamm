"""Join pose_strip.py tiles into one row and delete them. Args: <out png> [scale]"""
import sys, glob, os
from PIL import Image
out = sys.argv[1]; k = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
fs = sorted(glob.glob(out + '.[0-9][0-9].png')); ims = [Image.open(f).convert('RGB') for f in fs]
W = Image.new('RGB', (sum(i.width for i in ims), ims[0].height)); x = 0
for i in ims: W.paste(i, (x, 0)); x += i.width
if k != 1: W = W.resize((int(W.width * k), int(W.height * k)))
W.save(out)
for f in fs: os.remove(f)
print('JOINED', out, len(fs))
