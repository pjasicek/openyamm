#!/usr/bin/env python3
"""Append or replace the PeasantF3 bindings in assets_dev/worlds/mm9/models/actors.yml and its rows in
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root; re-reads both files inside it)."""
import os
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN = '# >>> mm9_peasantf3_claude'; END = '# <<< mm9_peasantf3_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 PeasantF3 (level_generation/creatures/mm9_peasantf3_claude): PEASANTF3.abc is PEASANTF1.abc with a long veil down the back and two
# braids, so the approved PeasantF1 body, rig, weights and clips (the MM9 PeasantFemale library) are reused; veil and braids are added
# (MM9's Ponytail and xpony chains). Own 4K body paint (skin A, blue dress) with region ramps for skin B (brown dress, dirty apron) and a
# head colour per tier (two women: A blonde, B dark-haired). Clips MM9's scripts play: NPCbase.scr (Converse -> conv1-3, BaseRun LoopAnim
# Cower); Shopkeeper.scr, retainer.scr, NPC181.scr and NPC182.scr play none. No attack clip in the library: attacks play Fidget.
"""
for row, role, skin, label in ((35, 'Prisoner', 'pf3_b', 'Peasant Human1 FemaleD A (row 35, skin PeasantF3b, no DAT placement)'),
                               (40, 'Shopkeeper', 'pf3_a', 'Peasant Human2 FemaleC A (row 40, skin PeasantF3a, DAT ShopkeeperHuman2FemaleA)')):
    BLOCK += f"""# {role}, {label}
- descriptor: MM9 {row} {role}
  model: worlds/mm9/models/mm9_peasantf3.glb
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
tmp = p + '.tmp_pf3'; open(tmp, 'w').write(s); os.replace(tmp, p)
t = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
lines = open(t).read().rstrip('\n').split('\n')
lines = [l for l in lines if l.split('\t')[0] not in ('35', '40')]
lines += ['35\t357\tPrisoner, Peasant Human1 FemaleD A (PeasantF3 body = PeasantF1 + veil and braids, PeasantF3b skin): no DAT placement found in the rebuilt maps; 3D model mm9_peasantf3, tier pf3_b',
          '40\t382\tShopkeeper, Peasant Human2 FemaleC A (PeasantF3 body = PeasantF1 + veil and braids, PeasantF3a skin): DAT class ShopkeeperHuman2FemaleA; 3D model mm9_peasantf3, tier pf3_a']
tmp = t + '.tmp_pf3'; open(tmp, 'w').write('\n'.join(lines) + '\n'); os.replace(tmp, t)
print('BOUND rows 35, 40')
