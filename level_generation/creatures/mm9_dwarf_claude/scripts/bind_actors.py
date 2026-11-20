#!/usr/bin/env python3
"""Write the dwarves' three descriptors into assets_dev/worlds/mm9/models/actors.yml. Run under the shared flock from the repo root:
flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <this>  (temp + rename: the file is hard-linked)."""
import os, re, sys, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm9/models/actors.yml')
STRIDE, RUN = sys.argv[1], sys.argv[2]
HEAD = '''# >>> mm9_dwarf_claude
# MM9 Dwarf (level_generation/creatures/mm9_dwarf_claude): Meshy body and head-only model on the original DWARF.abc skeleton with its 16 clips, true handedness: throwing axe in the right fist, rigid on MM9's RHand1. Rows: Dwarven Guard L10, Soldier L20,
# Commander L30; MM9 has one skin, tiers here are ramps. WAttack1 Rattack 0.5 s. Rattack1 Rangeattack 0.5 s from the fist; RHand1's scale hides the axe until the clip's end.
'''
TAIL = '# <<< mm9_dwarf_claude\n'
ENTRY = '''# {comment}
- descriptor: MM9 Dwarf {k}
  model: worlds/mm9/models/mm9_dwarf.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: {stride}
    run_stride_length: {run}
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      axe: RHand1
    events:
      attack_melee: {{impact: 0.5}}
      attack_ranged: {{impact: 0.5, release: axe}}
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
    hit2: Hit2
    taunt: Taunt
    search: Search
    aware: Aware
    dying2: Death2
  skin: dwarf_{low}
'''
block = HEAD + ''.join(ENTRY.format(comment=c, k=k, low=k.lower(), stride=STRIDE, run=RUN) for c, k in (('Dwarven Guard (row 120)', 'A'), ('Dwarven Soldier (row 121)', 'B'), ('Dwarven Commander (row 122)', 'C'))) + TAIL
s = A.read_text()
s = re.sub(r'# >>> mm9_dwarf_claude\n.*?# <<< mm9_dwarf_claude\n', '', s, flags=re.S)
if not s.endswith('\n'): s += '\n'
s += block
fd, tmp = tempfile.mkstemp(dir=A.parent, prefix='.actors_', suffix='.yml')
with os.fdopen(fd, 'w') as f: f.write(s)
os.chmod(tmp, 0o644); os.replace(tmp, A)
print('BOUND', len(s.splitlines()))
