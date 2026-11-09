#!/usr/bin/env python3
"""Emission of the Harvester's glow material (after hes_turrets_claude/scripts/set_emissive.py): every material whose
name starts with HS_Glow_ keeps the emissive texture build_actor.py exported (textures/harvester_glow_emissive.png:
the orange nozzle throat and vent louvres, the white-gold core slots; their dark bars stay dark), and gets
emissiveFactor [1, 1, 1] and KHR_materials_emissive_strength STRENGTH; with an emissive texture a creature material also blooms
(engine/render/MODEL_RENDERING.md, "Emission and bloom"). Edge darkening off on it. In place.
Usage: set_emissive.py <glb> [...]"""
import json, struct, sys
from pathlib import Path
STRENGTH = 1.25                                        # stronger clips the hot orange to yellow-white
for path in (Path(a) for a in sys.argv[1:]):
    raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + n]); rest = raw[20 + n:]
    hits = []
    for m in doc['materials']:
        if m.get('name', '').startswith('HS_Glow_'):
            if 'emissiveTexture' not in m:                    # build_actor.py exports harvester_glow_emissive.png
                sys.exit(f'{path}: {m["name"]} has no emissive texture')
            m['emissiveFactor'] = [1.0, 1.0, 1.0]
            m.setdefault('extensions', {})['KHR_materials_emissive_strength'] = {'emissiveStrength': STRENGTH}
            m.setdefault('extras', {})['openyamm_edge_darkening'] = 0
            hits.append(m['name'])
    if not hits:
        sys.exit(f'{path}: no HS_Glow_ material')
    used = doc.setdefault('extensionsUsed', [])
    if 'KHR_materials_emissive_strength' not in used:
        used.append('KHR_materials_emissive_strength')
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    path.write_bytes(struct.pack('<III', 0x46546c67, 2, 12 + 8 + len(enc) + len(rest))
                     + struct.pack('<II', len(enc), 0x4e4f534a) + enc + rest)
    print('EMISSIVE', path.name, hits, 'strength', STRENGTH)
