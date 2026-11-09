#!/usr/bin/env python3
"""Append the Colloidal Warrior bindings to assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock
claude_shared/locks/mm9_actors_yml.lock from the repo root; re-reads the file inside the lock). Args: <walk stride> <run stride>"""
import os, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
if 'mm9_colloidalwarrior.glb' in s: sys.exit('already bound')
walk, run = sys.argv[1:3]
BLOCK = """# MM9 colloidal warrior body (level_generation/creatures/mm9_colloidalwarrior_claude): Meshy body and head-only head on the original
# COLLOIDALWARRIOR.abc skeleton, MPFB hands on 15 finger bones copying MM9's own Finger0-42 curls, MM9 clips in true handedness.
# Hattack1 hits at 0.489 s (Rattack), Hattack2 at 0.483 s; Rattack1 throws at 1.333 s from MM9's RangeAttack hand (right).
# Tiers: one shared set + region mask + ramps (body and head sets). Scale = 100 x MONSTERS Scale (1.5 / 1.75 / 2).
"""
TPL = """# {who} (row {row})
- descriptor: MM9 Colloidal {t}
  model: worlds/mm9/models/mm9_colloidalwarrior.glb
  scale: {scale}
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: {walk}
    run_stride_length: {run}
    upper_body_root: Bip01 Spine2
    look: {{nodes: [Bip01 Head], max_yaw_degrees: 50, max_pitch_degrees: 30}}
    sockets:
      cast_hand: Bip01 R Hand
    events:
      attack_melee: {{impact: 0.489}}
      attack_ranged: {{impact: 1.333, release: cast_hand}}
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
    fidget2: Fidget2
    hit2: Hit2
    taunt: Taunt
    death2: Death2
    backpedal: Backpedal
    backpedal_run: BackpedalRun
  skin: {skin}
"""
for who, row, t, skin, scale in (('Colloidal Soldier', 9234, 'A', 'cw_a', '150.0'), ('Colloidal Warrior', 9235, 'B', 'cw_b', '175.0'), ('Colloidal Guardian', 9236, 'C', 'cw_c', '200.0')):
    BLOCK += TPL.format(who=who, row=row, t=t, skin=skin, walk=walk, run=run, scale=scale)
if not s.endswith('\n'): s += '\n'
tmp = p + '.tmp.colloidal'
open(tmp, 'w').write(s + BLOCK); os.chmod(tmp, os.stat(p).st_mode); os.replace(tmp, p); print('bound')
