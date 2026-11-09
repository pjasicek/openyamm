#!/usr/bin/env python3
"""The attachments are rigid (no burn death of their own) but split_attachments.py copies the creature's material extras,
including openyamm_burn_map texture indices that do not exist in the attachment file (the model cook fails on them):
remove that extra from every material of the given GLBs in place. Usage: strip_attachment_burn.py <glb> [...]"""
import json, struct, sys
for path in sys.argv[1:]:
    raw = open(path, 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n])
    binary = raw[28 + n:28 + n + struct.unpack_from('<I', raw, 20 + n)[0]]
    k = 0
    for m in doc.get('materials', []):
        if 'openyamm_burn_map' in m.get('extras', {}):
            del m['extras']['openyamm_burn_map']; k += 1
            if not m['extras']: del m['extras']
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    binary += b'\0' * (-len(binary) % 4)
    open(path, 'wb').write(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary)) + struct.pack('<II', len(enc), 0x4e4f534a)
                           + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)
    print('STRIPPED', path, k)
