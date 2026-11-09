#!/usr/bin/env python3
"""Set material extras / pbr factors on every material whose name starts with a prefix (one skin, no tier ramps,
so claude_shared/region_variants.py is not needed). Usage: material_extras.py in.glb out.glb PREFIX KEY=VALUE ...
KEY pbr.<name> sets pbrMetallicRoughness.<name>; values are JSON."""
import json, struct, sys
from pathlib import Path

src, dst, prefix = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
raw = src.read_bytes()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); binary = raw[28 + n:]
hit = 0
for m in doc['materials']:
    if not m.get('name', '').startswith(prefix):
        continue
    hit += 1
    for kv in sys.argv[4:]:
        k, v = kv.split('=', 1)
        if k.startswith('pbr.'):
            m.setdefault('pbrMetallicRoughness', {})[k[4:]] = json.loads(v)
        else:
            m.setdefault('extras', {})[k] = json.loads(v)
if not hit:
    raise SystemExit(f'no material starts with {prefix}')
enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
dst.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)
print(dst, 'materials', hit, [m['name'] for m in doc['materials']])
