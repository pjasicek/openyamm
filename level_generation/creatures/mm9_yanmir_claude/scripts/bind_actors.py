#!/usr/bin/env python3
"""Bind MM9 row 206 Yanmir in assets_dev/worlds/mm9/models/actors.yml (temp + rename; run from the repo root under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, re-reading the file inside it). Replaces an older block of
this project (between the markers). Args: <walk stride> <run stride>"""
import os, re, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
walk, run = sys.argv[1:3]
BEGIN, END = '# >>> mm9_yanmir_claude\n', '# <<< mm9_yanmir_claude\n'
BLOCK = BEGIN + f"""# MM9 Yanmir body (level_generation/creatures/mm9_yanmir_claude): Meshy body and head on the original YANMIR.abc skeleton at 0.3 x size
# (scale 333.333 restores MM9's 9.6 m), rest frames turned onto our limbs (MM9's bind is a stride), MPFB hands, MM9 clips in true handedness.
# HAttack1 stomps at 0.603 s (lkick); Rattack1 casts at 0.405 s from MM9's RangeAttack node (Ystafftop, the staff's head). Staff rigid on
# Ystaff in the right fist; crown rigid on Head. Death/Death2 are MM9's Giant die1/die2 retargeted (Yanmir's own Die ends standing: script clip).
- descriptor: MM9 206 Yanmir
  model: worlds/mm9/models/mm9_yanmir.glb
  scale: 333.333
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: {walk}
    run_stride_length: {run}
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      cast_hand: Ystafftop
    events:
      attack_melee: {{impact: 0.603}}
      attack_ranged: {{impact: 0.405, release: cast_hand}}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: AttackMelee
    attack_ranged: AttackRanged
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  script_clips:
    attack2: AttackMelee2
    attack3: StepOn
    ranged2: AttackRanged2
    fidget2: Fidget2
    taunt: Taunt
    wipe: Wipe
    kick_door: KickDoor
    hit2: Hit2
    death2: Death2
    start_die: StartDie
    fall: Fall
    die_standing: Die
    attack_save: AttackMeleeSave
    ranged_old: AttackRangedOld
""" + END
if BEGIN in s:
    s = s[:s.index(BEGIN)] + BLOCK + s[s.index(END) + len(END):]
else:
    if not s.endswith('\n'): s += '\n'
    s += BLOCK
tmp = p + '.tmp.yanmir'
open(tmp, 'w').write(s); os.chmod(tmp, os.stat(p).st_mode); os.replace(tmp, p); print('bound')
