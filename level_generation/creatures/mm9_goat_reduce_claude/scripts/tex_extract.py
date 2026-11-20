#!/usr/bin/env python3
"""Goat copy (2026-11-05) of the Ram/Cow texture-guard extract: the goat has one material (Goat), no region mask and no
tiers, so the guard image for mpqem.py is the installed base colour only: work/tex_Goat_B.png (bytes as installed)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_goat.glb')
mat = next(m for m in doc['materials'] if m['name'] == 'Goat')
im = doc['images'][doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]
v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
(HERE / 'work' / 'tex_Goat_B.png').write_bytes(b[o:o + v['byteLength']]); print('TEX Goat B', im.get('name'), v['byteLength'])
