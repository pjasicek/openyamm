#!/usr/bin/env python3
"""Roles json for clips_mm9.py on the MM9 dwarf FEMALE townsfolk skeleton (PEASANTFEMALEDWARF.abc library, 10 clips,
all carried: NPCbase / shopkeeper / Bankorb scripts play no named clip, so the core roles plus MM9's three fidgets and
conv1). Scene Root carries Spine1, the skirt ring Bone22 and both thighs: all root nodes (full translation).
Usage: dwarf_roles.py <out json> [--lib source/mm9_lib/pfemaledwarf.glb]"""
import json, sys

ROLE = {   # role: (library clip, options); the whole PEASANTFEMALEDWARF library (10 clips)
    'Standing': ('stand', {'loop': True}),
    'Walking': ('walk', {'loop': True}),
    'Running': ('run', {'loop': True}),
    'Talk': ('conv1', {'ease': 'both'}),
    'Fidget': ('fidget2', {'ease': 'both'}),
    'Fidget2': ('fidget3', {'ease': 'both'}),
    'Fidget3': ('fidget4', {'ease': 'both'}),
    'AttackMelee': ('hattack', {'ease': 'both'}),
    'Hit': ('wince', {'ease': 'both'}),
    'Death': ('die1', {'ease': 'in'}),
}
EXTRA = {}
out = sys.argv[1]
lib = sys.argv[sys.argv.index('--lib') + 1] if '--lib' in sys.argv else 'source/mm9_lib/pfemaledwarf.glb'
roles = dict(ROLE)
if '--all' in sys.argv:
    roles.update(EXTRA)
FA = {}
for S in 'LR':
    for f, m in (('Index', 0.75), ('Middle', 0.85), ('Ring', 0.95), ('Pinky', 1.0)):
        FA[f'Bip01 {S} {f}1'] = [f'Bip01 {S} Finger1', m, 'copy']
        FA[f'Bip01 {S} {f}2'] = [f'Bip01 {S} Finger11', 0.9 * m, 'copy']
        FA[f'Bip01 {S} {f}3'] = [f'Bip01 {S} Finger11', 0.5 * m, 'delta']
    FA[f'Bip01 {S} Thumb1'] = [f'Bip01 {S} Finger0', 1.0, 'copy']
    FA[f'Bip01 {S} Thumb2'] = [f'Bip01 {S} Finger01', 1.0, 'copy']
    FA[f'Bip01 {S} Thumb3'] = [f'Bip01 {S} Finger01', 0.7, 'delta']
spec = {
    'root': 'Bip01 Spine1',
    'root_nodes': ['Bip01 Spine1', 'Scene Root', 'Bone22', 'Bip01 L Thigh', 'Bip01 R Thigh'],
    'foot': 'Bip01 L Toe0',
    'sources': {'lib': lib},
    'standing': 'Standing',
    'dead_from': 'Death',
    'roles': {r: dict({'src': 'lib', 'clips': [c]}, **o) for r, (c, o) in roles.items()},
    'lift_to_floor': False,
    'finger_alias': FA,
    'soft_offsets': True,
    # the female library's clips start at their bind (no source_offset, unlike the male dwarf library)
    '_note': 'written by scripts/dwarf_roles.py (peasantdf)' + (' --all' if '--all' in sys.argv else ''),
}
json.dump(spec, open(out, 'w'), indent=1)
print('ROLES', out, len(roles))
