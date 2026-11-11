#!/usr/bin/env python3
"""Append the zombie bindings to assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock, from the repo root)."""
import os, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
if 'mm9_zombie.glb' in s:
    sys.exit('already bound')
BLOCK = """# MM9 zombie body (level_generation/creatures/mm9_zombie_claude): Meshy body and head-only model on the original ZOMBIE.abc skeleton, fitted joint for joint (15 finger bones per side,
# half-rotation helpers on hips, knees, elbows, shoulders, neck, head), MM9 clips in true handedness. MM9 has no run: Running is walk x1.5. Hattack2 hits at 0.618 s, rAttack2 RangeAttack 0.377 s
# from MM9's RangeAttack node (left hand). Tiers: shared body and head sets with ramps; the torso part has one image per tier (bare chest, vest, mail).
# ResurrectFX GreaterDemon at the pelvis as a corpse rises (Resurrect); the ResurrectSpell's DoFX 1 names FX1 (0-based), which the rows leave empty.
"""
TPL = """# {who} (row {row})
- descriptor: MM9 Zombie {t}
  model: worlds/mm9/models/mm9_zombie.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.2
    run_stride_length: 1.2
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      throw_hand: Bip01 L Finger11
      body: Bip01 Pelvis
    events:
      attack_melee: {{impact: 0.618}}
      attack_ranged: {{impact: 0.377, release: throw_hand}}
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
    ranged2: AttackRanged2
    hit2: Hit2
    taunt: Taunt
    resurrect_spell: ResurrectSpell
    resurrect: Resurrect
    wakeup: Wakeup
    death2: Death2
    wakeup2: Wakeup2
    coffin_idle: Coffin2
  skin: {skin}
"""
for who, row, t, skin in (('Rotter', 180, 'A', 'zombie_a'), ('Dripper', 181, 'B', 'zombie_b'), ('Zombie', 182, 'C', 'zombie_c')):
    BLOCK += TPL.format(who=who, row=row, t=t, skin=skin)
if not s.endswith('\n'): s += '\n'
tmp = p + '.tmp.zombie'
open(tmp, 'w').write(s + BLOCK)
os.chmod(tmp, os.stat(p).st_mode)
os.replace(tmp, p)
print('bound')
