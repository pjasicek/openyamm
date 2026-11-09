#!/usr/bin/env python3
"""Bind the dwarf boy (rows 67, 68) in assets_dev/worlds/mm9/models/actors.yml and add the rows to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (re-read inside the lock, temp + rename). Run from the repo root under
the flock, then the table generator:
  flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
  level_generation/creatures/mm9_peasantdboy_claude/scripts/bind_actors.py && python3
  tools/mm9_import_discovery/generate_mm9_monster_tables.py'"""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '67': '67\t313\tCommoner Child, Peasant Dwarf Child A (PeasantDboy1 body, DwarfBoy1 skin): DAT class CommonerChildDwarfChildA (YanmirChild.scr); 3D model mm9_peasantdboy, tier pdboy_a',
    '68': '68\t322\tTownsfolk Child, Peasant Dwarf Child B (PeasantDboy1 body, DwarfBoy2 skin): no placed DAT object; 3D model mm9_peasantdboy, tier pdboy_b',
}
text = open(TSV).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
add = [v for k, v in ROWS.items() if k not in have]
if add:
    if not text.endswith('\n'):
        text += '\n'
    text += '\n'.join(add) + '\n'
    tmp = TSV + '.tmp_pdboy'
    open(tmp, 'w').write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, TSV)
print('rows added', len(add))

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_peasantdboy_claude', '# <<< mm9_peasantdboy_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 dwarf boy (level_generation/creatures/mm9_peasantdboy_claude): one Meshy body on PEASANTDBOY1.abc's own 38-joint
# skeleton (no child models) with its own clips (stand, walk, run, fidget1, fidget2, Hattack1 Rattack 0.242 s, wince1,
# die1; NPCbase.scr has no conv/cower clip on this model, YanmirChild.scr walks and runs), five-finger MPFB hands,
# mirrored to MM9's true handedness. Tiers: one body paint with region mask and ramps (tunic, embroidered bands,
# trousers, belt) and a head colour per boy (two different children).
"""
for desc, skin, label in (
        ('MM9 67 Commoner Child', 'pdboy_a', 'Commoner Child (67, Peasant Dwarf Child A, PeasantDboy1 + skin DwarfBoy1, DAT CommonerChildDwarfChildA)'),
        ('MM9 68 Townsfolk Child', 'pdboy_b', 'Townsfolk Child (68, Peasant Dwarf Child B, PeasantDboy1 + skin DwarfBoy2, no placed object)')):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_peasantdboy.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: STRIDE_WALK
    run_stride_length: STRIDE_RUN
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 0.242}}
      attack_ranged: {{impact: 0.242}}
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
    run: Running
    fidget1: Fidget
    fidget2: Fidget2
  skin: {skin}
"""
BLOCK += END + '\n'
BLOCK = BLOCK.replace('STRIDE_WALK', os.environ.get('STRIDE_WALK', '0.37')).replace('STRIDE_RUN', os.environ.get('STRIDE_RUN', '0.78'))
tmp = p + '.tmp_pdboy'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
