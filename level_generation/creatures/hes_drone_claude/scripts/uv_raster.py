#!/usr/bin/env python3
"""Draw the UV triangles of every primitive of a GLB: uv_raster.py in.glb out.png [size]"""
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, __import__('os').path.dirname(__file__))
from glb_io import read_glb, acc
doc, b = read_glb(sys.argv[1]); size = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
im = Image.new('RGB', (size, size), (20, 20, 20)); d = ImageDraw.Draw(im)
for m in doc['meshes'][:1]:
    for p in m['primitives']:
        if 'TEXCOORD_0' not in p['attributes']:
            continue
        uv = acc(doc, b, p['attributes']['TEXCOORD_0']) * size
        idx = acc(doc, b, p['indices']).reshape(-1, 3)
        for t in idx:
            d.polygon([tuple(uv[i]) for i in t], outline=(90, 200, 90))
im.save(sys.argv[2]); print(sys.argv[2])
