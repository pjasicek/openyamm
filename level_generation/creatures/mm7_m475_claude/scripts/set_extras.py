#!/usr/bin/env python3
"""Material extras for a creature with ONE look (all three m475 descriptors draw palette 527): no colour variants,
no region mask; only claude_shared/region_variants.py's --extra step (specular mask on, metallic 0), done in place.
Usage: set_extras.py in.glb out.glb NAME_PREFIX KEY=VALUE [NAME_PREFIX KEY=VALUE ...]  (values are JSON; pbr.<k>
sets pbrMetallicRoughness.<k>)"""
import json, struct, sys
from pathlib import Path
src, dst, items = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:]
raw = src.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); rest = raw[20 + n:]
for prefix, kv in zip(items[::2], items[1::2]):
    key, value = kv.split('=', 1); value = json.loads(value)
    hit = [m for m in doc['materials'] if m.get('name', '').startswith(prefix)]
    if not hit:
        sys.exit(f'no material starts with {prefix}')
    for m in hit:
        if key.startswith('pbr.'):
            m.setdefault('pbrMetallicRoughness', {})[key[4:]] = value
        else:
            m.setdefault('extras', {})[key] = value
enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
dst.write_bytes(struct.pack('<III', 0x46546c67, 2, 12 + 8 + len(enc) + len(rest)) + struct.pack('<II', len(enc), 0x4e4f534a) + enc + rest)
print('EXTRAS', dst, [m['name'] for m in doc['materials']])
