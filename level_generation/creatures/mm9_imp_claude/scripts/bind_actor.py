#!/usr/bin/env python3
"""Append the Imp bindings to assets_dev/worlds/mm9/models/actors.yml, temp + rename, under the flock (run with flock)."""
import os, re, sys
from pathlib import Path
Y = Path('assets_dev/worlds/mm9/models/actors.yml')
s = Y.read_text()
assert 'MM9 Imp A' not in s
T = """# MM9 Imp family (level_generation/creatures/mm9_imp_claude): Meshy body on the original IMP.abc skeleton (joints
# translated, the mesh posed to MM9's bind), MM9's own clips, the right fist solved round the trident; one shared skin,
# tiers by region mask + ramps from IMP1-3; B's shin wraps and C's tongue are per-tier attachments. Scale 100 is the MM9 size.
# Event times are the MM9 clip events: Hattack2 Rattack 0.389 s, Rattack1 RangeAttack 0.45 s, released at the trident's tip.
"""
for tier, label, extra in (('A', 'Imply: yellow, green eyes (IMP1)', ''),
                           ('B', 'Imp: brown, amber eyes, shin wraps (IMP2)', """    - model: worlds/mm9/models/mm9_imp_wrapl.glb
      node: Xwrap L
    - model: worlds/mm9/models/mm9_imp_wrapr.glb
      node: Xwrap R
"""),
                           ('C', 'Imp Elder: red, orange eyes, tongue (IMP3)', """    - model: worlds/mm9/models/mm9_imp_tongue.glb
      node: Xtongue
""")):
    T += f"""# {label}
- descriptor: MM9 Imp {tier}
  model: worlds/mm9/models/mm9_imp.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 0.76
    run_stride_length: 1.0
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      trident: Yweapon
    events:
      attack_melee: {{impact: 0.389}}
      attack_ranged: {{impact: 0.45, release: trident}}
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
    fidget2: Fidget2
    aware: Aware
    attack_melee2: AttackRanged
    hit2: Hit2
    death2: Death2
    dead2: Dead2
    backpedal: Backpedal
    backpedal_run: BackpedalRun
  skin: imp_{tier.lower()}
  attachments:
    - model: worlds/mm9/models/mm9_imp_trident.glb
      node: Yweaponbase
{extra}"""
tmp = Y.with_suffix('.yml.imp_tmp')
tmp.write_text(s.rstrip('\n') + '\n' + T)
os.replace(tmp, Y)
print('BOUND', len(T))
