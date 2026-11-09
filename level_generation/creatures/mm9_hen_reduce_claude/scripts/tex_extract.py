#!/usr/bin/env python3
"""Guard images for mpqem.py: every material's base colour (and region mask, when the material has one as an extension or a
second texture) as installed: work/tex_<material>_<slot>.png. Usage: tex_extract.py <glb>"""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
doc, b = gb.read(sys.argv[1])
def dump(mat, slot, tex_index):
    im = doc['images'][doc['textures'][tex_index]['source']]
    v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    (HERE / 'work' / f"tex_{mat['name']}_{slot}.png").write_bytes(b[o:o + v['byteLength']]); print('TEX', mat['name'], slot, im.get('name'), v['byteLength'])
for mat in doc['materials']:
    bc = mat.get('pbrMetallicRoughness', {}).get('baseColorTexture')
    if bc: dump(mat, 'B', bc['index'])
    rm = mat.get('extras', {}).get('openyamm_region_mask')
    if rm: dump(mat, 'M', rm['index'])
    for k, ext in mat.get('extensions', {}).items():
        print('  ext', mat['name'], k, json.dumps(ext)[:200])
    print('  extras', mat['name'], json.dumps(mat.get('extras', {}))[:300])
