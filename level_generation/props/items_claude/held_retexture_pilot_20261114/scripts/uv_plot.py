#!/usr/bin/env python3
"""Draw the UV layout of a GLB's first mesh (filled triangles, island borders) to a PNG.
Usage: python3 -I uv_plot.py <in.glb> <out.png> [size]"""
import json
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

glb, out = sys.argv[1], sys.argv[2]
size = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
data = open(glb, 'rb').read()
jlen = struct.unpack('<I', data[12:16])[0]
doc = json.loads(data[20:20 + jlen])
binary = data[20 + jlen + 8:]
TYPES = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}
COUNTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}


def accessor(i):
    a = doc['accessors'][i]
    view = doc['bufferViews'][a['bufferView']]
    start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
    n = a['count'] * COUNTS[a['type']]
    return np.frombuffer(binary, TYPES[a['componentType']], n, start).reshape(a['count'], -1)


prim = doc['meshes'][0]['primitives'][0]
uv = accessor(prim['attributes']['TEXCOORD_0'])
idx = accessor(prim['indices']).ravel().reshape(-1, 3)
img = Image.new('RGB', (size, size), (20, 20, 20))
draw = ImageDraw.Draw(img)
for t in idx:
    pts = [(float(uv[k, 0]) * size, float(uv[k, 1]) * size) for k in t]
    draw.polygon(pts, fill=(90, 140, 200), outline=(200, 220, 255))
img.save(out)
