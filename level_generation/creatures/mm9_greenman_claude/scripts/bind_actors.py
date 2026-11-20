#!/usr/bin/env python3
"""Bind The Green Man (row 266) in assets_dev/worlds/mm9/models/actors.yml and add the row to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (re-read inside the lock, temp + rename). Run from the repo root under
the flock, then the table generator:
  flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
  level_generation/creatures/mm9_greenman_claude/scripts/bind_actors.py && python3
  tools/mm9_import_discovery/generate_mm9_monster_tables.py'"""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '266': '266\t451\tThe Green Man (GREENMAN.abc, greenman skin + Greenmanstaff, own 56-joint Bip01 skeleton with five-finger hands and a staff bone): druid promotion NPC; DAT object GreenMan0 in Frosgard (NPC221.scr: BaseWander, Rude promotes to Druid; GreenMan.scr: never winces); legacy Treant A as the fallback visual; 3D model mm9_greenman',
}
text = open(TSV).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
add = [v for k, v in ROWS.items() if k not in have]
if add:
    if not text.endswith('\n'):
        text += '\n'
    text += '\n'.join(add) + '\n'
    tmp = TSV + '.tmp_gm'
    open(tmp, 'w').write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, TSV)
print('rows added', len(add))

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_greenman_claude', '# <<< mm9_greenman_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 The Green Man (level_generation/creatures/mm9_greenman_claude): Meshy body on GREENMAN.abc's own 56-joint Bip01
# skeleton (five three-joint fingers per hand, staff bone Bone01), five-finger MPFB hands copying MM9's finger chains, a
# rigid staff in the right hand, mirrored to MM9's true handedness. Row 266 (NPC, GreenMan.scr / NPC221.scr BaseWander,
# BaseName PeasantMale, Scale 1), one skin. Clips: GREENMAN.abc's own stand, walk, fidget1, fidget2; it has no run, attack,
# hit or death: Running, AttackMelee (hattack1, Rattack 0.5 s), Hit and Death are PeasantMale library clips retargeted
# onto its skeleton (world-rotation copy, leg ratio 1.654, the staff kept in the hand).
- descriptor: MM9 266 Green Man
  model: worlds/mm9/models/mm9_greenman.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: STRIDE_WALK
    run_stride_length: STRIDE_RUN
    look: {nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}
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
    fidget1: Fidget
    fidget2: Fidget2
"""
BLOCK += END + '\n'
BLOCK = BLOCK.replace('STRIDE_WALK', os.environ.get('STRIDE_WALK', '1.9')).replace('STRIDE_RUN', os.environ.get('STRIDE_RUN', '4.6'))
tmp = p + '.tmp_gm'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
