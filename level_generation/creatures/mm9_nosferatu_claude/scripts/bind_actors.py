#!/usr/bin/env python3
"""Append or replace the Nosferatu bindings in assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock). Args: <walk stride> <run stride>"""
import os, re, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
walk, run = sys.argv[1:3]
s = open(p).read()
BEGIN = '# MM9 Nosferatu body (level_generation/creatures/mm9_nosferatu_claude)'
if BEGIN in s:
    a = s.index(BEGIN); m = re.search(r'\n# (?!Bloodsucker|Annelid|Vampir|MM9 Nosferatu body|One body paint and one head paint)', s[a:]); b = a + m.start() + 1 if m else len(s)
    s = s[:a] + s[b:]
BLOCK = BEGIN + """: Meshy body and head on NOSFERATU.abc's skeleton (bound in the masters' A pose, clips are MM9's local rotations), 15 finger bones per side from the mesh, robe on a 48-bone lattice keyed per clip from MM9's legs and tail
# One body paint and one head paint with region ramps. Events are MM9's: Hattack1 Rattack 0.333 s, RAttack1 RangeAttack 0.666 s on LHand1. DoFX n plays FX n of MONSTERS.txt (0-based, object.lto 0x1001af90): RAttack1 DoFX 1 greenyeldots on both palms 0.266-1.333 s; ResurrectSpell's DoFX 2 names no FX (nothing plays); FX0 bluedots is never played. ResurrectFX GreaterDemon at the pelvis as it rises (resurrect). No glow: MM9 has no light there.
"""
for desc, skin, label in (('MM9 Nosferatu A', 'nos_a', 'Bloodsucker (row 195)'), ('MM9 Nosferatu B', 'nos_b', 'Annelid (row 196)'), ('MM9 Nosferatu C', 'nos_c', 'Vampir (row 197)')):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_nosferatu.glb
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
      palm_left: LHand1
      palm_right: RHand1
      body: Bip01 Pelvis
    events:
      attack_melee: {{impact: 0.333}}
      attack_ranged: {{impact: 0.666, release: palm_left, effect: {{id: mm9:greenyeldots, sockets: [palm_left, palm_right], start: 0.266, end: 1.333}}}}
      cast: {{impact: 0.666, release: palm_left, effect: {{id: mm9:greenyeldots, sockets: [palm_left, palm_right], start: 0.266, end: 1.333}}}}
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
    fidget2: Fidget2
    taunt: Taunt
    resurrect_spell: ResurrectSpell
    resurrect: Resurrect
    hit2: Hit2
    dying2: Death2
    backpedal: Backpedal
    backpedal_run: BackpedalRun
  skin: {skin}
"""
tmp = p + '.tmp_nos'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
