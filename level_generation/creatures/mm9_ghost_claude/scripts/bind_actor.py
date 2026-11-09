#!/usr/bin/env python3
"""Write the Ghost's three descriptors into assets_dev/worlds/mm9/models/actors.yml. Run under the shared flock:
flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <this>  (temp + rename: the file is hard-linked)."""
import os, re, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm9/models/actors.yml')
BLOCK = '''# >>> mm9_ghost_claude
# MM9 Ghost family (level_generation/creatures/mm9_ghost_claude): see-through by user decision (devdocs/mm9_rework/PLAN.md): four blended primitives (body, two arms, head) on the original GHOST.abc
# skeleton, MM9's own clips. The head is a separate piece that flies free of the body, as in MM9. Rows: Shadow L33 (GHOST1), Apparition L44 (GHOST2), Specter L55 (GHOST3). Scale 180 = 100 x MONSTERS.txt
# Scale 1.8. Events = MM9 clip events: Rattack 0.400 s (HattackAir1), RangeAttack 0.292 s (RAttack1, right hand leads). MM9 has no death clip: Death is authored (a whirl up to nothing), Dead is empty.
- descriptor: MM9 Ghost A
  model: worlds/mm9/models/mm9_ghost.glb
  scale: 180.0
  yaw_offset: -1.570796327
  animation: &mm9_ghost_animation
    cast: AttackRanged
    run: Walking
    stride_length: 2.0
    gait_rate: [0.7, 1.4]
    upper_body_root: Scene Root
    look: {nodes: [Xhead], max_yaw_degrees: 60, max_pitch_degrees: 35}
    sockets:
      palm_left: ZfingA
      palm_right: ZfingA01
    events:
      attack_melee: {impact: 0.4}
      attack_ranged: {impact: 0.292, glow: [palm_right], release: palm_right}
      cast: {impact: 0.292, glow: [palm_right], release: palm_right}
  clips: &mm9_ghost_clips
    standing: Standing
    walking: Walking
    attack_melee: AttackMelee
    attack_ranged: AttackRanged
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  script_clips: &mm9_ghost_script_clips
    taunt: Taunt
    aware: Aware
    fidget2: Fidget2
    attack_melee2: AttackMelee2
    hit2: Hit2
  skin: ghost_a
- descriptor: MM9 Ghost B
  model: worlds/mm9/models/mm9_ghost.glb
  scale: 180.0
  yaw_offset: -1.570796327
  animation: *mm9_ghost_animation
  clips: *mm9_ghost_clips
  script_clips: *mm9_ghost_script_clips
  skin: ghost_b
- descriptor: MM9 Ghost C
  model: worlds/mm9/models/mm9_ghost.glb
  scale: 180.0
  yaw_offset: -1.570796327
  animation: *mm9_ghost_animation
  clips: *mm9_ghost_clips
  script_clips: *mm9_ghost_script_clips
  skin: ghost_c
# <<< mm9_ghost_claude
'''

text = A.read_text()
pattern = re.compile(r'# >>> mm9_ghost_claude\n.*?# <<< mm9_ghost_claude\n', re.S)
text = pattern.sub(BLOCK, text) if pattern.search(text) else text.rstrip('\n') + '\n' + BLOCK
fd, tmp = tempfile.mkstemp(dir=A.parent)
with os.fdopen(fd, 'w') as f:
    f.write(text)
os.chmod(tmp, 0o644)
os.replace(tmp, A)
print('BOUND')
