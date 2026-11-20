#!/usr/bin/env python3
"""Viewer copies for the reduction review: a LOD0-only GLB (three.js would draw every LOD and shadow mesh) with its
base colour replaced by the Gorgon's baked tier textures (mm8_m564_claude/work/tier_<variant>_Gorgon_A.png, written by
that project's viewer_tiers.py; the engine applies the same ramps at runtime). Writes review/viewer/mm8_m564_<label>_<tier>.glb.
Usage: viewer_tiers.py <label> <lod0.glb> [tier letters, default abc]"""
import io, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
P = Path(__file__).resolve().parents[1]; TIERS = P.parent / 'mm8_m564_claude' / 'work'
label, src = sys.argv[1], Path(sys.argv[2]); letters = sys.argv[3] if len(sys.argv) > 3 else 'abc'
for t in letters:
    doc, binary = read_glb(src); binary = bytearray(binary)
    png = (TIERS / f'tier_gorgon_{t}_Gorgon_A.png').read_bytes()
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(png)}); binary += png
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': f'Gorgon_A_{t}'})
    for mat in doc['materials']:
        info = mat['pbrMetallicRoughness']['baseColorTexture']
        doc['textures'].append(dict(doc['textures'][info['index']], source=len(doc['images']) - 1))
        info['index'] = len(doc['textures']) - 1
    out = P / 'review' / 'viewer' / f'mm8_m564_{label}_{t}.glb'; write_glb(out, doc, bytes(binary)); print('VIEWER', out.name)
