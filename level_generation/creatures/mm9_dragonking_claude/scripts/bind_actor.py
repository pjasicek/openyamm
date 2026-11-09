#!/usr/bin/env python3
"""Add or replace the Dragon King binding in assets_dev/worlds/mm9/models/actors.yml (text block between markers).
Run under flock (level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock); re-reads the file inside the
lock and writes by temp file + os.replace (assets_dev is hard-linked into output/ mirrors)."""
import os, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
YML = ROOT / 'assets_dev/worlds/mm9/models/actors.yml'
BEGIN = '# >>> MM9 Dragon King (level_generation/creatures/mm9_dragonking_claude)'
END = '# <<< MM9 Dragon King'
BLOCK = f"""{BEGIN}
# Meshy body weighted to the original MM9 DRAGON.abc skeleton (113 joints), the MM9 clips resampled: stand, fly
# (travel; the wing downstroke lifts the body off the floor), fidget1, WingAttack (melee: the wing clap at 0.533 s),
# rAttack1 (MM9 fire-bolt spit, RangeAttack 0.417 s: attack 1 and attack 2, the authored third fire-breath
# projectile), Rattack3 (MM9 breath, BreathAttack 0.833 s: the spells Incinerate and Dark Grasp), wince1, die1.
# Taunt and Land (MM9's fly-in from above) are script clips for a boss script. Released from the mouth socket on the
# skull (MM9 RangeAttack socket node Xjawbase). The head follows the party (MM9 HeadFollow) over the neck chain.
# Scale 100 = the MM9 size (GLB in LithTech units x 0.0256; MM9 world scale 2.56): about 1,820 units standing.
- descriptor: MM9 212 Dragon King
  model: worlds/mm9/models/mm9_dragonking.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    cast: Cast
    run: Running
    stride_length: 7.0
    run_stride_length: 9.0
    gait_rate: [0.8, 1.3]
    blend_seconds: 0.25
    sockets:
      mouth: Socket_Mouth
    look: {{nodes: [XneckB, Bip01 Head, XneckD], max_yaw_degrees: 50, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 0.533}}
      attack_ranged: {{impact: 0.417, glow: [mouth], release: mouth, glow_scale: 2.5}}
      cast: {{impact: 0.833, glow: [mouth], release: mouth, glow_scale: 3.0}}
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
    taunt: Taunt
    land: Land
    fidget2: Fidget2
    spit_across: SpitAcross
    breath2: Breath2
    hit2: Hit2
{END}
"""
text = YML.read_text()
if BEGIN in text:
    a = text.index(BEGIN); b = text.index(END) + len(END) + 1
    text = text[:a] + BLOCK + text[b:]
else:
    text = text.rstrip('\n') + '\n' + BLOCK
fd, tmp = tempfile.mkstemp(dir=YML.parent, prefix='.actors.yml.')
with os.fdopen(fd, 'w') as f:
    f.write(text)
os.chmod(tmp, 0o664)
os.replace(tmp, YML)
print('BOUND', YML)
