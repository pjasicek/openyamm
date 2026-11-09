#!/usr/bin/env python3
"""Albedo match for the leftover trees: multiply every primitive's COLOR_0 (all LODs, impostor included) by the
species' linear `albedo_tint` [r, g, b] (species/<id>.json), so the flat albedo (texture x COLOR_0, scripts/albedo.py)
matches the native sprite's mean; the indoor engine lights the model like the sprite. Reads
work/plants/<id>/tree_cut.glb, writes work/plants/<id>/tree_tinted.glb (finish_plants.py exports it).
Tints are below 1 (the trees' leaf textures are brighter than the dark native sprites).
Usage: plant_tint.py <id>"""
import json
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link  # noqa: E402

sid = sys.argv[1]
tint = np.array(json.load(open(HERE / 'scripts' / 'species' / f'{sid}.json')).get('albedo_tint', [1.0, 1.0, 1.0]))
work = HERE / 'work' / 'plants' / sid
document, binary = link.read_glb(work / 'tree_cut.glb')
SCALE = {5121: (np.uint8, 255.0), 5123: (np.uint16, 65535.0), 5126: (np.float32, 1.0)}
done = set()
for mesh in document['meshes']:
    for primitive in mesh['primitives']:
        index = primitive['attributes']['COLOR_0']
        if index in done:
            continue
        done.add(index)
        accessor = document['accessors'][index]; view = document['bufferViews'][accessor['bufferView']]
        dtype, scale = SCALE[accessor['componentType']]
        n = {'VEC3': 3, 'VEC4': 4}[accessor['type']]
        offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        size = accessor['count'] * n * np.dtype(dtype).itemsize
        values = np.frombuffer(bytes(binary[offset:offset + size]), dtype).reshape(-1, n).astype(np.float64) / scale
        values[:, :3] = np.clip(values[:, :3] * tint, 0.0, 1.0)
        encoded = values * scale if scale == 1.0 else np.round(values * scale)
        binary[offset:offset + size] = encoded.astype(dtype).tobytes()
link.write_glb(work / 'tree_tinted.glb', document, binary)
print('TINT', sid, tint.tolist(), 'accessors', len(done), work / 'tree_tinted.glb')
