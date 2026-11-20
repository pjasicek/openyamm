#!/usr/bin/env python3
"""Append or replace the PeasantF1 bindings in assets_dev/worlds/mm9/models/actors.yml and its rows in
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root; re-reads both files inside it)."""
import os
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN = '# >>> mm9_peasantf1_claude'; END = '# <<< mm9_peasantf1_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 PeasantF1 body (level_generation/creatures/mm9_peasantf1_claude): the older human townswoman in a hood. Meshy body on PEASANTF1.abc's human
# female skeleton (73 joints, skirt chains keyed as MM9 keys them, MPFB female arms with 15 finger bones per side), the MM9 PeasantFemale clip
# library, whole model mirrored to true handedness. One body paint with region ramps (bodice, skirt, tier-A gold embroidery), a head + hood colour
# per tier (the two skins are two women with differently coloured hoods). Clips MM9's scripts play: NPCbase.scr (Converse -> conv1-3, BaseRun
# LoopAnim Cower); retainer.scr, shopkeeper.scr, BankOrb.scr and NPC244.scr play none. No attack clip in the library: attacks play Fidget.
"""
for row, role, skin, label in ((29, 'Commoner', 'pf1_b', 'Peasant Human1 FemaleA A (row 29, skin PeasantF1b, DAT CommonerHumanFemaleA)'),
                               (33, 'Shopkeeper', 'pf1_a', 'Peasant Human1 FemaleC A (row 33, skin PeasantF1a, DAT ShopkeeperHumanFemaleA)')):
    BLOCK += f"""# {role}, {label}
- descriptor: MM9 {row} {role}
  model: worlds/mm9/models/mm9_peasantf1.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.0
    run_stride_length: 1.6
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
    talk: Talk
    cower: Cower
    conv1: Conv1
    conv2: Talk
    conv3: Conv3
    stand: Standing
  skin: {skin}
"""
BLOCK += END + '\n'
if not s.endswith('\n'): s += '\n'
s += BLOCK
tmp = p + '.tmp_pf1'; open(tmp, 'w').write(s); os.replace(tmp, p)
# descriptor rows
t = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
lines = open(t).read().rstrip('\n').split('\n')
lines = [l for l in lines if l.split('\t')[0] not in ('29', '33')]
lines += ['29\t349\tCommoner, Peasant Human1 FemaleA A (PeasantF1 body, PeasantF1b skin): DAT class CommonerHumanFemaleA; 3D model mm9_peasantf1, tier pf1_b',
          '33\t355\tShopkeeper, Peasant Human1 FemaleC A (PeasantF1 body, PeasantF1a skin): DAT class ShopkeeperHumanFemaleA; 3D model mm9_peasantf1, tier pf1_a']
tmp = t + '.tmp_pf1'; open(tmp, 'w').write('\n'.join(lines) + '\n'); os.replace(tmp, t)
print('BOUND rows 29, 33')
