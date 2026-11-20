#!/usr/bin/env python3
"""Bind the human boy family (rows 69, 70, 73) in assets_dev/worlds/mm9/models/actors.yml and add the rows to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (re-read inside the lock, temp + rename). Run from the repo root under
the flock, then the table generator:
  flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
  level_generation/creatures/mm9_peasantboy_claude/scripts/bind_actors.py && python3
  tools/mm9_import_discovery/generate_mm9_monster_tables.py'"""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '69': '69\t166\tCommoner Child, Peasant Human Child A (PeasantBoy1 body, PeasantBoy1 skin): DAT class CommonerChildHumanChildA; 3D model mm9_peasantboy, tier pboy_a',
    '70': '70\t167\tTownsfolk Child, Peasant Human Child B (PeasantBoy2 = PeasantBoy1 body, PeasantBoy3 skin): no placed DAT object; 3D model mm9_peasantboy, tier pboy_b',
    '73': '73\t340\tCommoner Child, Peasant Elf Child A (PeasantBoy1e = PeasantBoy1 body + elf ears, PeasantBoy2 skin): DAT class CommonerChildElfChildA; 3D model mm9_peasantboy, tier pboy_e + attachment mm9_peasantboy_elfears',
}
text = open(TSV).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
add = [v for k, v in ROWS.items() if k not in have]
if add:
    if not text.endswith('\n'):
        text += '\n'
    text += '\n'.join(add) + '\n'
    tmp = TSV + '.tmp_pboy'
    open(tmp, 'w').write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, TSV)
print('rows added', len(add))

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_peasantboy_claude', '# <<< mm9_peasantboy_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 human boy family (level_generation/creatures/mm9_peasantboy_claude): one Meshy body on MM9's child-boy skeleton
# (PEASANTBOY1/2/1E share it; 30 joints plus a static Bip01 L Hand: MM9's left fingers hang off the forearm) with the
# PEASANTCHILDBOY library clips the child scripts play (NPCbase wander/converse/cower, YanmirChild follow and run;
# hattack1 Rattack 0.7 s), five-finger MPFB hands, mirrored to MM9's true handedness. Tiers: one body paint with region
# mask and ramps (vest, sleeves, trousers, belt) and a head colour per boy (three different children). Row 73's elf ears
# (MM9's Boy_1a piece) are an attachment on Bip01 ElfEars, carried by that descriptor only.
"""
for desc, skin, label, ears in (
        ('MM9 69 Commoner Child', 'pboy_a', 'Commoner Child (69, Peasant Human Child A, PeasantBoy1, DAT CommonerChildHumanChildA)', False),
        ('MM9 70 Townsfolk Child', 'pboy_b', 'Townsfolk Child (70, Peasant Human Child B, PeasantBoy2 + skin PeasantBoy3, no placed object)', False),
        ('MM9 73 Commoner Child', 'pboy_e', 'Commoner Child (73, Peasant Elf Child A, PeasantBoy1e + skin PeasantBoy2, DAT CommonerChildElfChildA)', True)):
    BLOCK += f"""# {label}
- descriptor: {desc}
  model: worlds/mm9/models/mm9_peasantboy.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: STRIDE_WALK
    run_stride_length: STRIDE_RUN
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 0.7}}
      attack_ranged: {{impact: 0.7}}
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
    cower: Cower
    stand: Standing
  skin: {skin}
"""
    if ears:
        BLOCK += """  attachments:
    - model: worlds/mm9/models/mm9_peasantboy_elfears.glb
      node: Bip01 ElfEars
"""
BLOCK += END + '\n'
BLOCK = BLOCK.replace('STRIDE_WALK', os.environ.get('STRIDE_WALK', '0.45')).replace('STRIDE_RUN', os.environ.get('STRIDE_RUN', '1.3'))
tmp = p + '.tmp_pboy'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
