#!/usr/bin/env python3
"""Append the gezzampt bindings to assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock, from the repo root). Args: <walk stride> <run stride>"""
import os, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
if 'mm9_gezzampt.glb' in s:
    sys.exit('already bound')
walk, run = sys.argv[1:3]
BLOCK = """# MM9 gezzampt body (level_generation/creatures/mm9_gezzampt_claude): Meshy body and head wrapped to one closed skin on the original GEZZAMPT.abc skeleton, joints translated (half-rotation helpers), closed five-finger fists, MM9 clips in true handedness.
# Hattack1 and Hattack2 hit at 0.389 s (Rattack); Rattack1 casts lightning at 0.389 s from MM9's RangeAttack node (R Hand). Tiers: one shared set + region mask + ramps fitted to MM9's three skins.
"""
TPL = """# {who} (row {row})
- descriptor: MM9 Gezzampt {t}
  model: worlds/mm9/models/mm9_gezzampt.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: {walk}
    run_stride_length: {run}
    upper_body_root: Bip01 Spine2
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      cast_hand: Bip01 R Hand
    events:
      attack_melee: {{impact: 0.389}}
      attack_ranged: {{impact: 0.389, release: cast_hand}}
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
    aware: Aware
    death2: Death2
    backpedal: Backpedal
    backpedal_run: BackpedalRun
  skin: {skin}
"""
for who, row, t, skin in (('Gezzamptling', 171, 'A', 'gezz_a'), ('Gezzampt', 172, 'B', 'gezz_b'), ('Gezzampt Elder', 173, 'C', 'gezz_c')):
    BLOCK += TPL.format(who=who, row=row, t=t, skin=skin, walk=walk, run=run)
if not s.endswith('\n'): s += '\n'
tmp = p + '.tmp.gezzampt'
open(tmp, 'w').write(s + BLOCK)
os.chmod(tmp, os.stat(p).st_mode)
os.replace(tmp, p)
print('bound')
