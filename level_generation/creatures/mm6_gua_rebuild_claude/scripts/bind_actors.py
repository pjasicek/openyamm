#!/usr/bin/env python3
"""Write the guards' three descriptors into assets_dev/worlds/mm9/models/actors.yml. Run under the shared flock from the repo root:
flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <this>  (temp + rename: the file is hard-linked)."""
import os, re, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm9/models/actors.yml')
HEAD = '''# >>> mm9_guard_claude
# MM9 Guard family (level_generation/creatures/mm9_guard_claude): Meshy body on the original GUARD.abc skeleton, MM9 clips un-mirrored to their true handedness (halberd in the anatomical
# right hand), grafted five-finger gloves, tunic skirt on six hinge bones keyed clear of the thighs. Rows: Guard L11 (GUARD1), Guard Segeant L19 (GUARD2), Guard Captain L33 (GUARD3); the tiers
# differ in pattern, so each has its own colour, normal and ORM images (variants). Rattack: Hattack1 0.456 s, Hattack2 0.497 s. Halberd is an attachment on Xbase: the floor pass must not see its butt.
'''
TAIL = '# <<< mm9_guard_claude\n'
ENTRY = '''# {comment}
- descriptor: MM9 Guard {k}
  model: worlds/mm9/models/mm9_guard.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.3
    run_stride_length: 3.4
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 0.456}}
      attack_ranged: {{impact: 0.497}}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: AttackMelee
    attack_ranged: AttackMelee2
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  script_clips:
    fidget2: Fidget2
    hit2: Hit2
    taunt: Taunt
    aware: Aware
    sleep: Sleep
    cower: Cower
    cower_start: CowerStart
    cower_end: CowerEnd
    cower_loop: CowerLoop
    backpedal: Backpedal
    backpedal_run: BackpedalRun
    death2: Death2
  skin: guard_{low}
  attachments:
    - model: worlds/mm9/models/{pole}.glb
      node: Xbase
    - model: worlds/mm9/models/{plate}.glb
      node: Bip01 Head
'''
block = HEAD + ''.join(ENTRY.format(comment=c, k=k, low=k.lower(), pole=p, plate='mm9_guard_plate_a' if k == 'A' else 'mm9_guard_plate_c') for c, k, p in (('Guard (row 111)', 'A', 'mm9_guard_halberd'), ('Guard Segeant (row 112)', 'B', 'mm9_guard_halberd'), ('Guard Captain (row 113)', 'C', 'mm9_guard_halberd2'))) + TAIL
s = A.read_text()
s = re.sub(r'# >>> mm9_guard_claude\n.*?# <<< mm9_guard_claude\n', '', s, flags=re.S)
if not s.endswith('\n'): s += '\n'
s += block
fd, tmp = tempfile.mkstemp(dir=A.parent, prefix='.actors_', suffix='.yml')
with os.fdopen(fd, 'w') as f: f.write(s)
os.chmod(tmp, 0o644); os.replace(tmp, A)
print('BOUND', len(s.splitlines()))
