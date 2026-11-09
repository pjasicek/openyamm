#!/usr/bin/env python3
"""Bind the seven PeasantDF rows (MONSTERS.txt 1-7) in assets_dev/worlds/mm9/models/actors.yml and add them to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (re-read inside the lock, temp + rename). Run from the repo root under
the flock, then the table generator:
  flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
  level_generation/creatures/mm9_peasantdf_claude/scripts/bind_actors_pdf.py && python3
  tools/mm9_import_discovery/generate_mm9_monster_tables.py'
Only designs whose GLB is installed are bound (DESIGNS env, default all four)."""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
# row: (legacy stand-in from mm9_npc_legacy_replacements.tsv, role, MONSTERS name, design, skin/tier, DAT class)
ROWS = {
    '1': ('313', 'Commoner', 'Peasant Dwarf FemaleA A', 'd1', 'pdf1_a', 'PeasantDF1a', 'CommonerDwarfFemaleA'),
    '2': ('314', 'Commoner', 'Peasant Dwarf FemaleA B', 'd2', 'pdf2_b', 'PeasantDF2b', 'CommonerDwarfFemaleB'),
    '3': ('316', 'Town', 'Peasant Dwarf FemaleB A', 'd4', 'pdf4_b', 'PeasantDF4b', 'no placed object'),
    '4': ('317', 'Town', 'Peasant Dwarf FemaleB B', 'd3', 'pdf3_a', 'PeasantDF3a', 'TownDwarfFemaleB'),
    '5': ('319', 'Shopkeeper', 'Peasant Dwarf FemaleC A', 'd1', 'pdf1_b', 'PeasantDF1b', 'no placed object'),
    '6': ('320', 'Shopkeeper', 'Peasant Dwarf FemaleC B', 'd4', 'pdf4_a', 'PeasantDF4a', 'ShopKeeperDwarfFemaleB'),
    '7': ('318', 'Prisoner', 'Peasant Dwarf FemaleD A', 'd3', 'pdf3_b', 'PeasantDF3b', 'no placed object'),
}
DESIGNS = os.environ.get('DESIGNS', 'd1,d2,d3,d4').split(',')
rows = {k: v for k, v in ROWS.items() if v[3] in DESIGNS}
text = open(TSV).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
add = [f'{k}\t{v[0]}\t{v[1]}, {v[2]} (PeasantDF{v[3][1]} body, {v[5]} skin): DAT class {v[6]}; 3D model mm9_peasantdf{v[3][1]}, tier {v[4]}'
       for k, v in rows.items() if k not in have]
if add:
    if not text.endswith('\n'):
        text += '\n'
    text += '\n'.join(add) + '\n'
    tmp = TSV + '.tmp_pdf'
    open(tmp, 'w').write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, TSV)
print('rows added', len(add))

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_peasantdf_claude', '# <<< mm9_peasantdf_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 dwarf townswomen PeasantDF1-4 (level_generation/creatures/mm9_peasantdf_claude): MM9's four models are one mesh with
# different paint, so ONE Meshy body (design 1) on the MM9 dwarf female townsfolk skeleton (53 nodes: skirt ring Bone22 with
# eight hem chains, hair-side chains LF/RF_tail) with the whole PEASANTFEMALEDWARF library (stand, walk, run, conv1, fidget2-4,
# hattack Rattack 0.608 s, wince, die1), five-finger MPFB hands, mirrored to MM9's true handedness; one GLB per MM9 model
# (mm9_peasantdf1..4: the same mesh and clips, each with its own body + head paint), the model's two skins as tiers by
# region mask + ramps. NPCbase / shopkeeper / Bankorb scripts play no named clip (the library has no cower).
"""
for k, v in sorted(rows.items(), key=lambda kv: int(kv[0])):
    legacy, role, name, d, skin, mm9skin, dat = v
    BLOCK += f"""# {role} ({k}, {name}, {mm9skin}, DAT {dat})
- descriptor: MM9 {k} {role}
  model: worlds/mm9/models/mm9_peasantdf{d[1]}.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: STRIDE_WALK
    run_stride_length: STRIDE_RUN
    upper_body_root: Bip01 Spine1
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 0.608}}
      attack_ranged: {{impact: 0.608}}
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
    fidget2: Fidget
    fidget3: Fidget2
    fidget4: Fidget3
    stand: Standing
  skin: {skin}
"""
BLOCK += END + '\n'
BLOCK = BLOCK.replace('STRIDE_WALK', os.environ.get('STRIDE_WALK', '0.35')).replace('STRIDE_RUN', os.environ.get('STRIDE_RUN', '0.55'))
if not s.endswith('\n'):
    s += '\n'
s += BLOCK
tmp = p + '.tmp_pdf'
open(tmp, 'w').write(s)
os.chmod(tmp, 0o644)
os.replace(tmp, p)
print('BOUND', sorted(rows))
