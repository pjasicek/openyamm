#!/usr/bin/env python3
"""Append or replace the MM9 Skeleton bindings in assets_dev/worlds/mm9/models/actors.yml (temp + rename; run from the repo root under the flock). Args: <walk stride> <run stride>"""
import os, re, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
walk, run = sys.argv[1:3]
BEGIN, END = '# >>> mm9_skeleton_claude\n', '# <<< mm9_skeleton_claude\n'
BLOCK = BEGIN + """# MM9 Skeleton body (level_generation/creatures/mm9_skeleton_claude): Meshy skeleton of rigid bone pieces plus a skull-only model, on the original SKELETON.abc rig (joints moved onto the pieces' ends,
# 14 finger bones per side, dagger rigid on Bone01); MM9 clips un-mirrored to true handedness: dagger in the true right hand, throws from it (MM9's RangeAttack socket is on R Hand). Hattack1 Rattack 0.4 s,
# RAttack1 RangeAttack 0.38 s. Tiers: skel_a = the paint (SKELETON2), skel_r = ramps (SKELETONRED). MONSTERS.txt Scale 0.5 -> 50 for Skeletoid, Bone Thrasher, Skull Thrower. Row heights are unchanged (they still carry the
# sprite stand-in's 166): the 3D size comes from the scale alone. Skeleton L16 (row 135) alone has a ResurrectFX: GreaterDemon at
# the pelvis as it rises (resurrect).
"""
for desc, skin, scale, label in (('MM9 Skeleton C', 'skel_a', 100, 'Skeleton L16 (row 135)'), ('MM9 192 Skeleton', 'skel_a', 100, 'Skeleton L40 (row 192)'),
                                 ('MM9 Skeleton B', 'skel_a', 50, 'Bone Thrasher (row 184, Scale 0.5)'), ('MM9 Skeleton A', 'skel_r', 50, 'Skeletoid (row 183, Scale 0.5)'),
                                 ('MM9 185 Skull Thrower', 'skel_r', 50, 'Skull Thrower (row 185, Scale 0.5)')):
    # MONSTERS.txt ResurrectFX (row 135 only): MM9 plays it as a corpse rises.
    rise_socket = '\n      body: Bip01 Pelvis' if desc == 'MM9 Skeleton C' else ''
    rise_event = '\n      resurrect: {effect: {id: mm9:GreaterDemon, socket: body}}' if desc == 'MM9 Skeleton C' else ''
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_skeleton.glb
  scale: {scale}.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: {walk}
    run_stride_length: {run}
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      throw_hand: Bip01 R Hand{rise_socket}
    events:
      attack_melee: {{impact: 0.4}}
      attack_ranged: {{impact: 0.38, release: throw_hand}}{rise_event}
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
    hit2: Hit2
    fidget2: Fidget2
    fidget3: Fidget3
    taunt: Taunt
    resurrect: Resurrect
    backpedal: Backpedal
    backpedal_run: BackpedalRun
  skin: {skin}
"""
BLOCK += END
if BEGIN in s:
    s = s[:s.index(BEGIN)] + s[s.index(END) + len(END):]
if not s.endswith('\n'):
    s += '\n'
tmp = p + '.skeleton.tmp'
open(tmp, 'w').write(s + BLOCK)
os.chmod(tmp, os.stat(p).st_mode)
os.replace(tmp, p)
print('bound')
