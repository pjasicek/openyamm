#!/usr/bin/env python3
"""Bind Krohn (row 255) in assets_dev/worlds/mm9/models/actors.yml and add the row to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (re-read inside the lock, temp + rename). Run from the repo root under
the flock, then the table generator:
  flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
  level_generation/creatures/mm9_krohn_claude/scripts/bind_actors.py && python3
  tools/mm9_import_discovery/generate_mm9_monster_tables.py'"""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
ROWS = {
    '255': '255\t565\tKrohn (KROHN.abc, Krohn skin + KrohnSword/KrohnSpear, own 64-joint Bip01 skeleton): the god in the Hall of the Gods; DAT class Krohn with NPC335.scr (quest, loopanim stand) and WG_NPC335.scr (the win-game cutscene: Krohn01-05, SC7_22_Krohn), the statue prop Krohnstat (PropAnim statue, sculpt skins); legacy Armored Death Knight as the fallback visual; 3D model mm9_krohn',
}
text = open(TSV).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
add = [v for k, v in ROWS.items() if k not in have]
if add:
    if not text.endswith('\n'):
        text += '\n'
    text += '\n'.join(add) + '\n'
    tmp = TSV + '.tmp_kr'
    open(tmp, 'w').write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, TSV)
print('rows added', len(add))

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_krohn_claude', '# <<< mm9_krohn_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 Krohn, the god of the Hall of the Gods (level_generation/creatures/mm9_krohn_claude): Meshy body on KROHN.abc's own
# 64-joint Bip01 skeleton (hair, beard, cape and skirt-flap joints), five-finger MPFB hands, the glaive rigid in the right
# fist (Xspear) and the scabbarded sword on the back (Xsword) in one GLB, mirrored to MM9's true handedness. Row 255 (L1,
# NPCbase.scr, BaseName PeasantMale, Scale 1; a 2.78 m giant), one skin. Clips: KROHN.abc's own (stand, walk, fidget1,
# statue, the cutscene clips WG_NPC335.scr plays: Krohn01-05, SC7_22_Krohn); KROHN.abc has no run, attack, hit or death:
# Running, AttackMelee (hattack1 Rattack 0.5 s), Hit and Death are PeasantMale library clips retargeted (world-rotation copy).
- descriptor: MM9 255 Krohn
  model: worlds/mm9/models/mm9_krohn.glb
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
    statue: Statue
    krohn01: Krohn01
    krohn02: Krohn02
    krohn03: Krohn03
    krohn04: Krohn04
    krohn05: Krohn05
    sc7_22_krohn: SC7_22_Krohn
"""
BLOCK += END + '\n'
BLOCK = BLOCK.replace('STRIDE_WALK', os.environ.get('STRIDE_WALK', '1.55')).replace('STRIDE_RUN', os.environ.get('STRIDE_RUN', '3.6'))
tmp = p + '.tmp_kr'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.replace(tmp, p)
print('bound')
