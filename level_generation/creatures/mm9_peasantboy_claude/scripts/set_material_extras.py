#!/usr/bin/env python3
"""Set glTF material extras / factors on every material of a GLB (in place on a copy).
Usage: set_material_extras.py in.glb out.glb key=value ...   (pbr.metallicFactor=0, openyamm_specular=0, ...)"""
import json, struct, sys
from pathlib import Path

src, dst, *pairs = sys.argv[1:]
raw = Path(src).read_bytes()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n])
rest = raw[20 + n:]
for mat in doc.get('materials', []):
    for pair in pairs:
        key, value = pair.split('=', 1)
        value = json.loads(value)
        if key.startswith('pbr.'):
            mat.setdefault('pbrMetallicRoughness', {})[key[4:]] = value
        else:
            mat.setdefault('extras', {})[key] = value
js = json.dumps(doc, separators=(',', ':')).encode()
js += b' ' * (-len(js) % 4)
out = bytearray(raw[:12]) + struct.pack('<II', len(js), 0x4E4F534A) + js + rest
struct.pack_into('<I', out, 8, len(out))
Path(dst).write_bytes(out)
print('EXTRAS', dst, pairs)
