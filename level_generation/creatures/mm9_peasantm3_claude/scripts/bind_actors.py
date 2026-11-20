#!/usr/bin/env python3
"""Bind PeasantM3 (rows 45, 52) in assets_dev/worlds/mm9/models/actors.yml and add the rows to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root, then run the table generator)."""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '45': '45\t361\tTown, Peasant Human1 MaleB A (PeasantM3 body, PeasantM3b skin): DAT class TownHumanMaleA; 3D model mm9_peasantm3, tier pm3_b',
    '52': '52\t370\tTown, Peasant Human2 MaleB A (PeasantM3 body, PeasantM3a skin): DAT class TownHuman2MaleA; 3D model mm9_peasantm3, tier pm3_a',
}
lines = open(TSV).read().rstrip('\n').split('\n')
have = {l.split('\t')[0] for l in lines}
for k, row in ROWS.items():
    if k not in have:
        lines.append(row)
tmp = TSV + '.tmp_pm3'
open(tmp, 'w').write('\n'.join(lines) + '\n')
os.replace(tmp, TSV)

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_peasantm3_claude', '# <<< mm9_peasantm3_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 PeasantM3 human townsman (level_generation/creatures/mm9_peasantm3_claude): Meshy body on the MM9 PeasantM3/PeasantMale
# skeleton (45 joints) with the PeasantMale library clips (stand1, walk3, run, fidget4, conv2 talk, hattack1 Rattack 0.5 s, wince1,
# die1) and the one clip its scripts play (cower: NPCbase via BaseRun.inc), five-finger MPFB hands posed from MM9's mitten curl,
# mirrored to MM9's true handedness. Tiers: one body paint (PEASANTM3A) with region mask + ramps (B: brown tunic, paler neck skin)
# and one head colour per tier (two different men: A blond with a beard, B dark-haired with moustache and goatee).
"""
for desc, skin, label in (('MM9 45 Town', 'pm3_b', 'Town (45, Peasant Human1 MaleB A, PeasantM3b, DAT TownHumanMaleA)'),
                          ('MM9 52 Town', 'pm3_a', 'Town (52, Peasant Human2 MaleB A, PeasantM3a, DAT TownHuman2MaleA)')):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_peasantm3.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.1
    run_stride_length: 2.8
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 0.5}}
      attack_ranged: {{impact: 0.5}}
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
    cower: Cower
    stand: Standing
  skin: {skin}
"""
BLOCK += END + '\n'
tmp = p + '.tmp_pm3'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
