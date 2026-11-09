#!/usr/bin/env python3
"""Per-material mean COLOR_0 of an export GLB's LOD0 mesh (checks the tints). Usage: colour_check.py <glb>"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'tools'))
import link_static_model_lods as link  # noqa: E402

doc, binary = link.read_glb(Path(sys.argv[1]))
for p in doc['meshes'][0]['primitives']:
    a = doc['accessors'][p['attributes']['COLOR_0']]; v = doc['bufferViews'][a['bufferView']]
    width = 4 if a['type'] == 'VEC4' else 3
    dtype, scale = {5126: (np.float32, 1.0), 5123: (np.uint16, 65535.0), 5121: (np.uint8, 255.0)}[a['componentType']]
    arr = np.frombuffer(binary, dtype, a['count'] * width, v.get('byteOffset', 0) + a.get('byteOffset', 0))
    print(doc['materials'][p['material']]['name'], (arr.reshape(-1, width).mean(0) / scale).round(3))
