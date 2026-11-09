#!/usr/bin/env python3
"""LOD extras, one node, specular off, then mirror (the skeleton is mirrored last). Usage: post_hat.py in.glb out.glb"""
import json, struct, subprocess, sys
src, dst = sys.argv[1:3]
raw = open(src, 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); blob = raw[20 + n + 8:]
names = {nd['name']: i for i, nd in enumerate(doc['nodes'])}
meshes = {nd['name']: nd['mesh'] for nd in doc['nodes'] if 'mesh' in nd}
base = meshes['Hat']; lods = [meshes['Hat_LOD1'], meshes['Hat_LOD2']]
doc['meshes'][base]['extras'] = {'openyamm_lods': lods}
hat = names['Hat']
doc['scenes'][0]['nodes'] = [hat]
for i in ('Hat_LOD1', 'Hat_LOD2'):
    doc['nodes'][names[i]].pop('mesh'); 
for m in doc['materials']:
    m.setdefault('extras', {})['openyamm_specular'] = 0.0
    m.setdefault('pbrMetallicRoughness', {})['metallicFactor'] = 0.0
enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
open(dst + '.tmp.glb', 'wb').write(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(blob)) + struct.pack('<II', len(enc), 0x4e4f534a) + enc + struct.pack('<II', len(blob), 0x004e4942) + blob)
print(subprocess.run([sys.executable, 'v2/scripts/mirror_glb.py', dst + '.tmp.glb', dst], capture_output=True, text=True).stdout.strip())
