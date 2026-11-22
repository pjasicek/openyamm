#!/usr/bin/env python3
"""The deep-water variant of the installed octopod for indoor swimmers inside water volumes (P4's Great Octopods,
lane S session 8): the same GLB with the surface foam ring's node emptied (its `mesh` and `skin` removed; the node
stays so no index moves). Everything else (body, LODs, shadows, clips, skins) is byte-identical.
Usage: deep_variant.py <installed source glb> <out glb>"""
import json
import struct
import sys

src, out = sys.argv[1], sys.argv[2]
data = open(src, 'rb').read()
json_len = struct.unpack('<I', data[12:16])[0]
doc = json.loads(data[20:20 + json_len])
rest = data[20 + json_len:]
foam = [n for n in doc['nodes'] if n.get('name') == 'Foam']
assert len(foam) == 1 and 'mesh' in foam[0], 'no Foam mesh node'
foam[0].pop('mesh')
foam[0].pop('skin', None)
encoded = json.dumps(doc, separators=(',', ':')).encode()
encoded += b' ' * (-len(encoded) % 4)
total = 12 + 8 + len(encoded) + len(rest)
open(out, 'wb').write(struct.pack('<III', 0x46546c67, 2, total) + struct.pack('<II', len(encoded), 0x4e4f534a)
                      + encoded + rest)
print('foam node emptied:', out)
