#!/usr/bin/env python3
"""The converted MM9 model as a reference tier for the review viewer: its clips renamed to our role names (extra clips
dropped, 'Dead' = Die1 again) and a parent node lifting the feet onto the floor, so viewer shots at the same clip, time
and camera compare MM9 with ours. Usage: mm9_compare_glb.py <mm9 glb> <lift metres> <out glb>"""
import json, struct, sys
from pathlib import Path

src, lift, dst = Path(sys.argv[1]), float(sys.argv[2]), Path(sys.argv[3])
ROLE = {'Stand': 'Standing', 'Walk': 'Walking', 'Run': 'Running', 'Fidget1': 'Fidget', 'HAttack1': 'AttackMelee',
        'Wince1': 'Hit', 'Die1': 'Death'}
raw = src.read_bytes()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); binary = raw[28 + n:]
scene = doc['scenes'][doc.get('scene', 0)]
doc['nodes'].append({'name': 'Lift', 'translation': [0.0, lift, 0.0], 'children': scene['nodes']})
scene['nodes'] = [len(doc['nodes']) - 1]
kept = []
for a in doc['animations']:
    if a['name'] in ROLE:
        a['name'] = ROLE[a['name']]
        kept.append(a)
        if a['name'] == 'Death':
            kept.append({'name': 'Dead', 'channels': a['channels'], 'samplers': a['samplers']})
doc['animations'] = kept
enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
dst.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary))
                + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(binary), 0x004e4942) + binary)
print('MM9 reference', dst, [a['name'] for a in kept])
