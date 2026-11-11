#!/usr/bin/env python3
"""Append or replace the Monk bindings in assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock, from the repo root). Args: <walk stride> <run stride>"""
import os, re, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
walk, run = sys.argv[1:3]
s = open(p).read()
BEGIN = '# >>> mm9_monk_claude'; END = '# <<< mm9_monk_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 Monk body (level_generation/creatures/mm9_monk_claude): Meshy robe and head on MONK.abc's skeleton, MM9's eight cloth chains and two cord chains keyed as MM9 keys them, 15 finger bones per side (MPFB hand), whole model mirrored to true handedness.
# One body paint with region ramps, a head colour per tier. Events are MM9's: Hattack1 Rattack 0.214 s (Lattack 0.428, Rattack 0.643, Lattack 0.965 are not carried: one impact per attack), castspell1 CastSpell 0.5 s, castspell3 0.882 s. Work and prayer clips are script clips. No hand effect and no glow, as in MM9: the castspell clips' DoFX 1 names FX1 (0-based, object.lto 0x1001af90), which the rows leave empty (FX0 bluedots never plays); MM9 has no light there.
"""
for desc, skin, label in (('MM9 Monk A', 'mk_a', 'Initiate (row 123)'), ('MM9 Monk B', 'mk_b', 'Monk (row 124)'), ('MM9 Monk C', 'mk_c', 'Reverend Monk (row 125)')):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_monk.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    cast: AttackRanged3
    stride_length: {walk}
    run_stride_length: {run}
    upper_body_root: Bip01 Spine2
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      palm_left: LHand1
      palm_right: RHand1
    events:
      attack_melee: {{impact: 0.214}}
      attack_ranged: {{impact: 0.5, release: palm_left}}
      cast: {{impact: 0.882, release: palm_left}}
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
    aware: Aware
    taunt: Taunt
    pray: Pray
    cower_start: CowerStart
    cower: Cower
    cower_end: CowerEnd
    attack_ranged2: AttackRanged2
    attack_ranged3: AttackRanged3
    hit2: Hit2
    death2: Death2
    backpedal: Backpedal
    backpedal_run: BackpedalRun
    play: Play
    hoe_wait: HoeWait
    hoe: Hoe
    hoe_fidget: HoeFidget
    sweep_wait: SweepWait
    sweep: Sweep
    sweep_fidget: SweepFidget
    hammer_wait: HammerWait
    hammer: Hammer
    hammer_fidget: HammerFidget
    wash_wait: WashWait
    wash: Wash
    wash_fidget: WashFidget
  skin: {skin}
"""
BLOCK += END + '\n'
tmp = p + '.tmp_mk'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
