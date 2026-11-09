#!/usr/bin/env python3
"""Bind MM9 Demon A (row 241 Lesser Demon) in assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock
claude_shared/locks/mm9_actors_yml.lock, from the repo root). Replaces an earlier block of this project."""
import os, re
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
s = re.sub(r'# >>> mm9_stage1demon_claude\n.*?# <<< mm9_stage1demon_claude\n', '', s, flags=re.S)
BLOCK = """# >>> mm9_stage1demon_claude
# MM9 Lesser Demon (level_generation/creatures/mm9_stage1demon_claude): Meshy body and head-only model on the original
# STAGE1DEMON.abc skeleton (talons rebuilt on MM9's finger chains, jaw pivot at the mouth corners, half-rotation helpers),
# all 18 MM9 clips in true handedness. Hattack1 hits at 0.341 s (Rattack); rattack1 RangeAttack 0.488 s from the mouth
# (MM9's RangeAttack node is the jaw pivot). One row, one skin. MONSTERS HeadTurn 0: no look block.
- descriptor: MM9 Demon A
  model: worlds/mm9/models/mm9_lesserdemon.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 2.39
    run_stride_length: 2.17
    upper_body_root: Bip01 Spine1
    sockets:
      mouth: Xtong
    events:
      attack_melee: {impact: 0.341}
      attack_ranged: {impact: 0.488, release: mouth}
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
    fidget2: Fidget2
    taunt: Taunt
    block: Block
    attack_melee2: AttackMelee2
    dodge_left: DodgeLeft
    dodge_right: DodgeRight
    hit2: Hit2
    backpedal: Backpedal
    backpedal_run: BackpedalRun
    clop_setup: ClopSetup
# <<< mm9_stage1demon_claude
"""
if not s.endswith('\n'): s += '\n'
tmp = p + '.tmp.stage1demon'
open(tmp, 'w').write(s + BLOCK)
os.chmod(tmp, os.stat(p).st_mode)
os.replace(tmp, p)
print('bound MM9 Demon A')
