#!/usr/bin/env python3
"""Bind Markel the Great (row 248) in assets_dev/worlds/mm9/models/actors.yml and add the row to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root, then run the table generator)."""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '248': '248\t579\tMarkel the Great (MARKEL body and skin, PeasantMale skeleton): merchant of Guberland; DAT class MarkeltheGreat in Guberland City (NPC127.scr), Afterworld (NPCbase) and Thronheim City (ARG_Markel.scr, the Argument scene); legacy Merchant C as the fallback visual; 3D model mm9_markel',
}
lines = open(TSV).read().rstrip('\n').split('\n')
have = {l.split('\t')[0] for l in lines}
for k, row in ROWS.items():
    if k not in have:
        lines.append(row)
tmp = TSV + '.tmp_mk'
open(tmp, 'w').write('\n'.join(lines) + '\n')
os.replace(tmp, TSV)

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_markel_claude', '# <<< mm9_markel_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 Markel the Great, merchant of Guberland (level_generation/creatures/mm9_markel_claude): Meshy body on MARKEL.abc's skeleton
# (the 45-joint PeasantMale biped, MONSTERS.txt BaseName PeasantMale) with five-finger MPFB hands, mirrored to MM9's true
# handedness. PeasantMale library clips (stand1, walk3, run, fidget4, conv2 talk, hattack1 Rattack 0.5 s, wince1, die1, cower:
# NPCbase via BaseRun.inc) and his own MARKEL.abc clips: NPC127.scr (Guberland) and PropAnim props loop Sit; ARG_Markel.scr in
# Thronheim's Argument scene (loopanim Sit; Applause; Sc2_MARKEL02/04/08/10/13/15 on Scene2/Speak4/8/11/13/15; Sc2_markel21 on
# Kill, then loopanim static_die2). Agree (ARG_Markel.scr) exists in neither MARKEL.abc nor the library. One skin, no tiers.
# Markel the Great (248, MARKEL.abc, MARKEL.dtx)
- descriptor: MM9 248 Markel the Great
  model: worlds/mm9/models/mm9_markel.glb
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
    walk: Walking
    sit: Sit
    applause: Applause
    sc2_markel02: Sc2_MARKEL02
    sc2_markel04: Sc2_MARKEL04
    sc2_markel08: Sc2_Markel08
    sc2_markel10: Sc2_Markel10
    sc2_markel13: Sc2_Markel13
    sc2_markel15: Sc2_Markel15
    sc2_markel21: Sc2_markel21
    static_die2: StaticDie
"""
BLOCK += END + '\n'
tmp = p + '.tmp_mk'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
