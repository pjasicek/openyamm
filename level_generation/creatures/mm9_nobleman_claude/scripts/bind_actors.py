#!/usr/bin/env python3
"""Write the noblemen's three descriptors into assets_dev/worlds/mm9/models/actors.yml. Run under the shared flock from the repo root:
flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <this>  (temp + rename: the file is hard-linked)."""
import os, re, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm9/models/actors.yml')
HEAD = '''# >>> mm9_nobleman_claude
# MM9 Nobleman family (level_generation/creatures/mm9_nobleman_claude): Meshy body and head-only model on NOBLEMAN.abc's skeleton and its 15 clips, true handedness. Rows: Baron L45, Viscount L55, Count L65. No weapon: MM9's attacks are bare hands (Hattack1 Rattack 0.533 s, Hattack2 Rattack 0.8 s on the second attack slot).
# Torso and head images per tier (design differs), limbs one shared set with a breeches ramp (variants). Doublet skirt on MM9's six hinge bones.
'''
TAIL = '# <<< mm9_nobleman_claude\n'
ENTRY = '''# {comment}
- descriptor: MM9 Nobleman {k}
  model: worlds/mm9/models/mm9_nobleman.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.17
    run_stride_length: 3.6
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 0.533}}
      attack_ranged: {{impact: 0.8}}
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
    cower: Cower
    cower_start: CowerStart
    cower_loop: CowerLoop
    cower_end: CowerEnd
    death2: Death2
  skin: nb_{low}
'''
block = HEAD + ''.join(ENTRY.format(comment=c, k=k, low=k.lower()) for c, k in (('Baron (row 153)', 'A'), ('Viscount (row 154)', 'B'), ('Count (row 155)', 'C'))) + TAIL
s = A.read_text()
s = re.sub(r'# >>> mm9_nobleman_claude\n.*?# <<< mm9_nobleman_claude\n', '', s, flags=re.S)
if not s.endswith('\n'): s += '\n'
s += block
fd, tmp = tempfile.mkstemp(dir=A.parent, prefix='.actors_', suffix='.yml')
with os.fdopen(fd, 'w') as f: f.write(s)
os.chmod(tmp, 0o644); os.replace(tmp, A)
print('BOUND', len(s.splitlines()))
