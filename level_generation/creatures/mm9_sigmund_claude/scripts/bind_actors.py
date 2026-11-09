#!/usr/bin/env python3
"""Bind Sigmund the Stressed (row 247) in assets_dev/worlds/mm9/models/actors.yml and add the row to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (re-read inside the lock, temp + rename). Run from the repo root under
the flock, then the table generator:
  flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
  level_generation/creatures/mm9_sigmund_claude/scripts/bind_actors.py && python3
  tools/mm9_import_discovery/generate_mm9_monster_tables.py'"""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '247': '247\t403\tSigmund the Stressed (sigmund.abc + child model sigmund_child.ABC, sigmund skin, FHP skeleton): Jarl of Drangheim; DAT class SigmundtheStressed in Drangheim City (NPCbase), Afterworld (NPC87.scr) and Thronheim City (ARG_Sigmund.scr, the Argument scene); legacy Swordsman A as the fallback visual; 3D model mm9_sigmund',
}
text = open(TSV).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
add = [v for k, v in ROWS.items() if k not in have]
if add:
    if not text.endswith('\n'):
        text += '\n'
    text += '\n'.join(add) + '\n'
    tmp = TSV + '.tmp_sig'
    open(tmp, 'w').write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, TSV)
print('rows added', len(add))

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_sigmund_claude', '# <<< mm9_sigmund_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 Sigmund the Stressed, Jarl of Drangheim (level_generation/creatures/mm9_sigmund_claude): Meshy body on SIGMUND.abc's
# own 49-joint FHP skeleton (pelvis root, ponytail and mail-skirt joints), five-finger MPFB hands, mirrored to MM9's true
# handedness. Row 247 (L80, NPCbase.scr, BaseName PeasantMale, Scale 1), one skin. Clips: the child model sigmund_child.ABC
# (stand, walk, fidget) and SIGMUND.abc's own clips his scripts play (ARG_Sigmund.scr: loopanim Sit, Agree, Applause,
# Sc2_Sigmund1b/1c/3b; NPC87.scr: loopanim Sit; PropAnim props: Static_die1). Neither model has run, attack, hit or death
# clips: Running, AttackMelee (hattack1 Rattack 0.5 s), Hit and Death are PeasantMale library clips retargeted onto the
# FHP skeleton (world-rotation copy).
- descriptor: MM9 247 Sigmund the Stressed
  model: worlds/mm9/models/mm9_sigmund.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: STRIDE_WALK
    run_stride_length: STRIDE_RUN
    look: {nodes: [FHP Neck, FHP Head], max_yaw_degrees: 60, max_pitch_degrees: 35}
    events:
      attack_melee: {impact: 0.5}
      attack_ranged: {impact: 0.5}
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
    fidget: Fidget
    sit: Sit
    agree: Agree
    applause: Applause
    sc2_sigmund1b: Sc2_Sigmund1b
    sc2_sigmund1c: Sc2_Sigmund1c
    sc2_sigmund3b: Sc2_Sigmund3b
    static_die1: StaticDie
"""
BLOCK += END + '\n'
BLOCK = BLOCK.replace('STRIDE_WALK', os.environ.get('STRIDE_WALK', '1.34')).replace('STRIDE_RUN', os.environ.get('STRIDE_RUN', '2.8'))
tmp = p + '.tmp_sig'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
