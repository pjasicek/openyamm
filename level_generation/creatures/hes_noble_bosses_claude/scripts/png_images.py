#!/usr/bin/env python3
"""Re-encode every non-PNG image of a GLB as PNG (the model cook takes PNG only). Usage: png_images.py in.glb out.glb"""
import io, json, struct, sys
from pathlib import Path
from PIL import Image
raw = Path(sys.argv[1]).read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); binary = bytearray(raw[28 + n:])
changed = 0
for im in doc.get('images', []):
    if im.get('mimeType') == 'image/png':
        continue
    v = doc['bufferViews'][im['bufferView']]
    data = bytes(binary[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']])
    buf = io.BytesIO(); Image.open(io.BytesIO(data)).save(buf, 'PNG'); png = buf.getvalue()
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(png)}); binary += png
    im['bufferView'] = len(doc['bufferViews']) - 1; im['mimeType'] = 'image/png'; changed += 1
binary += b'\0' * (-len(binary) % 4); doc['buffers'][0]['byteLength'] = len(binary)
js = json.dumps(doc, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
Path(sys.argv[2]).write_bytes(struct.pack('<III', 0x46546C67, 2, 28 + len(js) + len(binary))
                              + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(binary), 0x004E4942) + binary)
print('PNG images re-encoded:', changed)
