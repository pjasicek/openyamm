#!/usr/bin/env python3
"""The Yeti's head: its own colour image (open snarl, blue bands: a design difference), no ramps. Args: <in.glb> <out.glb>"""
import io, sys
from PIL import Image
sys.path.insert(0, '../claude_shared')
import region_variants as RV
src, dst = sys.argv[1:3]
doc, blob = RV.read_glb(src); blob = bytearray(blob)
buf = io.BytesIO(); Image.open('textures/bf_head_c_final.png').convert('RGB').save(buf, 'PNG'); data = buf.getvalue()
blob.extend(b'\0' * (-len(blob) % 4))
doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)}); blob.extend(data)
doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': 'BigfootHead_C'})
m = next(x for x in doc['materials'] if x['name'] == 'BigfootHead_C')
smp = doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)
doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': smp})
m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
e = m.get('extras', {}); e.pop('openyamm_region_mask', None); e.pop('openyamm_region_ramps', None)
RV.write_glb(dst, doc, bytes(blob)); print('TIERC done')
