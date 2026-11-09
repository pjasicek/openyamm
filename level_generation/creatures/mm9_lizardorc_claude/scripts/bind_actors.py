#!/usr/bin/env python3
"""Append the Lizard-Orc bindings to assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock). Args: <walk stride> <run stride>. Repo root."""
import os, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
walk, run = sys.argv[1:3]
s = open(p).read()
if 'mm9_lizardorc.glb' in s:
    sys.exit('already bound')
BLOCK = """# MM9 Lizard-Orc family (level_generation/creatures/mm9_lizardorc_claude): Meshy body and open-mouth head on LIZARDORC.abc's skeleton, true handedness, cutlass rigid on Bone07 in the right fist, jaw Box01, tongue Bone02-05, tail Box03-05, Finger1-3 chains and thumb.
# MM9 has one skin for its three rows: A is the paint, B and C ramps on the same images. Hattack1 Rattack 0.304 s, Rattack1 RangeAttack 0.5 s from MM9's RangeAttack node on the left hand. Scale from MONSTERS Scale 1.
"""
for desc, skin, label in (('MM9 Lizard-Orc A', 'liz_a', 'Lizard-Orc (row 189)'), ('MM9 Lizard-Orc B', 'liz_b', 'Lizard-Orc Warrior (row 190)'), ('MM9 Lizard-Orc C', 'liz_c', 'Lizard-Orc Mage (row 191)')):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_lizardorc.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    cast: AttackRanged
    stride_length: {walk}
    run_stride_length: {run}
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      cast_hand: Bip01 L Finger11
    events:
      attack_melee: {{impact: 0.304}}
      attack_ranged: {{impact: 0.5, release: cast_hand}}
      cast: {{impact: 0.5, release: cast_hand}}
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
    backpedal: Backpedal
    backpedal_run: BackpedalRun
    death2: Death2
  skin: {skin}
"""
tmp = p + '.tmp_lizardorc'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
