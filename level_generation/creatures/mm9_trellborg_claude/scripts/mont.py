"""Montage: mont.py out.png cols cell f1 f2 ..."""
import sys
from PIL import Image
o, c, s = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); fs = sys.argv[4:]
r = (len(fs) + c - 1) // c
W = Image.new('RGB', (c * s, r * s), (30, 30, 30))
for i, f in enumerate(fs):
    W.paste(Image.open(f).convert('RGB').resize((s, s), Image.LANCZOS), (i % c * s, i // c * s))
W.save(o)
