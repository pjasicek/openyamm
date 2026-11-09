#!/usr/bin/env python3
"""As ../mm6_pman_claude_20261013/scripts/assemble_runtime.py: drop KHR_materials_specular (the engine reads
openyamm_specular). Usage: strip_specular.py <glb> ... (in place)"""
import json, struct, sys
from pathlib import Path
for path in map(Path, sys.argv[1:]):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n]); binary = raw[28 + n:]
    for m in doc['materials']:
        ext = m.get('extensions', {}); ext.pop('KHR_materials_specular', None)
        if not ext:
            m.pop('extensions', None)
    for k in ['extensionsUsed', 'extensionsRequired']:
        if k in doc:
            doc[k] = [s for s in doc[k] if s != 'KHR_materials_specular']
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary)) + struct.pack('<II', len(enc), 0x4e4f534a)
                     + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)
    print('STRIPPED', path.name)
