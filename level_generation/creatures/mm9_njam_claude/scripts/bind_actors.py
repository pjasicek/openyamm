#!/usr/bin/env python3
"""Write Njam's descriptor into assets_dev/worlds/mm9/models/actors.yml (from mm9_nobleman_claude/scripts/bind_actors.py). Run under the
shared flock from the repo root:
flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <this>  (temp + rename: the file is hard-linked)."""
import os, re, tempfile
from pathlib import Path
A = Path('assets_dev/worlds/mm9/models/actors.yml')
BLOCK = '''# >>> mm9_njam_claude
# MM9 Njam the Meddler (level_generation/creatures/mm9_njam_claude): Meshy body and head-only model on NJAM.abc's skeleton with its
# own 6 clips and the 41 of its child model PEASANTMALE.abc (all MM9 clips carried), true handedness. Row 261 (L200), baserange.scr,
# MONSTERS Scale 1.5. Bare hands: Njam_Hattack1 Rattack 1.2 s, Njam_Spell1 RangeAttack 0.866 s (right palm forward), Njam_Spell2
# RangeAttack 1.466 s. One skin. Scripted boss events (njam_wingame: CameraSwitch, StartBall, CameraSwitch2, Lightning; freeze skins
# NJAM1-7) are script work: their clips are carried as script_clips (see the project README).
- descriptor: MM9 261 Njam the Meddler
  model: worlds/mm9/models/mm9_njam.glb
  scale: 150.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    cast: Cast
    stride_length: 1.37
    run_stride_length: 3.2
    look: {nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}
    sockets:
      palm_left: LHand1
      palm_right: RHand1
    events:
      attack_melee: {impact: 1.2}
      attack_ranged: {impact: 0.866, release: palm_right}
      cast: {impact: 1.466, release: palm_left}
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
    njam: NjamPose
    spell_attack: SpellAttack
    njam_wingame: WinGame
    njam_twitch: Twitch
    njam_frozen: Frozen
    statue: Statue
    kick: Kick
    attack_melee2: AttackMelee2
    run2: Run2
    lean: Lean
    lean_fidget: LeanFidget
    bar_drink: BarDrink
    bar_fidget: BarFidget
    bar_stand: BarStand
    bless: Bless
    pray: Pray
    bow: Bow
    conv: Conv
    conv1: Conv1
    conv2: Conv2
    conv3: Conv3
    conv4: Conv4
    conv5: Conv5
    fidget2: Fidget2
    fidget3: Fidget3
    fidget4: Fidget4
    fidget5: Fidget5
    fidget8: Fidget8
    peasant_attack: PeasantAttack
    peasant_attack2: PeasantAttack2
    hit2: Hit2
    backpedal: Backpedal
    backpedal_run: BackpedalRun
    cower_start: CowerStart
    cower_loop: CowerLoop
    cower_end: CowerEnd
    sc07_shot1: Sc07Shot1
    play_death: PlayDeath
    play_getup: PlayGetup
# <<< mm9_njam_claude
'''
s = A.read_text()
s = re.sub(r'# >>> mm9_njam_claude\n.*?# <<< mm9_njam_claude\n', '', s, flags=re.S)
if not s.endswith('\n'): s += '\n'
s += BLOCK
fd, tmp = tempfile.mkstemp(dir=A.parent, prefix='.actors_', suffix='.yml')
with os.fdopen(fd, 'w') as f: f.write(s)
os.chmod(tmp, 0o644); os.replace(tmp, A)
print('BOUND', len(s.splitlines()))
