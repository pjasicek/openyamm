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
# One body paint with region ramps; Apprentice has its own lower-body image (pattern differs), every tier its head colour (faces differ). Events are MM9's (EVILSORCERER.abc keys; DoFX n plays FX n of MONSTERS.txt, 0-based and only 0-2: object.lto 0x1001af90; each dots effect has one emitter on LHand1 and one on RHand1, so both palms share one effect): hAttack1 rattack 0.36 s, DoFX 1 (redyeldots) 0.36 s to its end; rAttack1 (the ranged attack and the cast) rangeAttack 0.833 s on LHand1, DoFX 2 (greenyeldots) 0.133-1.266 s; fidget2 (our Fidget) DoFX 1 0.6-1.933 s; rAttack1Lame (AttackRanged2) DoFX 1 0.114-1.657 s; Taunt DoFX 2 0.141-0.817 s; ResurrectSpell's DoFX 3 names no FX (nothing plays). FX0 bluedots is never played. No glow: MM9 has no light there.
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
      attack_melee: {{impact: 0.36, effect: {{id: mm9:redyeldots, sockets: [palm_left, palm_right], start: 0.36}}}}
      attack_ranged: {{impact: 0.833, release: palm_left, effect: {{id: mm9:greenyeldots, sockets: [palm_left, palm_right], start: 0.133, end: 1.266}}}}
      cast: {{impact: 0.833, release: palm_left, effect: {{id: mm9:greenyeldots, sockets: [palm_left, palm_right], start: 0.133, end: 1.266}}}}
      fidget: {{effect: {{id: mm9:redyeldots, sockets: [palm_left, palm_right], start: 0.6, end: 1.933}}}}
      attack_ranged2: {{effect: {{id: mm9:redyeldots, sockets: [palm_left, palm_right], start: 0.114, end: 1.657}}}}
      taunt: {{effect: {{id: mm9:greenyeldots, sockets: [palm_left, palm_right], start: 0.141, end: 0.817}}}}
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
