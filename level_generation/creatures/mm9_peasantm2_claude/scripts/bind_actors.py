#!/usr/bin/env python3
"""Write the PeasantM2 townsman descriptors (rows 44, 50) into assets_dev/worlds/mm9/models/actors.yml. Run under the shared flock from
the repo root: flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <this> <walk stride> <run stride>
(temp + rename: the file is hard-linked)."""
import os, re, sys, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm9/models/actors.yml')
WS, RS = sys.argv[1], sys.argv[2]
def block(desc, skin):
    return f'''- descriptor: {desc}
  model: worlds/mm9/models/mm9_peasantm2.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: {WS}
    run_stride_length: {RS}
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 0.533}}
      attack_ranged: {{impact: 0.533}}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: AttackMelee
    attack_ranged: AttackMelee
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  script_clips:
    talk: Talk
    cower: Cower
    conv1: Conv1
    conv2: Talk
    conv3: Conv3
    bow: Bow
  skin: {skin}
'''
BLOCK = ('# >>> mm9_peasantm2_claude\n'
         '# MM9 PeasantM2 townsman (level_generation/creatures/mm9_peasantm2_claude): Meshy body on the PeasantMale skeleton (PEASANTM2.abc,\n'
         '# 45 joints) with the PeasantMale clips its NPC scripts play (NPCbase.scr, BaseRun.inc Cower, Wilam.scr conv1/conv2/conv3/stand/Bow),\n'
         '# true handedness. Row 44 Commoner Human1 MaleA B (PEASANTM2B: cream tunic, brown sleeves, clean-shaven) = tier pm2_b; row 50 Commoner\n'
         '# Human2 MaleA A (PEASANTM2A: olive tunic, white beard) = tier pm2_a. Body: one shared set + region ramps; head per tier (faces differ).\n'
         '# hattack2 impact 0.533 s (MM9 Rattack), as MM9 54 Shopkeeper on the same library.\n'
         + block('MM9 44 Commoner', 'pm2_b') + block('MM9 50 Commoner', 'pm2_a') + '# <<< mm9_peasantm2_claude\n')
s = A.read_text()
s = re.sub(r'# >>> mm9_peasantm2_claude\n.*?# <<< mm9_peasantm2_claude\n', '', s, flags=re.S)
for d in ('MM9 44 Commoner', 'MM9 50 Commoner'):
    assert f'descriptor: {d}\n' not in s, d + ' already bound elsewhere'
if not s.endswith('\n'): s += '\n'
s += BLOCK
fd, tmp = tempfile.mkstemp(dir=A.parent, prefix='.actors_', suffix='.yml')
with os.fdopen(fd, 'w') as f: f.write(s)
os.chmod(tmp, 0o644); os.replace(tmp, A)
print('BOUND', len(s.splitlines()))
