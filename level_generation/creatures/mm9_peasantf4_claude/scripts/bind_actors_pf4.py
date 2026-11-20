#!/usr/bin/env python3
"""Append or replace the PeasantF4 bindings in assets_dev/worlds/mm9/models/actors.yml and its rows in
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root; re-reads both files inside it)."""
import os
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN = '# >>> mm9_peasantf4_claude'; END = '# <<< mm9_peasantf4_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 PeasantF4 (level_generation/creatures/mm9_peasantf4_claude): PEASANTF4.abc is PEASANTF1.abc with a longer hood falling to the
# shoulders and long bell sleeves, so the approved PeasantF1 body, rig, weights and clips (the MM9 PeasantFemale library) are reused; a new
# hood (MM9 F4's Head / xpony / Ponytail11 weights, the cape on the bodice) and sleeve tubes are added. Own 4K body paint (skin A, olive
# dress) with region ramps for skin B (rust dress, dirty apron) and a head colour per tier (two women: A about 45, B about 60). Clips MM9's
# scripts play: NPCbase.scr (Converse -> conv1-3, BaseRun LoopAnim Cower); NPC187.scr plays none. No attack clip: attacks play Fidget.
"""
for row, role, skin, label in ((30, 'Commoner', 'pf4_a', 'Peasant Human1 FemaleA B (row 30, skin PeasantF4a, DAT CommonerHumanFemaleB x5, one NPC187.scr)'),
                               (37, 'Commoner', 'pf4_a', 'Peasant Human2 FemaleA B (row 37, skin PeasantF4a, DAT CommonerHuman2FemaleB x2)'),
                               (42, 'Prisoner', 'pf4_b', 'Peasant Human2 FemaleD A (row 42, skin PeasantF4b, no DAT placement)')):
    BLOCK += f"""# {role}, {label}
- descriptor: MM9 {row} {role}
  model: worlds/mm9/models/mm9_peasantf4.glb
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
tmp = p + '.tmp_pf4'; open(tmp, 'w').write(s); os.replace(tmp, p)
t = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
lines = open(t).read().rstrip('\n').split('\n')
lines = [l for l in lines if l.split('\t')[0] not in ('30', '37', '42')]
lines += ['30\t350\tCommoner, Peasant Human1 FemaleA B (PeasantF4 body = PeasantF1 + long hood and bell sleeves, PeasantF4a skin): DAT class CommonerHumanFemaleB; 3D model mm9_peasantf4, tier pf4_a',
          '37\t377\tCommoner, Peasant Human2 FemaleA B (PeasantF4 body = PeasantF1 + long hood and bell sleeves, PeasantF4a skin): DAT class CommonerHuman2FemaleB; 3D model mm9_peasantf4, tier pf4_a',
          '42\t384\tPrisoner, Peasant Human2 FemaleD A (PeasantF4 body = PeasantF1 + long hood and bell sleeves, PeasantF4b skin): no DAT placement found in the rebuilt maps; 3D model mm9_peasantf4, tier pf4_b']
tmp = t + '.tmp_pf4'; open(tmp, 'w').write('\n'.join(lines) + '\n'); os.replace(tmp, t)
print('BOUND rows 30, 37, 42')
