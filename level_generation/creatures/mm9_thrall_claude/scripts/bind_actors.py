#!/usr/bin/env python3
"""Append the thrall bindings to assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock, from the repo root). Args: <walk stride> <run stride>"""
import os, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
if 'mm9_thrall.glb' in s:
    sys.exit('already bound')
walk, run = sys.argv[1:3]
BLOCK = """# MM9 thrall body (level_generation/creatures/mm9_thrall_claude): Meshy body and head-only model on the original THRALL.abc skeleton, joints translated (15 finger bones per side,
# half-rotation helpers, eight skirt hinges keyed so the thighs stay under the cloth), MM9 clips in true handedness. hattack1 hits at 0.733 s; Rattack1 throws its knife at 0.688 s from MM9's RangeAttack node (right hand).
# Tiers: limbs shared with ramps; torso + skirt and head have one image per tier (tunic, half pelt, bare chest; old bald man, headband, dark hair).
"""
TPL = """# {who} (row {row})
- descriptor: MM9 Thrall {t}
  model: worlds/mm9/models/mm9_thrall.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: {walk}
    run_stride_length: {run}
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      throw_hand: Bip01 R Finger1
    events:
      attack_melee: {{impact: 0.733}}
      attack_ranged: {{impact: 0.688, release: throw_hand}}
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
    attack3: AttackMelee3
    fidget2: Fidget2
    hit2: Hit2
    taunt: Taunt
    death2: Death2
  skin: {skin}
"""
for who, row, t, skin in (('Field Thrall', 90, 'A', 'thrall_a'), ('Thrall', 91, 'B', 'thrall_b'), ('Thrall Master', 92, 'C', 'thrall_c')):
    BLOCK += TPL.format(who=who, row=row, t=t, skin=skin, walk=walk, run=run)
if not s.endswith('\n'): s += '\n'
tmp = p + '.tmp.thrall'
open(tmp, 'w').write(s + BLOCK)
os.chmod(tmp, os.stat(p).st_mode)
os.replace(tmp, p)
print('bound')
