#!/usr/bin/env python3
"""Bind PeasantM7 (rows 51, 53) in assets_dev/worlds/mm9/models/actors.yml and add the rows to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root, then run the table generator)."""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '51': '51\t368\tCommoner, Peasant Human2 MaleA B (PeasantM7 body, PeasantM7b skin): DAT class CommonerHuman2MaleB; 3D model mm9_peasantm7, tier pm7_b',
    '53': '53\t371\tTown, Peasant Human2 MaleB B (PeasantM7 body, PeasantM7a skin): DAT class TownHuman2MaleB; 3D model mm9_peasantm7, tier pm7_a',
}
lines = open(TSV).read().rstrip('\n').split('\n')
have = {l.split('\t')[0] for l in lines}
for k, row in ROWS.items():
    if k not in have:
        lines.append(row)
tmp = TSV + '.tmp_pm7'
open(tmp, 'w').write('\n'.join(lines) + '\n')
os.replace(tmp, TSV)

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_peasantm7_claude', '# <<< mm9_peasantm7_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 PeasantM7 human townsman (level_generation/creatures/mm9_peasantm7_claude): Meshy body on the MM9 PeasantM7/PeasantMale
# skeleton (45 joints) with the PeasantMale library clips (stand1, walk3, run, fidget4, conv2 talk, hattack2 Rattack 0.533 s, wince1,
# die1) and the clips its scripts play (cower: NPCbase via BaseRun.inc; conv1: NPC213/Ralof; conv4, conv5: NPC110), five-finger
# MPFB hands, mirrored to MM9's true handedness. Tiers: one body + head set, region masks and ramps (shared paint PEASANTM7B; A:
# slate-blue tunic, gold collar and hem band, auburn hair, redder breeches).
"""
for desc, skin, label in (('MM9 51 Commoner', 'pm7_b', 'Commoner (51, Peasant Human2 MaleA B, PeasantM7b, DAT CommonerHuman2MaleB)'),
                          ('MM9 53 Town', 'pm7_a', 'Town (53, Peasant Human2 MaleB B, PeasantM7a, DAT TownHuman2MaleB)')):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_peasantm7.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.1
    run_stride_length: 2.8
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 0.533}}
      attack_ranged: {{impact: 0.533}}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: AttackMelee
    attack_ranged: AttackMelee
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  script_clips:
    talk: Talk
    conv2: Talk
    conv1: Conv1
    conv4: Conv4
    conv5: Conv5
    cower: Cower
    stand: Standing
  skin: {skin}
"""
BLOCK += END + '\n'
tmp = p + '.tmp_pm7'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
