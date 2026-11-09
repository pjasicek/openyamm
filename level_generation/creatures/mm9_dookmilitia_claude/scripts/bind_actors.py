#!/usr/bin/env python3
"""Write the half orcs' three descriptors into assets_dev/worlds/mm9/models/actors.yml. Run under the shared flock from the repo root:
flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <this>  (temp + rename: the file is hard-linked)."""
import os, re, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm9/models/actors.yml')
HEAD = '''# >>> mm9_dookmilitia_claude
# MM9 Half Orc family (level_generation/creatures/mm9_dookmilitia_claude): Meshy body and head-only model on the original DOOKMILITIA.abc skeleton with its 13 clips plus the 8 of its LithTech child model FIGHTERBASE.abc,
# un-mirrored to true handedness: short sword in the right fist on MM9's Ybasesword bone, left hand empty (MM9's dagger piece is one empty face; the knife leaves the left hand). Rows: Half Orc Recruit L14, Soldier L24, Captain L35;
# torso and head differ in pattern per tier, limbs A and B shared, C own (variants). Hattack1 rattack 0.3 s. Rattack1 RangeAttack 0.5 s from the dagger socket.
'''
TAIL = '# <<< mm9_dookmilitia_claude\n'
ENTRY = '''# {comment}
- descriptor: MM9 Half Orc {k}
  model: worlds/mm9/models/mm9_dookmilitia.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.65
    run_stride_length: 3.3
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      dagger: Ybasedagger
    events:
      attack_melee: {{impact: 0.3}}
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
    taunt2: Taunt2
    cower: Cower
    backpedal: Backpedal
    backpedal_run: BackpedalRun
    death2: Death2
    fidget3: Fidget3
    hit3: Hit3
    sleep: Sleep
  skin: dook_{low}
'''
block = HEAD + ''.join(ENTRY.format(comment=c, k=k, low=k.lower()) for c, k in (('Half Orc Recruit', 'A'), ('Half Orc Soldier', 'B'), ('Half Orc Captain', 'C'))) + TAIL
s = A.read_text()
s = re.sub(r'# >>> mm9_dookmilitia_claude\n.*?# <<< mm9_dookmilitia_claude\n', '', s, flags=re.S)
if not s.endswith('\n'): s += '\n'
s += block
fd, tmp = tempfile.mkstemp(dir=A.parent, prefix='.actors_', suffix='.yml')
with os.fdopen(fd, 'w') as f: f.write(s)
os.chmod(tmp, 0o644); os.replace(tmp, A)
print('BOUND', len(s.splitlines()))
