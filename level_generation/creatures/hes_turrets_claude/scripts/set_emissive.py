#!/usr/bin/env python3
"""Give every material whose name ends in _Energy the glTF emission: emissiveFactor FACTOR (blue-white) and, with
--texture, emissiveTexture = its own base colour texture (the energy swatch and the painted grooves), so the glow
follows the painted energy. Without the texture the energy faces glow a flat blue-white. tools/cook_models.py
rejects emissiveTexture today ("which the engine does not sample"), so the runtime exports carry the factor only
until the engine samples emissive textures on actors (then build_runtime.sh with EMISSIVE_TEXTURE=1).
Edge darkening off on them. In place. Usage: set_emissive.py [--texture] <glb> [...]"""
import json, struct, sys
from pathlib import Path
FACTOR = [0.70, 0.85, 1.0]
args = sys.argv[1:]
with_texture = '--texture' in args
for path in (Path(a) for a in args if a != '--texture'):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + n]); rest = raw[20 + n:]
    hits = []
    for m in doc['materials']:
        if m.get('name', '').endswith('_Energy'):
            tex = m['pbrMetallicRoughness']['baseColorTexture']
            m['emissiveFactor'] = FACTOR
            if with_texture:
                m['emissiveTexture'] = {'index': tex['index'], **({'texCoord': tex['texCoord']} if 'texCoord' in tex else {})}
            else:
                m.pop('emissiveTexture', None)
            m.setdefault('extras', {})['openyamm_edge_darkening'] = 0
            hits.append(m['name'])
    if not hits:
        sys.exit(f'{path}: no _Energy material')
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 12 + 8 + len(enc) + len(rest))
                     + struct.pack('<II', len(enc), 0x4e4f534a) + enc + rest)
    print('EMISSIVE', path.name, hits, 'factor', FACTOR, 'texture' if with_texture else 'no texture')
