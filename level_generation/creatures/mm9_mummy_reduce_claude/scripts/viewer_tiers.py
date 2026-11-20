#!/usr/bin/env python3
"""Review-viewer GLBs (the creature's own viewer_tiers.py with input/output arguments): the given GLB with each tier's materials
as the primitives' default (KHR_materials_variants resolved), specular off as the creature's viewer.
Usage: viewer_tiers.py <glb> <prefix>  -> work/viewer_<prefix>_a/b/c.glb"""
import json, struct, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
raw = Path(sys.argv[1]).read_bytes(); pre = sys.argv[2]
n = struct.unpack_from('<I', raw, 12)[0]; doc0 = json.loads(raw[20:20 + n]); blob = raw[28 + n:]
for vi, name in enumerate(('a', 'b', 'c')):
    doc = json.loads(json.dumps(doc0))
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            e = p.get('extensions', {}).get('KHR_materials_variants')
            if e:
                p['material'] = next(m['material'] for m in e['mappings'] if vi in m['variants'])
                del p['extensions']['KHR_materials_variants']
                if not p['extensions']: del p['extensions']
    doc.pop('extensions', None); doc['extensionsUsed'] = [x for x in doc.get('extensionsUsed', []) if x != 'KHR_materials_variants']
    for m in doc['materials']:
        ext = m.setdefault('extensions', {}); ext['KHR_materials_specular'] = {'specularFactor': 0}
    if 'KHR_materials_specular' not in doc['extensionsUsed']: doc['extensionsUsed'].append('KHR_materials_specular')
    j = json.dumps(doc, separators=(',', ':')).encode(); j += b' ' * (-len(j) % 4)
    with open(HERE / f'work/viewer_{pre}_{name}.glb', 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 28 + len(j) + len(blob))); f.write(struct.pack('<II', len(j), 0x4E4F534A)); f.write(j)
        f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
print('viewer tiers', pre)
