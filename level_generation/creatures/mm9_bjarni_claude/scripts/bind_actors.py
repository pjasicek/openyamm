#!/usr/bin/env python3
"""Bind Bjarni Thorvaldssen (row 246) in assets_dev/worlds/mm9/models/actors.yml and add the rows to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root, then run the table generator)."""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '246': '246\t586\tBjarni Thorvaldssen (BJARNI body and skin, PeasantMale skeleton): Jarl of Sturmford; DAT class BjarniThorvaldssen in Afterworld (NPCbase) and Thronheim City (ARG_Bjarni.scr, the Argument scene); 3D model mm9_bjarni',
}
lines = open(TSV).read().rstrip('\n').split('\n')
have = {l.split('\t')[0] for l in lines}
for k, row in ROWS.items():
    if k not in have:
        lines.append(row)
tmp = TSV + '.tmp_bj'
open(tmp, 'w').write('\n'.join(lines) + '\n')
os.replace(tmp, TSV)

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_bjarni_claude', '# <<< mm9_bjarni_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 Bjarni Thorvaldssen, Jarl of Sturmford (level_generation/creatures/mm9_bjarni_claude): Meshy body on BJARNI.abc's skeleton
# (the 45-joint PeasantMale biped, MONSTERS.txt BaseName PeasantMale) with five-finger MPFB hands, mirrored to MM9's true
# handedness. PeasantMale library clips (stand1, walk3, run, fidget4, conv2 talk, hattack1 Rattack 0.5 s, wince1, die1, cower:
# NPCbase via BaseRun.inc) and his own BJARNI.abc clips played by ARG_Bjarni.scr in Thronheim's Argument scene (loopanim Sit;
# Agree, Applause, Sc2_Bjarni1a on Shot1A, Sc2_Bjarni1c on Shake, Sc2_Bjarni2/9/15 on Speak2/9/16). One skin, no tiers.
# Bjarni Thorvaldssen (246, BJARNI.abc, BJARNI.dtx)
- descriptor: MM9 246 Bjarni Thorvaldssen
  model: worlds/mm9/models/mm9_bjarni.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.1
    run_stride_length: 2.8
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
    stand: Standing
    sit: Sit
    agree: Agree
    applause: Applause
    argument_shot1a: ArgumentShot1A
    argument_shake: ArgumentShake
    argument_speak2: ArgumentSpeak2
    argument_speak9: ArgumentSpeak9
    argument_speak16: ArgumentSpeak16
"""
BLOCK += END + '\n'
tmp = p + '.tmp_bj'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
