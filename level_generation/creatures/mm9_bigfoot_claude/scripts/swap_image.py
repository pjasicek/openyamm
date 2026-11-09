#!/usr/bin/env python3
"""Replace a material's base colour image in a GLB in place of a re-export (texture-only rebuilds: the clips and meshes
stay byte for byte). Args: <glb> <material name> <png>"""
import io, sys
from PIL import Image
sys.path.insert(0, '../claude_shared')
import region_variants as RV
path, mat, png = sys.argv[1:4]
doc, blob = RV.read_glb(path); blob = bytearray(blob)
buf = io.BytesIO(); Image.open(png).convert('RGB').save(buf, 'PNG'); data = buf.getvalue()
blob.extend(b'\0' * (-len(blob) % 4))
doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)}); blob.extend(data)
m = next(x for x in doc['materials'] if x['name'] == mat)
tex = doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]
doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': mat + '_base'})
tex['source'] = len(doc['images']) - 1
RV.write_glb(path, doc, bytes(blob)); print('SWAPPED', mat, png)
