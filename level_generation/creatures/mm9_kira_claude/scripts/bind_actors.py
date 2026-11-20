#!/usr/bin/env python3
"""Write Kira's descriptor into assets_dev/worlds/mm9/models/actors.yml (from mm9_njam_claude/scripts/bind_actors.py). Run under the
shared flock from the repo root:
flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <this>  (temp + rename: the file is hard-linked)."""
import os, re, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm9/models/actors.yml')
BLOCK = '''# >>> mm9_kira_claude
# MM9 Kira the Cold (level_generation/creatures/mm9_kira_claude): Meshy body and paint on KIRA.abc's own skeleton and clips (true
# handedness), MPFB five-finger hands, six added skirt hinges, braid on MM9's Yp chain. Row 251 (L110, NPCbase.scr, MONSTERS Scale 1),
# one skin (KIRAPLATE). KIRA.abc has no death clip: Death = wince2's recoil blended into static_die1 (the corpse pose MM9's PropAnim
# props use). Melee only: wattack1 Rattack 0.373 s; the ranged slot plays the same clip (the engine requires the key). No shield or sword
# on her: MM9 attaches neither by default (ARG_Kira.scr attaches KIRASWORD in the Argument cutscene only). Script clips: what
# ARG_Kira.scr and PropAnim (Static_die1) play.
- descriptor: MM9 251 Kira the Cold
  model: worlds/mm9/models/mm9_kira.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.05
    run_stride_length: 3.0
    look: {nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}
    events:
      attack_melee: {impact: 0.373}
      attack_ranged: {impact: 0.373}
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
    stand: Standing
    walk: Walking
    sit: Sit
    applause: Applause
    sc2_kira5: Sc2_KIRA5
    sc2_kira7: Sc2_Kira7
    sc2_kira9b: Sc2_Kira9b
    sc2_kira12: Sc2_KIRA12
    sc2_kira14: Sc2_KIRA14
    sc2_kira16b: Sc2_KIRA16b
    sc2_kira17: Sc2_Kira17
    sc2_kira20_23: Sc2_KIRA20_23
    sc2_kira22: Sc2_KIRA22
    sc2_kira19: Sc2_Kira19
    static_die1: StaticDie
# <<< mm9_kira_claude
'''
s = A.read_text()
s = re.sub(r'# >>> mm9_kira_claude\n.*?# <<< mm9_kira_claude\n', '', s, flags=re.S)
if not s.endswith('\n'): s += '\n'
s += BLOCK
fd, tmp = tempfile.mkstemp(dir=A.parent, prefix='.actors_', suffix='.yml')
with os.fdopen(fd, 'w') as f: f.write(s)
os.chmod(tmp, 0o644); os.replace(tmp, A)
print('BOUND', len(s.splitlines()))
