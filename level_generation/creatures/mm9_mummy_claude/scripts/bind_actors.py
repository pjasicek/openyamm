#!/usr/bin/env python3
"""Append the Mummy bindings to assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock). Args: <walk stride> <run stride>"""
import os, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
walk, run = sys.argv[1:3]
s = open(p).read()
if 'mm9_mummy.glb' in s:
    sys.exit('already bound')
BLOCK = """# MM9 Mummy body (level_generation/creatures/mm9_mummy_claude): symmetric Meshy body and head on MUMMY.abc's skeleton (bound in the masters' A pose, clips are MM9's local rotations), five-finger
# wrapped hands (15 bones per side), the long band as a rope solve on Bone04-08; MM9 clips, whole model mirrored to true handedness (band on the right forearm). Hattack1 Rattack 0.333 s, Rattack1 RangeAttack 0.333 s.
# Tiers carry their own colour and normal images: they differ in pattern and face (README, deviation). ResurrectFX GreaterDemon at
# the pelvis as a corpse rises (Resurrect). No glow: MM9 has no light there.
"""
for desc, skin, label in (('MM9 Mummy A', 'mummy_a', 'Canopic Mummy (row 144)'), ('MM9 Mummy B', 'mummy_b', 'Embalmed Mummy (row 145)'), ('MM9 Mummy C', 'mummy_c', 'Petrified Mummy (row 146)')):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_mummy.glb
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
      cast_hand: Bip01 R Hand
      body: Bip01 Pelvis
    events:
      attack_melee: {{impact: 0.333}}
      attack_ranged: {{impact: 0.333, release: cast_hand}}
      cast: {{impact: 0.333, release: cast_hand}}
      resurrect: {{effect: {{id: mm9:GreaterDemon, socket: body}}}}
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
    resurrect_spell: ResurrectSpell
    resurrect: Resurrect
    coffin: Coffin
    wakeup: Wakeup
    wakeup2: Wakeup2
    coffin2: Coffin2
    death2: Death2
    dead2: Dead2
    backpedal: Backpedal
    backpedal_run: BackpedalRun
  skin: {skin}
"""
tmp = p + '.tmp_mummy'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
