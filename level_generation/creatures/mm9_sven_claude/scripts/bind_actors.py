#!/usr/bin/env python3
"""Bind Sven Svenssen (MONSTERS.txt row 249) in assets_dev/worlds/mm9/models/actors.yml and add the row to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root, then run the table generator)."""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '249': '249\t520\tSven Svenssen (Sven.abc, sven skin, NPCbase.scr, Scale 1.25): Jarl of Arslegard, DAT objects Afterworld '
           'SvenSvenssen0 (NPCbase), Arslegard SvenSvenssen0 (NPC3.scr), The Arena SvenArena (SvenArena.scr), Thronheim Sven/'
           'SvenProp on Sven_ARG.abc (ARG_Sven.scr, PropAnim Sit); legacy Dwarf A as the fallback visual; 3D model mm9_sven',
}
lines = open(TSV).read().rstrip('\n').split('\n')
have = {l.split('\t')[0] for l in lines}
for k, row in ROWS.items():
    if k not in have:
        lines.append(row)
tmp = TSV + '.tmp_sven'
open(tmp, 'w').write('\n'.join(lines) + '\n')
os.replace(tmp, TSV)

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_sven_claude', '# <<< mm9_sven_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 Sven Svenssen, Jarl of Arslegard (level_generation/creatures/mm9_sven_claude): Meshy body on SVEN.abc's skeleton (the 45-joint
# PeasantMale skeleton) with the PeasantMale library clips (stand1, walk3, run, fidget4, conv2 talk, hattack1 Rattack 0.5 s, wince1,
# die1) and the clips his scripts play: cower (NPCbase via BaseRun.inc), bless (SvenArena.scr), and from SVEN_ARG.abc (the same
# body and skin seated on a ChairPlain chair; ARG_Sven.scr / PropAnim) Sitting, Agree, Applause. Five-finger MPFB hands, mirrored
# to MM9's true handedness. One skin (SVEN), no tiers. Row 249 MONSTERS Scale 1.25.
- descriptor: MM9 249 Sven Svenssen
  model: worlds/mm9/models/mm9_sven.glb
  scale: 125.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.2
    run_stride_length: 3.1
    look: {nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}
    events:
      attack_melee: {impact: 0.5}
      attack_ranged: {impact: 0.5}
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
    bless: Bless
    sit: Sit
    sitting: Sit
    agree: Agree
    applause: Applause
    stand: Standing
"""
BLOCK += END + '\n'
tmp = p + '.tmp_sven'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
