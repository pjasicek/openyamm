#!/usr/bin/env python3
"""Append the trellborg bindings to assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock, from the repo root). Args: <walk stride> <run stride>"""
import os, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
if 'mm9_trellborg.glb' in s:
    sys.exit('already bound')
walk, run = sys.argv[1:3]
BLOCK = """# MM9 trellborg body (level_generation/creatures/mm9_trellborg_claude): Meshy body and head wrapped to one closed skin on the original TRELLBORG.abc skeleton, posed fists, spiked club rigid on Yclub (MM9's turn of the club in the fist solved at the wrist).
# Hattack1 hits at 0.333 s, Rattack1 releases at 0.686 s from MM9's RangeAttack node (R Hand). Tiers: three outfits, body and head colour per tier (KHR_materials_variants), club shared.
"""
TPL = """# {who} (row {row})
- descriptor: MM9 Trellborg {t}
  model: worlds/mm9/models/mm9_trellborg.glb
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
      attack_melee: {{impact: 0.333}}
      attack_ranged: {{impact: 0.686, release: cast_hand}}
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
    fidget3: Fidget3
    hit2: Hit2
    taunt: Taunt
    aware: Aware
    death2: Death2
  skin: {skin}
"""
for who, row, t, skin in (('Trellborg', 165, 'A', 'trell_a'), ('Kin Trellborg', 166, 'B', 'trell_b'), ('Ancient Trellborg', 167, 'C', 'trell_c')):
    BLOCK += TPL.format(who=who, row=row, t=t, skin=skin, walk=walk, run=run)
if not s.endswith('\n'): s += '\n'
tmp = p + '.tmp.trellborg'
open(tmp, 'w').write(s + BLOCK)
os.chmod(tmp, os.stat(p).st_mode)
os.replace(tmp, p)
print('bound')
