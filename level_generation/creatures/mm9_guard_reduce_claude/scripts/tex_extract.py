#!/usr/bin/env python3
"""Tier base colours of the installed GLB for mpqem.py's texture guard and texture_drift.py: work/tex_<material>.png (bytes as installed)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_guard.glb')
for m in doc['materials']:
    im = doc['images'][doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]; v = doc['bufferViews'][im['bufferView']]
    o = v.get('byteOffset', 0); (HERE / 'work' / f"tex_{m['name']}.png").write_bytes(b[o:o + v['byteLength']]); print('TEX', m['name'])
