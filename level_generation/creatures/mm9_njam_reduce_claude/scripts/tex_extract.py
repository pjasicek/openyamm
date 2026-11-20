#!/usr/bin/env python3
"""Base colour of each material of the installed GLB (one skin: Njam limbs, NjTorso, NjHead) for mpqem.py's texture guard and
chart tests: work/tex_<material>.png (bytes as installed)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_njam.glb')
for m in doc['materials']:
    ti = m['pbrMetallicRoughness']['baseColorTexture']['index']
    src = doc['textures'][ti]['source']; im = doc['images'][src]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); (HERE / 'work' / f"tex_{m['name']}.png").write_bytes(b[o:o + v['byteLength']]); print('TEX', m['name'], 'image', src)
