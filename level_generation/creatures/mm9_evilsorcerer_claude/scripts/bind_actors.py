#!/usr/bin/env python3
"""Append or replace the Evil Sorcerer bindings in assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock). Args: <walk stride> <run stride>"""
import os, re, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
walk, run = sys.argv[1:3]
s = open(p).read()
BEGIN = '# MM9 Evil Sorcerer body (level_generation/creatures/mm9_evilsorcerer_claude)'
if BEGIN in s:
    a = s.index(BEGIN); m = re.search(r'\n# (?!Evil |MM9 Evil Sorcerer body)[^\n]*\n- descriptor:', s[a:]); b = a + m.start() + 1 if m else len(s)
    s = s[:a] + s[b:]
BLOCK = BEGIN + """: Meshy body and head on EVILSORCERER.abc's skeleton (bound in the masters' A pose, clips are MM9's local rotations), 15 finger bones per side from the mesh, four-link front and back panels keyed per clip, whole model mirrored to true handedness.
# One body paint with region ramps; Apprentice has its own lower-body image (pattern differs), every tier its head colour (faces differ). Events are MM9's: hAttack1 rattack 0.36 s (DoFX bluedots), rAttack1 rangeAttack 0.833 s on LHand1 (DoFX redyeldots from 0.13 s).
"""
for desc, skin, label in (('MM9 Evil Sorcerer A', 'es_a', 'Evil Apprentice (row 156)'), ('MM9 Evil Sorcerer B', 'es_b', 'Evil Sorcerer (row 157)'), ('MM9 Evil Sorcerer C', 'es_c', 'Evil Grand Sorcerer (row 158)')):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_evilsorcerer.glb
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
    events:
      attack_melee: {{impact: 0.36, glow: [palm_left, palm_right], color: [90, 140, 255]}}
      attack_ranged: {{impact: 0.833, glow: [palm_left, palm_right], release: palm_left}}
      cast: {{impact: 0.833, glow: [palm_left, palm_right], release: palm_left}}
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
    fidget3: Fidget3
    taunt: Taunt
    attack_ranged2: AttackRanged2
    resurrect_spell: ResurrectSpell
    hit2: Hit2
    death2: Death2
    backpedal: Backpedal
    backpedal_run: BackpedalRun
  skin: {skin}
"""
tmp = p + '.tmp_es'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
