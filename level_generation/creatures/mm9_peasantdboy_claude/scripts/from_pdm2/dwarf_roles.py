#!/usr/bin/env python3
"""Roles json for clips_mm9.py on the MM9 dwarf male townsfolk skeleton (PEASANTMALEDWARF.abc library, 21 clips).

Usage: dwarf_roles.py <out json> [--all] [--lib source/mm9_lib/pmaledwarf.glb]
Default: the MM9 roles + the clips PeasantDM2's DAT objects' scripts play (rows 8/13/14: NPCbase -> BaseRun.inc
LoopAnim Cower; NPC109 stand/conv1 + basemelee; DwarvenMiner rub_beard/rock/hammer/dump). --all writes every library
clip (the next dwarf body, PeasantDM2..4, picks its own subset from that list).
The skeleton has no pelvis: Bip01 Spine is the root, and the tunic ring Bone22 hangs from the Scene Root and carries
the pelvis' translation itself, so it is a root node too (otherwise the skirt stays behind when the body moves)."""
import json, sys

ROLE = {   # role: (library clip, options)
    'Standing': ('stand', {'loop': True}),
    'Walking': ('walk', {'loop': True}),
    'Running': ('run', {'loop': True}),
    'Fidget': ('Fidget1', {'ease': 'both'}),
    'Fidget2': ('Fidget2', {'ease': 'both'}),
    'Talk': ('conv1', {'ease': 'both'}),
    'AttackMelee': ('hattack1', {'ease': 'both'}),
    'Hit': ('wince', {'ease': 'both'}),
    'Death': ('die1', {'ease': 'in'}),
    'Cower': ('cower', {'loop': True}),
    'RubBeard': ('Rub_beard', {'ease': 'both'}),
    'Rock': ('Rock', {'ease': 'both'}),
    'Hammer': ('hammer', {'ease': 'both'}),
    'Dump': ('Dump', {'ease': 'both'}),
}
EXTRA = {  # the rest of the library (not played by PeasantDM2's scripts)
    'Push': ('push', {'ease': 'both'}),
    'X': ('x', {'ease': 'both'}),
    'CowerStart': ('cowerstart', {'ease': 'in'}),
    'CowerEnd': ('cowerend', {'ease': 'both'}),
    'Npc008': ('NPC_008', {'ease': 'both'}),
    'WalkCarry': ('walk-carry', {'loop': True}),
    'Guard': ('Guard', {'ease': 'both'}),
}
out = sys.argv[1]
lib = sys.argv[sys.argv.index('--lib') + 1] if '--lib' in sys.argv else 'source/mm9_lib/pmaledwarf.glb'
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
    'root': 'Bip01 Spine',
    'root_nodes': ['Bip01 Spine', 'Scene Root', 'Bone22'],
    'foot': 'Bip01 L Toe0',
    'sources': {'lib': lib},
    'standing': 'Standing',
    'dead_from': 'Death',
    'roles': {r: dict({'src': 'lib', 'clips': [c]}, **o) for r, (c, o) in roles.items()},
    'lift_to_floor': False,
    'finger_alias': FA,
    'soft_offsets': True,
    # the library's clips carry the pelvis and the tunic ring 0.2214 m above their bind place (clips_mm9.py source_offset)
    'source_offset': {'Bip01 Spine': [0, 0.2214, 0], 'Bone22': [0, 0.2214, 0]},
    '_note': 'written by scripts/dwarf_roles.py' + (' --all' if '--all' in sys.argv else ''),
}
json.dump(spec, open(out, 'w'), indent=1)
print('ROLES', out, len(roles))
