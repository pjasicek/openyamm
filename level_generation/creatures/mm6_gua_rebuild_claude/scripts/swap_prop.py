#!/usr/bin/env python3
"""The Captain's pole: a copy of the LOD GLB with the Halberd material's images replaced (MM9 skins guardpole -> guardpole2), for split_attachment.py. Args: <in glb> <out glb>"""
import sys
from pathlib import Path
sys.path.insert(0, '../claude_shared')
import region_variants as RV
doc, binary = RV.read_glb(sys.argv[1]); binary = bytearray(binary)
m = next(x for x in doc['materials'] if x['name'] == 'Halberd')
pairs = ((m['pbrMetallicRoughness']['baseColorTexture']['index'], 'halberd_c_basecolor.png'), (m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'], 'halberd_c_orm.png'), (m['normalTexture']['index'], 'halberd_c_normal.png'))
for ti, fn in pairs:
    data = Path('textures', fn).read_bytes()
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append(dict(buffer=0, byteOffset=len(binary), byteLength=len(data)))
    binary += data
    doc['images'].append(dict(name=fn[:-4], mimeType='image/png', bufferView=len(doc['bufferViews']) - 1))
    doc['textures'][ti]['source'] = len(doc['images']) - 1
d2, b2 = RV._compact(doc, bytes(binary))
RV.write_glb(sys.argv[2], d2, b2)
print('SWAPPED', sys.argv[2])
