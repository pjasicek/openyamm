#!/usr/bin/env python3
"""Glow and dark-copy materials, in place: every material named HS_*_Energy gets the factor-only emission
(emissiveFactor GLOW[<name>], no emissive texture: rule 4 of CREATURE_BUILDS.md) with bloom and no edge darkening;
HS_*_Dark (the off state's copy of the glowing faces) gets baseColorFactor DARK, metallic 0, roughness 0.75, no
emission; HS_*_Hot (the emplacement's wind-up) gets HOT. All HS_ materials: edge darkening 0 (machines, like the turrets' undarkened mounts).
Usage: set_glow.py <name> <glb>"""
import json
import struct
import sys
from pathlib import Path

GLOW = {'starport_turret': [0.70, 0.85, 1.0],          # the colony's blue-white (the Ward Turret's)
        'capacitor_column': [0.62, 0.42, 1.0],         # the Lattice's violet-white
        'throne_conduit': [0.62, 0.42, 1.0],
        'test_emplacement': [0.24, 0.08, 0.46]}      # the great cannon's resting violet (its rest state)
HOT = [0.9, 0.62, 1.0]                               # the emplacement's wind-up layer (HS_*_Hot): white-violet
DARK = [0.22, 0.2, 0.26, 1.0]
# the emplacement's zones are untextured near-black violet: its dark copy must be darker than the grey factor above
DARK_FOR = {'test_emplacement': [0.025, 0.02, 0.035, 1.0]}
HOT_STRENGTH = 3.0                                   # KHR_materials_emissive_strength on the wind-up layer
name, path = sys.argv[1], Path(sys.argv[2])
raw = path.read_bytes(); n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); rest = raw[20 + n:]
seen = []
for m in doc['materials']:
    label = m.get('name', '')
    if not label.startswith('HS_'):
        continue
    extras = m.setdefault('extras', {})
    extras['openyamm_edge_darkening'] = 0
    pbr = m.setdefault('pbrMetallicRoughness', {})
    if '_Hot' in label:
        m['emissiveFactor'] = HOT
        m.setdefault('extensions', {})['KHR_materials_emissive_strength'] = {'emissiveStrength': HOT_STRENGTH}
        used = doc.setdefault('extensionsUsed', [])
        if 'KHR_materials_emissive_strength' not in used:
            used.append('KHR_materials_emissive_strength')
        m.pop('emissiveTexture', None)
        extras['openyamm_bloom'] = True
        pbr['metallicFactor'] = 0.0
        seen.append(label)
    elif '_Energy' in label:
        m['emissiveFactor'] = GLOW[name]
        m.pop('emissiveTexture', None)
        extras['openyamm_bloom'] = True
        pbr['metallicFactor'] = 0.0
        seen.append(label)
    elif '_Dark' in label:
        pbr['baseColorFactor'] = DARK_FOR.get(name, DARK)
        pbr['metallicFactor'] = 0.0
        pbr['roughnessFactor'] = 0.75
        m.pop('emissiveFactor', None)
        seen.append(label)
    assert 'emissiveTexture' not in m
if not any('_Energy' in s for s in seen):
    sys.exit(f'{path}: no _Energy material')
enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
path.write_bytes(struct.pack('<III', 0x46546c67, 2, 12 + 8 + len(enc) + len(rest))
                 + struct.pack('<II', len(enc), 0x4e4f534a) + enc + rest)
print('GLOW', path.name, seen, GLOW[name])
