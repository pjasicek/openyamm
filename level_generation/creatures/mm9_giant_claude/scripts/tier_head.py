#!/usr/bin/env python3
"""Per-tier head images (a design difference: red braids and headband against loose dark hair, earrings; MM9 has two heads):
GiantHead_B takes textures/gi_head_b_final.png and gi_head_b_normal.png; both head materials drop the unused ramp extras.
Args: <in.glb> <out.glb>"""
import io, sys
from PIL import Image
sys.path.insert(0, '../claude_shared')
import region_variants as RV
src, dst = sys.argv[1:3]
doc, blob = RV.read_glb(src); blob = bytearray(blob)
def add_image(path, name, rgb=True):
    buf = io.BytesIO(); Image.open(path).convert('RGB').save(buf, 'PNG'); data = buf.getvalue()
    blob.extend(b'\0' * (-len(blob) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)}); blob.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    return len(doc['images']) - 1
m = next(x for x in doc['materials'] if x['name'] == 'GiantHead_B')
smp = doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler', 0)
doc['textures'].append({'source': add_image('textures/gi_head_b_final.png', 'GiantHead_B'), 'sampler': smp})
m['pbrMetallicRoughness']['baseColorTexture'] = {'index': len(doc['textures']) - 1}
if 'normalTexture' in m:
    doc['textures'].append({'source': add_image('textures/gi_head_b_normal.png', 'GiantHead_B_normal'), 'sampler': smp})
    m['normalTexture'] = dict(m['normalTexture'], index=len(doc['textures']) - 1)
for x in doc['materials']:
    if x['name'].startswith('GiantHead_'):
        e = x.get('extras', {}); e.pop('openyamm_region_mask', None); e.pop('openyamm_region_ramps', None)
RV.write_glb(dst, doc, bytes(blob)); print('TIERHEAD done')
