#!/usr/bin/env python3
"""Review-viewer GLBs for Annud's two looks (three.js has no region ramps): tier a = the GLB as is (default material); tier b
(pm6_a) = a copy whose body and head base colour images are replaced by work/tex_Annud_B.png / tex_AnnudHead_B.png (tex_extract.py:
the pm6_a ramps applied by the engine rule, claude_shared/tier_textures.apply). Geometry, clips and every other byte unchanged.
Usage: viewer_tiers_annud.py <glb> <out_a.glb> <out_b.glb>"""
import io, shutil, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbpack as G  # noqa: E402
src, oa, ob = sys.argv[1:4]
shutil.copyfile(src, oa)
doc, binary = G.read(src)
for m in doc['materials'][:2]:
    img = doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
    data = (HERE / 'work' / f"tex_{m['name']}_B.png").read_bytes()
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary += data
    doc['images'][img]['bufferView'] = len(doc['bufferViews']) - 1; doc['images'][img]['mimeType'] = 'image/png'
    print('TIER b', m['name'], doc['images'][img].get('name'))
G.write(ob, doc, binary)
