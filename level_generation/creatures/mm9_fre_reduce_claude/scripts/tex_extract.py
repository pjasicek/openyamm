#!/usr/bin/env python3
"""Texture-guard images of the installed GLB (bytes as installed) for mpqem.py: work/tex_<image name>.png
(Fre: body, head and braid base colours)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_fre.glb')
for im in doc['images']:
    v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    (HERE / 'work' / f"tex_{im['name']}.png").write_bytes(b[o:o + v['byteLength']]); print('TEX', im['name'])
