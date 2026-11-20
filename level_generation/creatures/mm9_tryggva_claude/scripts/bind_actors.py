#!/usr/bin/env python3
"""Bind Tryggva Ravenlocks (row 250) in assets_dev/worlds/mm9/models/actors.yml and add the row to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root, then run the table generator)."""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '250': '250\t607\tTryggva Ravenlocks (TRYGGVA body and skin, PeasantMale skeleton): Jarl of Frosgard; DAT class TryggvaRavenlocks in Frosgard City (NPC180.scr, sits), Thronheim City (ARG_Tryygva.scr, the Argument scene) and Afterworld (NPCbase); 3D model mm9_tryggva',
}
lines = open(TSV).read().rstrip('\n').split('\n')
have = {l.split('\t')[0] for l in lines}
for k, row in ROWS.items():
    if k not in have:
        lines.append(row)
tmp = TSV + '.tmp_try'
open(tmp, 'w').write('\n'.join(lines) + '\n')
os.replace(tmp, TSV)

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_tryggva_claude', '# <<< mm9_tryggva_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 Tryggva Ravenlocks, Jarl of Frosgard (level_generation/creatures/mm9_tryggva_claude): Meshy body on TRYGGVA.abc's skeleton
# (the 45-joint PeasantMale biped, MONSTERS.txt BaseName PeasantMale) with five-finger MPFB hands, mirrored to MM9's true
# handedness. PeasantMale library clips (stand1, walk3, run, fidget4, conv2 talk, hattack2 Rattack 0.533 s, wince1, die1, cower:
# NPCbase via BaseRun.inc) and his own TRYGGVA.abc clips: sit (NPC180.scr in Frosgard, ARG_Tryygva.scr and PropAnim Sit in
# Thronheim), Agree and Applause (the Argument scene's Agree / Clap triggers), static_die1 (PropAnim corpse props in Afterworld
# and Yorwick). One skin, no tiers.
# Tryggva Ravenlocks (250, Tryggva.abc, tryggva.dtx)
- descriptor: MM9 250 Tryggva Ravenlocks
  model: worlds/mm9/models/mm9_tryggva.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.1
    run_stride_length: 2.8
    look: {nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}
    events:
      attack_melee: {impact: 0.533}
      attack_ranged: {impact: 0.533}
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
    sit: Sit
    agree: Agree
    applause: Applause
    static_die1: DeadStatic
    dead_static: DeadStatic
"""
BLOCK += END + '\n'
tmp = p + '.tmp_try'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
