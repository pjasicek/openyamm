#!/usr/bin/env python3
"""Images of the installed Ghost GLB for the texture guard: work/img_<name>.png (bytes as installed)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbpack as G  # noqa: E402
doc, b = G.read(HERE / 'before' / 'mm9_ghost.glb'); b = bytes(b)
for im in doc['images']:
    v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    (HERE / 'work' / f"img_{im['name']}.png").write_bytes(b[o:o + v['byteLength']]); print('IMG', im['name'])
for m in doc['materials']:
    t = m['pbrMetallicRoughness']['baseColorTexture']['index']
    print('MAT', m['name'], 'base image', doc['images'][doc['textures'][t]['source']]['name'], 'extras', {k: v for k, v in m.get('extras', {}).items() if 'mask' in k or 'region' in k or 'ramp' in k})
