#!/usr/bin/env python3
"""Append the Bigfoot bindings to assets_dev/worlds/mm9/models/actors.yml (temp + rename; under the flock, from the repo root). Args: <walk stride> <run stride>"""
import os, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
if 'mm9_bigfoot.glb' in s: sys.exit('already bound')
walk, run = sys.argv[1:3]
BLOCK = """# MM9 bigfoot body (level_generation/creatures/mm9_bigfoot_claude): Meshy body and head on the original BIGFOOT.abc skeleton, 15 finger bones on MPFB ape hands, MM9 clips in true handedness.
# Hattack1 hits at 0.456 s (Lattack), Hattack2 at 0.566 s (Rattack); Rattack1 throws at 0.566 s from MM9's RangeAttack node (R Hand). Tiers: one shared set + region mask + ramps, the Yeti's head its own image.
"""
TPL = """# {who} (row {row})
- descriptor: MM9 Bigfoot {t}
  model: worlds/mm9/models/mm9_bigfoot.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: {walk}
    run_stride_length: {run}
    upper_body_root: Bip01 Spine2
    look: {{nodes: [Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      cast_hand: Bip01 R Hand
    events:
      attack_melee: {{impact: 0.456}}
      attack_ranged: {{impact: 0.566, release: cast_hand}}
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
    walk_fidget: WalkFidget
    backpedal: Backpedal
    backpedal_run: BackpedalRun
    jumping_down: JumpingDown
    lying_down: LyingDown
  skin: {skin}
"""
for who, row, t, skin in (('Bigfoot', 198, 'A', 'bf_a'), ('Sasquatch', 199, 'B', 'bf_b'), ('Yeti', 200, 'C', 'bf_c')):
    BLOCK += TPL.format(who=who, row=row, t=t, skin=skin, walk=walk, run=run)
if not s.endswith('\n'): s += '\n'
tmp = p + '.tmp.bigfoot'
open(tmp, 'w').write(s + BLOCK); os.chmod(tmp, os.stat(p).st_mode); os.replace(tmp, p); print('bound')
