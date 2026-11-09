#!/usr/bin/env python3
"""Draw a UV triangle dump (uv_check.py's <prefix>_uvtris.npy) as <prefix>_layout.png."""
import sys
import numpy as np
from PIL import Image, ImageDraw
prefix = sys.argv[1]; size = 1024
t = np.load(prefix + '_uvtris.npy')
im = Image.new('RGB', (size, size), (20, 20, 20)); d = ImageDraw.Draw(im)
for tri in t:
    d.polygon([(u * size, (1 - v) * size) for u, v in tri], fill=(90, 140, 90), outline=(200, 230, 200))
im.save(prefix + '_layout.png')
