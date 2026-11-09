"""Body retexture v2 upload: the v1 Meshy return's own mesh (same faces, Meshy's v1 UV layout, which `transfer_uv.py`
copied to the rig's 'UVMap') without its images or materials. Retextured with enable_original_uv: true, the new maps
land in the UV space of the installed body texture, so neither the master nor the reduced model needs new UVs."""
import json, struct
from pathlib import Path
import numpy as np
P = Path(__file__).resolve().parents[1]
src, out = P / 'meshy/body_retexture_v1/model_urls_glb.glb', P / 'texturing/mercenary_body_upload_v2.glb'
raw = src.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; j = json.loads(raw[20:20 + n]); binary = raw[28 + n:]
pr = j['meshes'][0]['primitives'][0]
blobs, views, accessors = bytearray(), [], []
def take(index, target):
    a = dict(j['accessors'][index]); v = j['bufferViews'][a.pop('bufferView')]
    data = binary[v.get('byteOffset', 0) + a.pop('byteOffset', 0):][:v['byteLength']]
    blobs.extend(b'\0' * (-len(blobs) % 4)); views.append({'buffer': 0, 'byteOffset': len(blobs), 'byteLength': len(data), 'target': target})
    blobs.extend(data); a['bufferView'] = len(views) - 1; accessors.append(a); return len(accessors) - 1
attrs = {k: take(pr['attributes'][k], 34962) for k in ('POSITION', 'NORMAL', 'TEXCOORD_0')}
idx = take(pr['indices'], 34963)
doc = {'asset': {'version': '2.0', 'generator': 'make_body_upload_v2.py'}, 'scene': 0, 'scenes': [{'nodes': [0]}],
       'nodes': [{'mesh': 0, 'name': 'Body'}], 'meshes': [{'name': 'Body', 'primitives': [{'attributes': attrs, 'indices': idx, 'material': 0}]}],
       'materials': [{'name': 'Body', 'pbrMetallicRoughness': {'baseColorFactor': [0.8, 0.8, 0.8, 1], 'metallicFactor': 0}}],
       'accessors': accessors, 'bufferViews': views, 'buffers': [{'byteLength': 0}]}
blobs.extend(b'\0' * (-len(blobs) % 4)); doc['buffers'][0]['byteLength'] = len(blobs)
enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
out.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(blobs)) + struct.pack('<II', len(enc), 0x4e4f534a) + enc
                + struct.pack('<II', len(blobs), 0x004e4942) + bytes(blobs))
print('UPLOAD', out, out.stat().st_size, 'tris', j['accessors'][pr['indices']]['count'] // 3)
