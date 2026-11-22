#!/usr/bin/env python3
"""The far LOD materials (Guard_A_LOD2/LOD3, own UVs from lod_repair's unwrap) inherit LOD0's emissive texture,
which does not fit their UVs, and their region mask cannot tell the gem from the red seam (both channel G). The gem is
a few pixels at their switch sizes (512 and 256 px), so the far levels do not glow: emission removed from them.
Usage: far_emission.py in.glb out.glb"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
from emission import read_glb, write_glb   # noqa: E402
doc, binary = read_glb(sys.argv[1])
for m in doc['materials']:
    if '_LOD' not in m.get('name', ''):
        continue
    had = 'emissiveTexture' in m or 'emissiveFactor' in m
    m.pop('emissiveTexture', None); m.pop('emissiveFactor', None)
    (m.get('extensions') or {}).pop('KHR_materials_emissive_strength', None)
    ex = m.get('extras') or {}
    for k in ('openyamm_pulse', 'openyamm_bloom', 'openyamm_flicker'):
        ex.pop(k, None)
    print('FAR EMISSION removed' if had else 'FAR EMISSION none', m['name'])
write_glb(sys.argv[2], doc, binary)
