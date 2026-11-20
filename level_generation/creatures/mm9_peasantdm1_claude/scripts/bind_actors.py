#!/usr/bin/env python3
"""Bind PeasantDM1 (rows 8, 13, 14) in assets_dev/worlds/mm9/models/actors.yml and add the rows to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (re-read inside the lock, temp + rename). Run from the repo root under
the flock, then the table generator:
  flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
  level_generation/creatures/mm9_peasantdm1_claude/scripts/bind_actors.py && python3
  tools/mm9_import_discovery/generate_mm9_monster_tables.py'"""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '8': '8\t322\tCommoner, Peasant Dwarf MaleA A (PeasantDM1 body, PeasantDM1a skin): DAT class CommonerDwarfMaleA; 3D model mm9_peasantdm1, tier pdm1_a',
    '13': '13\t329\tShopkeeper, Peasant Dwarf MaleC B (PeasantDM1 body, PeasantDM1b skin): DAT class ShopkeeperDwarfMaleB; 3D model mm9_peasantdm1, tier pdm1_b',
    '14': '14\t329\tShopkeeper, Peasant Dwarf MaleC B (PeasantDM1 body, PeasantDM1b skin; duplicate of row 13): 3D model mm9_peasantdm1, tier pdm1_b',
}
text = open(TSV).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
add = [v for k, v in ROWS.items() if k not in have]
if add:
    if not text.endswith('\n'):
        text += '\n'
    text += '\n'.join(add) + '\n'
    tmp = TSV + '.tmp_pdm1'
    open(tmp, 'w').write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, TSV)
print('rows added', len(add))

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_peasantdm1_claude', '# <<< mm9_peasantdm1_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 PeasantDM1 dwarf townsman (level_generation/creatures/mm9_peasantdm1_claude): Meshy body on the MM9 PeasantDM1 /
# dwarf male townsfolk skeleton (41 joints, no pelvis, tunic ring Bone22) with the PEASANTMALEDWARF library clips (stand,
# walk, run, Fidget1, Fidget2, conv1 talk, hattack1 Rattack 0.966 s, wince, die1) and the clips its scripts play (cower:
# NPCbase via BaseRun.inc; conv1/stand: NPC109; rub_beard, rock, hammer, dump: DwarvenMiner.scr, whose pick prop
# dwarfaxe.abc is a held item), five-finger MPFB hands, mirrored to MM9's true handedness. Tiers: one body set with region
# mask and ramps (shared paint PEASANTDM1A; B: ochre tunic) and a tier B head colour (MM9 paints a different man).
"""
for desc, skin, label in (('MM9 8 Commoner', 'pdm1_a', 'Commoner (8, Peasant Dwarf MaleA A, PeasantDM1a, DAT CommonerDwarfMaleA)'),
                          ('MM9 13 Shopkeeper', 'pdm1_b', 'Shopkeeper (13, Peasant Dwarf MaleC B, PeasantDM1b, DAT ShopkeeperDwarfMaleB)'),
                          ('MM9 14 Shopkeeper', 'pdm1_b', 'Shopkeeper (14, the same as row 13)')):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_peasantdm1.glb
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
    rock: Rock
    hammer: Hammer
    dump: Dump
  skin: {skin}
"""
BLOCK += END + '\n'
BLOCK = BLOCK.replace('STRIDE_WALK', os.environ.get('STRIDE_WALK', '0.4')).replace('STRIDE_RUN', os.environ.get('STRIDE_RUN', '0.7'))
tmp = p + '.tmp_pdm1'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
