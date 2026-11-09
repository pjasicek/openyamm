#!/usr/bin/env python3
"""Append the Troglodyte bindings to assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock). Args: <walk stride> <run stride>. Repo root."""
import os, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
walk, run = sys.argv[1:3]
s = open(p).read()
if 'mm9_troglodyte.glb' in s:
    sys.exit('already bound')
BLOCK = """# MM9 Troglodyte body (level_generation/creatures/mm9_troglodyte_claude): Meshy body and open-mouth head on TROGLODYTE.abc's skeleton (bound in the mean of MM9's left and right bind directions, MM9's lengths, MM9's local rotations), three fingers on MM9's
# Finger1-3 chains (no thumb: MM9's has no vertices), half-rotation helpers on shoulders, elbows, hips, knees, tail. hattack1 Rattack 0.35 s, Rattack1 RangeAttack 0.396 s from MM9's RangeAttack node (right hand). Scale from MONSTERS Scale.
# Tiers: shared set with ramps and a rib mask (A), the paint (B), own colour and normal images for the leather (C).
"""
for desc, skin, label, sc in (('MM9 Troglodyte A', 'trog_a', 'Troglodyte (row 96)', 80.0), ('MM9 Troglodyte B', 'trog_b', 'Troglodyte Wren (row 97)', 100.0), ('MM9 Troglodyte C', 'trog_c', 'Troglodyte Gnoll (row 98)', 125.0)):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_troglodyte.glb
  scale: {sc}
  yaw_offset: -1.570796327
  animation:
    run: Running
    cast: AttackRanged
    stride_length: {walk}
    run_stride_length: {run}
    upper_body_root: Bip01 Spine1
    sockets:
      throw_hand: Bip02 R Finger21
    events:
      attack_melee: {{impact: 0.35}}
      attack_ranged: {{impact: 0.396, release: throw_hand}}
      cast: {{impact: 0.396, release: throw_hand}}
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
    search: Search
    death2: Death2
    backpedal: Backpedal
    backpedal_run: BackpedalRun
  skin: {skin}
"""
tmp = p + '.tmp_troglodyte'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
