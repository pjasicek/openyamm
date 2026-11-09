#!/usr/bin/env python3
"""Append the ghoul bindings to assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock, from the repo root)."""
import os, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
if 'mm9_ghoul.glb' in s:
    sys.exit('already bound')
BLOCK = """# MM9 ghoul body (level_generation/creatures/mm9_ghoul_claude): Meshy body and head-only model on the original GHOUL.abc skeleton (its real five-finger chains, half-rotation helpers on hips, knees,
# elbows, shoulders, neck, head), MM9 clips in true handedness. Hattack1 hits at 0.426 s, rAttack1 RangeAttack 0.8 s from MM9's RangeAttack node (right hand). Tiers: shared body and head sets with ramps.
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
    events:
      attack_melee: {{impact: 0.426}}
      attack_ranged: {{impact: 0.8, release: throw_hand}}
      cast: {{impact: 0.8, release: throw_hand}}
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
for who, row, t, skin in (('Ghast', 174, 'A', 'ghoul_a'), ('Ghoul', 175, 'B', 'ghoul_b'), ('Revenant', 176, 'C', 'ghoul_c')):
    BLOCK += TPL.format(who=who, row=row, t=t, skin=skin)
if not s.endswith('\n'): s += '\n'
tmp = p + '.tmp.ghoul'
open(tmp, 'w').write(s + BLOCK)
os.chmod(tmp, os.stat(p).st_mode)
os.replace(tmp, p)
print('bound')
