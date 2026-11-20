#!/usr/bin/env python3
"""Append or replace the Wyrde bindings in assets_dev/worlds/mm9/models/actors.yml and their rows in
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root; re-reads both files inside it)."""
import os
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN = '# >>> mm9_wyrde_claude'; END = '# <<< mm9_wyrde_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 Wyrdes (level_generation/creatures/mm9_wyrde_claude): wyrd_young.ABC and wyrd_mature.ABC are one mesh, so one Meshy body on MM9's human
# female skeleton (73 joints, skirt chains keyed as MM9 keys them, MPFB female hands with 15 finger bones per side), the MM9 PeasantFemale
# clip library, whole model mirrored to true handedness. One body paint with region ramps (mantle, gown, Verdandi's damask and cord), a
# head and hood colour per tier (two different women). Rows run basemelee.scr; no script plays any clip on them (WG_NPC334.scr only toggles
# their visibility in the win cutscene), so only MM9's roles are carried; the library has no attack: attacks play Fidget.
"""
for row, name, skin, label in ((264, 'Wyrde of the Knowing (Verdandi)', 'wy_mature', 'wyrd_mature.ABC, skin wyrdmature, DAT WyrdeoftheKnowing (Hall of the Gods)'),
                               (265, 'Wyrde of the Unknown (Morgan)', 'wy_young', 'wyrd_young.ABC, skin wyrdyoung, DAT class WyrdeoftheUnknown (Hall of the Gods)')):
    BLOCK += f"""# {name}: row {row}, {label}
- descriptor: MM9 {row} {name}
  model: worlds/mm9/models/mm9_wyrde.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 0.95
    run_stride_length: 1.13
    upper_body_root: FHP Spine2
    look: {{nodes: [FHP Neck, FHP Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 1.0}}
      attack_ranged: {{impact: 1.0}}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Fidget
    attack_ranged: Fidget
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  script_clips:
    cower: Cower
    stand: Standing
  skin: {skin}
"""
BLOCK += END + '\n'
if not s.endswith('\n'): s += '\n'
s += BLOCK
tmp = p + '.tmp_wyrde'; open(tmp, 'w').write(s); os.replace(tmp, p)
t = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
lines = open(t).read().rstrip('\n').split('\n')
lines = [l for l in lines if l.split('\t')[0] not in ('264', '265')]
lines += ['264\t380\tWyrde of the Knowing (Verdandi) (wyrd_mature.ABC = the wyrd_young mesh, wyrdmature skin, basemelee.scr): DAT WyrdeoftheKnowing in the Hall of the Gods; 3D model mm9_wyrde, tier wy_mature',
          '265\t384\tWyrde of the Unknown (Morgan) (wyrd_young.ABC, wyrdyoung skin, basemelee.scr): DAT class WyrdeoftheUnknown in the Hall of the Gods; 3D model mm9_wyrde, tier wy_young']
tmp = t + '.tmp_wyrde'; open(tmp, 'w').write('\n'.join(lines) + '\n'); os.replace(tmp, t)
print('BOUND rows 264, 265')
