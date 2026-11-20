#!/usr/bin/env python3
"""Write the Horde's three descriptors into assets_dev/worlds/mm9/models/actors.yml. Run under the shared flock from the repo root:
flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <this>  (temp + rename: the file is hard-linked)."""
import os, re, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm9/models/actors.yml')
HEAD = '''# >>> mm9_clansoldier_claude
# MM9 Horde family (level_generation/creatures/mm9_clansoldier_claude): Meshy body and head on the original CLANSOLDIER.abc skeleton with its 23 clips, true handedness: sword in the right fist, shield on a centre grip in the left, both rigid on MM9's Ybase bones.
# Rows: Horde Grunt L34, Horde Warrior L44, Horde Leader L54; coat, sleeves, head and weapons differ in pattern per tier, limbs shared by A and B (variants). Hattack1 Rattack 0.32 s, Hattack2 Rattack 0.35 s. No ranged clip in MM9: AttackRanged is Hattack2, release at the sword (rows carry MM9Axe at 100 %).
'''
TAIL = '# <<< mm9_clansoldier_claude\n'
ENTRY = '''# {comment}
- descriptor: MM9 Horde {k}
  model: worlds/mm9/models/mm9_clansoldier.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.8
    run_stride_length: 2.9
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      sword: Ybasesword
    events:
      attack_melee: {{impact: 0.32}}
      attack_ranged: {{impact: 0.35, release: sword}}
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
    aware: Aware
    aware2: Aware2
    sleep: Sleep
    block: Block
    hit2: Hit2
    cower: Cower
    backpedal: Backpedal
    backpedal_run: BackpedalRun
    death2: Death2
    dead_static: DeadStatic
    dead2: Dead2
  skin: clan_{low}
'''
block = HEAD + ''.join(ENTRY.format(comment=c, k=k, low=k.lower()) for c, k in (('Horde Grunt (row 129)', 'A'), ('Horde Warrior (row 130)', 'B'), ('Horde Leader (row 131)', 'C'))) + TAIL
s = A.read_text()
s = re.sub(r'# >>> mm9_clansoldier_claude\n.*?# <<< mm9_clansoldier_claude\n', '', s, flags=re.S)
if not s.endswith('\n'): s += '\n'
s += block
fd, tmp = tempfile.mkstemp(dir=A.parent, prefix='.actors_', suffix='.yml')
with os.fdopen(fd, 'w') as f: f.write(s)
os.chmod(tmp, 0o644); os.replace(tmp, A)
print('BOUND', len(s.splitlines()))
