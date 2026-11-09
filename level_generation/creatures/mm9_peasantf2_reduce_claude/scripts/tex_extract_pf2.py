#!/usr/bin/env python3
"""Base colour and region mask images of the installed PeasantF2 GLB for mpqem.py's texture guard: work/tex_body_tone.png,
tex_body_mask.png, tex_head_a.png, tex_head_b.png (bytes as installed)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(HERE / 'before' / 'mm9_peasantf2.glb')
want = {'pf_body_tone': 'tex_body_tone.png', 'pf_body_mask': 'tex_body_mask.png', 'pf_head_a_fix': 'tex_head_a.png', 'pf_head_b_fix': 'tex_head_b.png'}
for im in doc['images']:
    if im.get('name') in want:
        v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
        (HERE / 'work' / want[im['name']]).write_bytes(b[o:o + v['byteLength']]); print('TEX', want[im['name']])
