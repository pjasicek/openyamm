#!/usr/bin/env python3
"""Write the highwaymen's three descriptors into assets_dev/worlds/mm9/models/actors.yml. Run under the shared flock from the repo root:
flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <this>  (temp + rename: the file is hard-linked)."""
import os, re, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm9/models/actors.yml')
HEAD = '''# >>> mm9_highwayman_claude
# MM9 Highwayman family (level_generation/creatures/mm9_highwayman_claude): Meshy body and head-only model on the original HIGHWAYMAN.abc skeleton with its 9 clips plus the 12 of its LithTech child model FIGHTERBASE.abc,
# un-mirrored to true handedness: short sword in the right fist, dagger in the left, both rigid on MM9's Ybase bones. Rows: Cutpurse L8, Burglar L14, Bandit L22; torso and head differ in pattern per tier, limbs shared by A and B
# (variants). Hattack1 Rattack 0.444 s. Rattack1 RangeAttack 0.5 s from the dagger socket; the dagger's bone scales to nothing until the clip ends.
'''
TAIL = '# <<< mm9_highwayman_claude\n'
ENTRY = '''# {comment}
- descriptor: MM9 Highwayman {k}
  model: worlds/mm9/models/mm9_highwayman.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.6
    run_stride_length: 3.2
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      dagger: Ybasedagger
    events:
      attack_melee: {{impact: 0.444}}
      attack_ranged: {{impact: 0.5, release: dagger}}
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
    cower: Cower
    cower_start: CowerStart
    cower_loop: CowerLoop
    cower_end: CowerEnd
    backpedal: Backpedal
    backpedal_run: BackpedalRun
    death2: Death2
    lying_down: LyingDown
    jumping_down: JumpingDown
  skin: hw_{low}
'''
block = HEAD + ''.join(ENTRY.format(comment=c, k=k, low=k.lower()) for c, k in (('Cutpurse (row 99)', 'A'), ('Burglar (row 100)', 'B'), ('Bandit (row 101)', 'C'))) + TAIL
s = A.read_text()
s = re.sub(r'# >>> mm9_highwayman_claude\n.*?# <<< mm9_highwayman_claude\n', '', s, flags=re.S)
if not s.endswith('\n'): s += '\n'
s += block
fd, tmp = tempfile.mkstemp(dir=A.parent, prefix='.actors_', suffix='.yml')
with os.fdopen(fd, 'w') as f: f.write(s)
os.chmod(tmp, 0o644); os.replace(tmp, A)
print('BOUND', len(s.splitlines()))
