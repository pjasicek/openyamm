#!/usr/bin/env python3
"""Copy texturing/octopod_upload.glb with a dummy 2048 base-colour material 'measure' on every primitive
(work/upload_mat.glb), so claude_shared/texture_quality.py can gate the layout before the paint."""
import io, json, struct
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
raw = (ROOT / 'texturing/octopod_upload.glb').read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); binary = bytearray(raw[28 + n:])
buf = io.BytesIO(); Image.new('RGB', (2048, 2048), (128, 128, 128)).save(buf, 'PNG')
binary += b'\0' * (-len(binary) % 4)
doc.setdefault('bufferViews', []).append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
binary += buf.getvalue()
doc['images'] = [{'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png'}]
doc['textures'] = [{'source': 0}]
doc['materials'] = [{'name': 'measure', 'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}}}]
for m in doc['meshes']:
    for p in m['primitives']:
        p['material'] = 0
binary += b'\0' * (-len(binary) % 4)
doc['buffers'][0]['byteLength'] = len(binary)
enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
(ROOT / 'work/upload_mat.glb').write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
    + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)
print('WROTE work/upload_mat.glb')
