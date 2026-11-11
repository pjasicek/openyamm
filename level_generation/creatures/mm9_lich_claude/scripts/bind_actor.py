#!/usr/bin/env python3
"""Write the Lich's two descriptors into assets_dev/worlds/mm9/models/actors.yml. Run under the shared flock:
flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <this>  (temp + rename: the file is hard-linked)."""
import os, re, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm9/models/actors.yml')
BLOCK = '''# >>> mm9_lich_claude
# MM9 Lich family (level_generation/creatures/mm9_lich_claude): Meshy body on the original LICH.abc skeleton, MM9's own clips
# resampled, skull from a skull-only Meshy model (head set), bone fingers rigged by connectivity (three joints, driven by
# MM9's finger curl). Rows: Lich L45 (LICH1), Power Lich L55 (LICH2), tiers by region mask and ramps from the two skins; eyes
# glow red / green. Scale 120 = 100 x MONSTERS.txt Scale 1.2. Events = MM9 clip events: Rattack 0.386 s (Hattack2), RangeAttack
# 0.447 s (Rattack1, socket on the left hand). LHand1 / RHand1 are MM9's sockets, moved onto our palms. MM9's hand effects are
# socket effects on both palms (DoFX n plays FX n of MONSTERS.txt, 0-based: object.lto 0x1001af90): the Power Lich's Rattack1
# DoFX 0 bluedots 0.235-1.176 s, ResurrectSpell DoFX 1 greenyeldots 0.2-1.933 s; the Lich has no FX. Both rows' ResurrectFX
# GreaterDemon plays at the pelvis as a corpse rises (Resurrect). No glow: MM9 has no light there.
- descriptor: MM9 Lich A
  model: worlds/mm9/models/mm9_lich.glb
  scale: 120.0
  yaw_offset: -1.570796327
  animation:
    cast: AttackRanged
    run: Running
    stride_length: 1.06
    run_stride_length: 2.66
    gait_rate: [0.7, 1.4]
    upper_body_root: Bip01 Spine1
    look: {nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}
    sockets:
      palm_left: LHand1
      palm_right: RHand1
      body: Bip01 Pelvis
    events:
      attack_melee: {impact: 0.386}
      attack_ranged: {impact: 0.447, release: palm_left}
      cast: {impact: 0.447, release: palm_left}
      resurrect: {effect: {id: mm9:GreaterDemon, socket: body}}
  clips: &mm9_lich_clips
    standing: Standing
    walking: Walking
    attack_melee: AttackMelee
    attack_ranged: AttackRanged
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  script_clips: &mm9_lich_script_clips
    taunt: Taunt
    search: Search
    fidget2: Fidget2
    attack_melee2: AttackMelee2
    hit2: Hit2
    resurrect_spell: ResurrectSpell
    resurrect: Resurrect
    death2: Death2
    dead2: Dead2
    backpedal: Backpedal
    backpedal_run: BackpedalRun
  skin: lich_a
# Power Lich: navy cape, blue-steel trim, black wraps, green eyes (LICH2)
- descriptor: MM9 Lich B
  model: worlds/mm9/models/mm9_lich.glb
  scale: 120.0
  yaw_offset: -1.570796327
  animation:
    cast: AttackRanged
    run: Running
    stride_length: 1.06
    run_stride_length: 2.66
    gait_rate: [0.7, 1.4]
    upper_body_root: Bip01 Spine1
    look: {nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}
    sockets:
      palm_left: LHand1
      palm_right: RHand1
      body: Bip01 Pelvis
    events:
      attack_melee: {impact: 0.386}
      attack_ranged: {impact: 0.447, release: palm_left, effect: {id: mm9:bluedots, sockets: [palm_left, palm_right], start: 0.235, end: 1.176}}
      cast: {impact: 0.447, release: palm_left, effect: {id: mm9:bluedots, sockets: [palm_left, palm_right], start: 0.235, end: 1.176}}
      resurrect_spell: {effect: {id: mm9:greenyeldots, sockets: [palm_left, palm_right], start: 0.2, end: 1.933}}
      resurrect: {effect: {id: mm9:GreaterDemon, socket: body}}
  clips: *mm9_lich_clips
  script_clips: *mm9_lich_script_clips
  skin: lich_b
# <<< mm9_lich_claude
'''
s = A.read_text()
m = re.search(r'# >>> mm9_lich_claude\n.*?# <<< mm9_lich_claude\n', s, re.S)
s = s[:m.start()] + BLOCK + s[m.end():] if m else s.rstrip('\n') + '\n' + BLOCK
fd, tmp = tempfile.mkstemp(dir=A.parent, suffix='.tmp')
with os.fdopen(fd, 'w') as f:
    f.write(s)
os.chmod(tmp, A.stat().st_mode)
os.replace(tmp, A)
print('bound')
