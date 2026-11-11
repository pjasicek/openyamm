#!/usr/bin/env python3
"""Append the Skeleton Warrior bindings to assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock)."""
import os, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
if 'mm9_skelwar.glb' in s:
    sys.exit('already bound')
BLOCK = """# MM9 Skeleton Warrior body (level_generation/creatures/mm9_skeletonwarrior_claude): Meshy armoured skeleton of rigid pieces plus a
# skull-only model, on the original SKELETONWARRIOR.abc skeleton (joints moved onto the pieces' ends, 15 finger bones per side,
# scimitar rigid on Bone01); MM9 clips un-mirrored to their true handedness (MM9 ABC conversions are mirror images: the scimitar
# is in the anatomical right hand, the throw from the left, MM9's LHand1 socket). Hattack1 Rattack 0.339 s, RAttack1 RangeAttack
# 0.402 s. Tiers: Warrior ramps (black mail, amber eyes, SKELETONWAR2), Master = the paint itself (SKELETONWAR1).
# ResurrectFX GreaterDemon at the pelvis as a corpse rises (Resurrect). The Master's ResurrectSpell DoFX 0 (bluedots, 0.2-1.066 s)
# is not bound: fidget2 plays the same clip here (MM9's fidget2 has its motion without the key), and clip events follow the clip.
"""
for desc, skin, label in (('MM9 Skeleton Warrior A', 'skelwar_b', 'Skeleton Warrior (row 136)'),
                          ('MM9 Skeleton Warrior B', 'skelwar_c', 'Skeleton Master (row 137)')):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_skelwar.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.68
    run_stride_length: 3.4
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      throw_hand: LHand1
      body: Bip01 Pelvis
    events:
      attack_melee: {{impact: 0.339}}
      attack_ranged: {{impact: 0.402, release: throw_hand}}
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
    taunt: Taunt
    resurrect_spell: ResurrectSpell
    resurrect: Resurrect
    search: Search
    fidget2: ResurrectSpell
    attack_melee_old: AttackMeleeOld
    attack_ranged_old: AttackRangedOld
    hit2: Hit2
    death2: Death2
    dead2: Dead2
    backpedal: Backpedal
    backpedal_run: BackpedalRun
  skin: {skin}
"""
if not s.endswith('\n'):
    s += '\n'
tmp = p + '.skelwar.tmp'
open(tmp, 'w').write(s + BLOCK)
os.chmod(tmp, os.stat(p).st_mode)
os.replace(tmp, p)
print('bound')
