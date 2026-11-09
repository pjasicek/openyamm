#!/usr/bin/env python3
"""Bind PeasantDM3 (rows 11, 12) in assets_dev/worlds/mm9/models/actors.yml and add the rows to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (re-read inside the lock, temp + rename). Run from the repo root under
the flock, then the table generator:
  flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
  level_generation/creatures/mm9_peasantdm3_claude/scripts/bind_actors.py && python3
  tools/mm9_import_discovery/generate_mm9_monster_tables.py'"""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '11': '11\t326\tTown, Peasant Dwarf MaleB B (PeasantDM3 body, PeasantDM3b skin): DAT class TownDwarfMaleB; 3D model mm9_peasantdm3, tier pdm3_b',
    '12': '12\t328\tShopkeeper, Peasant Dwarf MaleC A (PeasantDM3 body, PeasantDM3a skin): DAT class ShopkeeperDwarfMaleA; 3D model mm9_peasantdm3, tier pdm3_a',
}
text = open(TSV).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
add = [v for k, v in ROWS.items() if k not in have]
if add:
    if not text.endswith('\n'):
        text += '\n'
    text += '\n'.join(add) + '\n'
    tmp = TSV + '.tmp_pdm3'
    open(tmp, 'w').write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, TSV)
print('rows added', len(add))

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_peasantdm3_claude', '# <<< mm9_peasantdm3_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 PeasantDM3 dwarf townsman (level_generation/creatures/mm9_peasantdm3_claude): variant of PeasantDM1's body, rig, weights and
# clips (same 41-joint dwarf male townsfolk skeleton) with MM9 DM3's long hair to the shoulders and a longer pointed beard, no
# medallion, and its own body and head paints; PEASANTMALEDWARF library clips (stand, walk, run, Fidget1, Fidget2, conv1 talk,
# hattack1 Rattack 0.966 s, wince, die1) + cower (NPCbase via BaseRun.inc; rows 11/12 have no DAT script). Tiers: one body and
# one head set with region masks and ramps (shared paint PEASANTDM3B; A: purple knit, pale gold trim, grey-brown hair).
"""
for desc, skin, label in (('MM9 11 Town', 'pdm3_b', 'Town (11, Peasant Dwarf MaleB B, PeasantDM3b, DAT TownDwarfMaleB)'),
                          ('MM9 12 Shopkeeper', 'pdm3_a', 'Shopkeeper (12, Peasant Dwarf MaleC A, PeasantDM3a, DAT ShopkeeperDwarfMaleA)')):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_peasantdm3.glb
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
  skin: {skin}
"""
BLOCK += END + '\n'
BLOCK = BLOCK.replace('STRIDE_WALK', os.environ.get('STRIDE_WALK', '0.4')).replace('STRIDE_RUN', os.environ.get('STRIDE_RUN', '0.7'))
tmp = p + '.tmp_pdm3'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
