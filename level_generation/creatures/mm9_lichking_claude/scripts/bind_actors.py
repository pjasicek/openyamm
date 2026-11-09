#!/usr/bin/env python3
"""Append or replace the Lich King binding in assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root). Args: <walk stride> <run stride>"""
import os, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
walk, run = sys.argv[1:3]
s = open(p).read()
BEGIN, END = '# >>> mm9_lichking_claude\n', '# <<< mm9_lichking_claude\n'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END, a) + len(END); s = s[:a] + s[b:]
BLOCK = BEGIN + f"""# MM9 Lich King (level_generation/creatures/mm9_lichking_claude): Meshy body on LICHKING.abc's own skeleton (no left Hand bone: L Finger0 is
# the left wrist), MM9's 19 clips resampled, the approved Lich's skull inside a Meshy crown-helm, five-finger gauntlets from the mesh, the right
# fist closed on a staff rigid on MM9's staff bone Bone01, coat on seven two-link hinge sectors and the tabard on four links keyed per clip.
# Row 209 Lich King L65 (LICHKING1), one tier by region mask and ramps; eyes glow red. Scale 135 = 100 x MONSTERS.txt Scale 1.35.
# Events are MM9's: Hattack1 Rattack 0.479 s; Rattack1 RangeAttack 0.474 s on Lhand1 (DoFX 1 from 0.105 s). u1 is MM9's staff socket.
- descriptor: MM9 209 Lich King
  model: worlds/mm9/models/mm9_lichking.glb
  scale: 135.0
  yaw_offset: -1.570796327
  animation:
    cast: AttackRanged
    run: Running
    stride_length: {walk}
    run_stride_length: {run}
    gait_rate: [0.7, 1.4]
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      palm_left: LHand1
      palm_right: RHand1
      staff_head: u1
    events:
      attack_melee: {{impact: 0.479}}
      attack_ranged: {{impact: 0.474, glow: [palm_left, staff_head], release: palm_left}}
      cast: {{impact: 0.474, glow: [palm_left, staff_head], release: palm_left}}
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
    fidget2: Fidget2
    search: Search
    aware: Aware
    taunt: Taunt
    resurrect_spell: ResurrectSpell
    resurrect: Resurrect
    hit2: Hit2
    death2: Death2
    dead2: Dead2
    death3: Death3
    backpedal: Backpedal
    backpedal_run: BackpedalRun
  skin: lichking
""" + END
s = s.rstrip('\n') + '\n' + BLOCK
tmp = p + '.lichking.tmp'; open(tmp, 'w').write(s); os.replace(tmp, p)
print('BOUND MM9 209 Lich King', walk, run)
