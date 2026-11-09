#!/usr/bin/env python3
"""Bind PeasantDM4 (row 10) in assets_dev/worlds/mm9/models/actors.yml and add the rows to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (re-read inside the lock, temp + rename). Run from the repo root under
the flock, then the table generator:
  flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
  level_generation/creatures/mm9_peasantdm4_claude/scripts/bind_actors.py && python3
  tools/mm9_import_discovery/generate_mm9_monster_tables.py'"""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '10': '10\t325\tTown, Peasant Dwarf MaleB A (PeasantDM4 body, PeasantDM4a skin): DAT class TownDwarfMaleA; 3D model mm9_peasantdm4 (one skin, no tiers)',
}
text = open(TSV).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
add = [v for k, v in ROWS.items() if k not in have]
if add:
    if not text.endswith('\n'):
        text += '\n'
    text += '\n'.join(add) + '\n'
    tmp = TSV + '.tmp_pdm4'
    open(tmp, 'w').write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, TSV)
print('rows added', len(add))

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_peasantdm4_claude', '# <<< mm9_peasantdm4_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 PeasantDM4 dwarf townsman with cap and red beard (level_generation/creatures/mm9_peasantdm4_claude): Meshy body on the
# MM9 dwarf male townsfolk skeleton (PEASANTDM4 = PEASANTDM1/DM2 bind: 41 joints, no pelvis, tunic ring Bone22) with the
# PEASANTMALEDWARF library clips (stand, walk, run, Fidget1, Fidget2, conv1 talk, hattack1 Rattack 0.966 s, wince, die1)
# and the clips its scripts play (cower: NPCbase via BaseRun.inc; Rub_Beard and x: NPC7.scr at the refinery;
# randverretainer.scr's `sitting` is not in the library), five-finger MPFB hands, rigid head, mirrored to MM9's true
# handedness. One skin (row 10); PEASANTDM4B is used by no row and is not built.
"""
for desc, skin, label in (('MM9 10 Town', None, 'Town (10, Peasant Dwarf MaleB A, PeasantDM4a, DAT TownDwarfMaleA)'),):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_peasantdm4.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: STRIDE_WALK
    run_stride_length: STRIDE_RUN
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 0.966}}
      attack_ranged: {{impact: 0.966}}
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
    conv1: Talk
    fidget1: Fidget
    fidget2: Fidget2
    cower: Cower
    stand: Standing
    rub_beard: RubBeard
    x: X
"""
BLOCK += END + '\n'
BLOCK = BLOCK.replace('STRIDE_WALK', os.environ.get('STRIDE_WALK', '0.4')).replace('STRIDE_RUN', os.environ.get('STRIDE_RUN', '0.7'))
tmp = p + '.tmp_pdm4'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
