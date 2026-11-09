#!/usr/bin/env python3
"""Append the Giant bindings to assets_dev/worlds/mm9/models/actors.yml (temp + rename; under the flock, from the repo root).
Replaces an existing giant block if one is there. Args: <walk stride> <run stride>"""
import os, re, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
walk, run = sys.argv[1:3]
MARK = '# MM9 giant body (level_generation/creatures/mm9_giant_claude)'
if MARK in s:                                   # drop the old block: from the marker to the next top-level comment of another body
    a = s.index(MARK)
    m = re.search(r'\n# (?!Plain Giant|Forest Giant|Hattack1|Tiers)', s[a + 1:])
    b = a + 1 + m.start() + 1 if m else len(s)
    s = s[:a] + s[b:]
BLOCK = MARK + """: Meshy body and head on the original GIANT.abc skeleton at 0.3 x size (scale 333.333 restores MM9's 8.5 m), MPFB hands, MM9 clips in true handedness.
# Hattack1 hits at 0.472 s (rattack); Rattack1 casts at 0.6 s from MM9's RangeAttack node (Bip01 L Finger11, left hand). Mallet rigid on MM9's Xhammer, right fist closed round it.
# Tiers: one shared body set + region mask + ramps; the heads are per-tier images (red braids and headband / loose dark hair and earrings).
"""
TPL = """# {who} (row {row})
- descriptor: MM9 Giant {t}
  model: worlds/mm9/models/mm9_giant.glb
  scale: 333.333
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: {walk}
    run_stride_length: {run}
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      cast_hand: Bip01 L Finger11
    events:
      attack_melee: {{impact: 0.472}}
      attack_ranged: {{impact: 0.6, release: cast_hand}}
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
    taunt: Taunt
    aware: Aware
    hit2: Hit2
    death2: Death2
  skin: {skin}
"""
for who, row, t, skin in (('Plain Giant', 204, 'A', 'gi_a'), ('Forest Giant', 205, 'B', 'gi_b')):
    BLOCK += TPL.format(who=who, row=row, t=t, skin=skin, walk=walk, run=run)
if not s.endswith('\n'): s += '\n'
tmp = p + '.tmp.giant'
open(tmp, 'w').write(s + BLOCK); os.chmod(tmp, os.stat(p).st_mode); os.replace(tmp, p); print('bound')
