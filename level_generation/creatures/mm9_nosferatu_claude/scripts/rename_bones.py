"""Rename MM9's `vampiresB` biped to the `Bip01` names every shared gate expects; drop nothing. Args: in.glb out.glb"""
import json, struct, sys
src, dst = sys.argv[1:3]
raw = open(src, 'rb').read()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); rest = raw[20 + n:]
for x in doc['nodes']:
    if x.get('name', '').startswith('vampiresB'): x['name'] = x['name'].replace('vampiresB', 'Bip01', 1)
for x in doc.get('meshes', []):
    if x.get('name', '').startswith('vampiresB'): x['name'] = x['name'].replace('vampiresB', 'Bip01', 1)
j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
total = 12 + 8 + len(j) + len(rest)
with open(dst, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, total)); f.write(struct.pack('<II', len(j), 0x4E4F534A)); f.write(j); f.write(rest)
print('RENAMED', dst)
