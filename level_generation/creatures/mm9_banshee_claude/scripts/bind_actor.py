#!/usr/bin/env python3
"""Write the Banshee's three descriptors into assets_dev/worlds/mm9/models/actors.yml. Run under the shared flock:
flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <this>  (temp + rename: the file is hard-linked)."""
import os, re, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm9/models/actors.yml')
BLOCK = '''# >>> mm9_banshee_claude
# MM9 Banshee family (level_generation/creatures/mm9_banshee_claude): see-through by user decision (devdocs/mm9_rework/PLAN.md): ten blended primitives (torso, dress, two arms, cape, two wings, head, two hair sides) on the original BANSHEE.abc
# skeleton, MM9's own clips (jaw folded to one hinge). Rows: Fright L35 (woman), Dread L55 (rotting skull), Terror L65 (green-eyed skull). Scale 100 = MONSTERS.txt Scale 1. Events = MM9 clip events: Lattack 0.269 s (HattackAir1), rangeAttack 0.588 s (RattackAir1), 0.444 s (RattackAir2), from the RangeAttack socket on her left hand (Zhand). True handedness: Zhand01 is her right.
# No hand effect and no glow, as in MM9: her clips' DoFX 1 names FX1 (0-based, object.lto 0x1001af90), which her rows leave empty
# (their only effect, FX0 redyeldots, never plays); MM9 has no light there.
- descriptor: MM9 Banshee A
  model: worlds/mm9/models/mm9_banshee.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation: &mm9_banshee_animation
    cast: AttackRanged2
    run: Walking
    stride_length: 2.0
    gait_rate: [0.7, 1.4]
    upper_body_root: Scene Root
    look: {nodes: [Xhead], max_yaw_degrees: 60, max_pitch_degrees: 35}
    sockets:
      palm_left: Zfingbase
      palm_right: Zfingbase04
    events:
      attack_melee: {impact: 0.269}
      attack_ranged: {impact: 0.588, release: palm_left}
      cast: {impact: 0.444, release: palm_left}
  clips: &mm9_banshee_clips
    standing: Standing
    walking: Walking
    attack_melee: AttackMelee
    attack_ranged: AttackRanged
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  script_clips: &mm9_banshee_script_clips
    taunt: Taunt
    fidget2: Fidget2
    attack_ranged2: AttackRanged2
    hit2: Hit2
    transition: Transition
    resurrect: Resurrect
    fly: Walking
  skin: banshee_a
- descriptor: MM9 Banshee B
  model: worlds/mm9/models/mm9_banshee.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation: *mm9_banshee_animation
  clips: *mm9_banshee_clips
  script_clips: *mm9_banshee_script_clips
  skin: banshee_b
- descriptor: MM9 Banshee C
  model: worlds/mm9/models/mm9_banshee.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation: *mm9_banshee_animation
  clips: *mm9_banshee_clips
  script_clips: *mm9_banshee_script_clips
  skin: banshee_c
# <<< mm9_banshee_claude
'''

text = A.read_text()
pattern = re.compile(r'# >>> mm9_banshee_claude\n.*?# <<< mm9_banshee_claude\n', re.S)
text = pattern.sub(BLOCK, text) if pattern.search(text) else text.rstrip('\n') + '\n' + BLOCK
fd, tmp = tempfile.mkstemp(dir=A.parent)
with os.fdopen(fd, 'w') as f:
    f.write(text)
os.chmod(tmp, 0o644)
os.replace(tmp, A)
print('BOUND')
