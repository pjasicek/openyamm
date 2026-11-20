#!/usr/bin/env python3
"""Append the ghoul bindings to assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock, from the repo root)."""
import os, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
if 'mm9_ghoul.glb' in s:
    sys.exit('already bound')
BLOCK = """# MM9 ghoul body (level_generation/creatures/mm9_ghoul_claude): Meshy body and head-only model on the original GHOUL.abc skeleton (its real five-finger chains, half-rotation helpers on hips, knees,
# elbows, shoulders, neck, head), MM9 clips in true handedness. Hattack1 hits at 0.426 s, rAttack1 RangeAttack 0.8 s from MM9's RangeAttack node (right hand). Tiers: shared body and head sets with ramps.
# MM9's hand effects on both hands (LHand1/RHand1 are on Bip01 L/R Hand; DoFX n plays FX n of MONSTERS.txt, 0-based, object.lto 0x1001af90): rAttack1 DoFX 0 0.2-1.466 s (Ghast bluedots,
# Ghoul and Revenant greenyeldots); ResurrectSpell DoFX 0 from 0.033 s, then DoFX 1 at 0.567 s (the Ghast's redyeldots replaces its bluedots; the others have no FX1), EndFX 1.733 s.
"""
TPL = """# {who} (row {row})
- descriptor: MM9 Ghoul {t}
  model: worlds/mm9/models/mm9_ghoul.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.85
    run_stride_length: 2.75
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    cast: AttackRanged
    sockets:
      throw_hand: Bip01 R Finger11
      palm_left: Bip01 L Hand
      palm_right: Bip01 R Hand
    events:
      attack_melee: {{impact: 0.426}}
      attack_ranged: {{impact: 0.8, release: throw_hand, effect: {{id: mm9:{fx0}, sockets: [palm_left, palm_right], start: 0.2, end: 1.466}}}}
      cast: {{impact: 0.8, release: throw_hand, effect: {{id: mm9:{fx0}, sockets: [palm_left, palm_right], start: 0.2, end: 1.466}}}}
      resurrect_spell: {resurrect_spell}
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
    hit2: Hit2
    dying2: Death2
    taunt: Taunt
    resurrect_spell: ResurrectSpell
    backpedal: Backpedal
    backpedal_run: BackpedalRun
  skin: {skin}
"""
# MONSTERS.txt FX0 and the ResurrectSpell effects per row (the Ghast's FX1 redyeldots replaces its FX0 at the second DoFX).
GHAST_RESURRECT = ('{effects: [{id: mm9:bluedots, sockets: [palm_left, palm_right], start: 0.033, end: 0.567}, '
                   '{id: mm9:redyeldots, sockets: [palm_left, palm_right], start: 0.567, end: 1.733}]}')
GREEN_RESURRECT = '{effect: {id: mm9:greenyeldots, sockets: [palm_left, palm_right], start: 0.033, end: 1.733}}'
for who, row, t, skin, fx0, resurrect_spell in (('Ghast', 174, 'A', 'ghoul_a', 'bluedots', GHAST_RESURRECT),
                                                ('Ghoul', 175, 'B', 'ghoul_b', 'greenyeldots', GREEN_RESURRECT),
                                                ('Revenant', 176, 'C', 'ghoul_c', 'greenyeldots', GREEN_RESURRECT)):
    BLOCK += TPL.format(who=who, row=row, t=t, skin=skin, fx0=fx0, resurrect_spell=resurrect_spell)
if not s.endswith('\n'): s += '\n'
tmp = p + '.tmp.ghoul'
open(tmp, 'w').write(s + BLOCK)
os.chmod(tmp, os.stat(p).st_mode)
os.replace(tmp, p)
print('bound')
