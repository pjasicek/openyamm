#!/usr/bin/env python3
"""Append or replace the Ebora bindings in assets_dev/worlds/mm9/models/actors.yml (temp + rename; run under the flock
level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock, from the repo root). Args: <walk stride> <run stride>"""
import os, re, sys
p = 'assets_dev/worlds/mm9/models/actors.yml'
walk, run = sys.argv[1:3]
s = open(p).read()
BEGIN = '# MM9 Ebora body (level_generation/creatures/mm9_ebora_claude)'
if BEGIN in s:
    a = s.index(BEGIN); m = re.search(r'\n# (?!Ebora |Concubine |MM9 Ebora body)[^\n]*\n- descriptor:', s[a:]); b = a + m.start() + 1 if m else len(s)
    s = s[:a] + s[b:]
BLOCK = BEGIN + """: Meshy body on EBORA.abc's skeleton (bound in the masters' A pose, MM9's local rotations), 15 finger bones per side from the mesh, bat wings built on MM9's wing chains (Bone13-69), whole model mirrored to true handedness.
# Tiers: eb = Ebora's own paint; s1 = the Concubine row (siren1) own paint; s2-s4 = siren2-4 by region ramps on s1 (EBORACONCUBINE.scr picks siren1-4 at random; only s1 is bound). Events: Hattack1 rattack 0.407 s; Castspell hands thrust forward at 0.6 s (speakanimsound 0.588).
"""
SCRIPT = """  script_clips:
    fidget2: Fidget2
    taunt: Taunt
    hit2: Hit2
    backpedal: Backpedal
    backpedal_run: BackpedalRun
    fly: Fly
    flap: Flap
    launch: Launch
    land: Land
    hit_air: HitAir
    death_air: DeathAir
    fall: Fall
    fall_down: FallDown
"""
for desc, skin, label in (('MM9 301 Ebora', 'eb', 'Ebora (row 301)'), ('MM9 302 Concubine', 's1', 'Concubine (row 302)')):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_ebora.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    cast: AttackRanged
    stride_length: {walk}
    run_stride_length: {run}
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    sockets:
      palm_left: LHand1
      palm_right: RHand1
    events:
      attack_melee: {{impact: 0.407}}
      attack_ranged: {{impact: 0.6, glow: [palm_left, palm_right], release: palm_right}}
      cast: {{impact: 0.6, glow: [palm_left, palm_right], release: palm_right}}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: AttackMelee
    attack_ranged: AttackRanged
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
""" + SCRIPT + f"""  skin: {skin}
"""
tmp = p + '.tmp_ebora'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
