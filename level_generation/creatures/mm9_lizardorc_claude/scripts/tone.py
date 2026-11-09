#!/usr/bin/env python3
"""Tier tone, colour only: base colour factors per material toward MM9's darker skins. Args: <in> <out>"""
import json, struct, sys
IN, OUT = sys.argv[1:3]
raw = open(IN, 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + n]); blob = raw[20 + n:]
F = {'Trog_B': [.80, .86, .76, 1], 'TrogHead_B': [.80, .86, .76, 1]}
for m in doc['materials']:
    if m['name'] in F: m['pbrMetallicRoughness']['baseColorFactor'] = F[m['name']]
j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
open(OUT, 'wb').write(struct.pack('<III', 0x46546C67, 2, 20 + len(j) + len(blob)) + struct.pack('<II', len(j), 0x4E4F534A) + j + blob)
print('tone', [(m['name'], m['pbrMetallicRoughness'].get('baseColorFactor')) for m in doc['materials']])
