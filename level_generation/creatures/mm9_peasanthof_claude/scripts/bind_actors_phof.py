#!/usr/bin/env python3
"""Bind the four PeasantHOF rows (MONSTERS.txt 61-64) in assets_dev/worlds/mm9/models/actors.yml and add them to
tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (re-read inside the lock, temp + rename). Run from the repo root under
the flock, then the body overrides and the table generator:
  flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock bash -c 'python3
  level_generation/creatures/mm9_peasanthof_claude/scripts/bind_actors_phof.py && python3
  tools/mm9_import_discovery/mm9_monster_bodies.py --write-overrides && python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py'
Only models whose GLB is installed are bound (MODELS env, default 1,2)."""
import os

TSV = 'tools/mm9_import_discovery/mm9_npc_actor_rows.tsv'
# row: (legacy stand-in from mm9_npc_legacy_replacements.tsv, role, MONSTERS name, design, skin/tier, DAT class)
ROWS = {
    '61': ('430', 'Commoner', 'Peasant Half-Orc Female A', '1', 'phof1_a', 'PeasantHOF1a', 'CommonerHalfOrcFemaleA'),
    '62': ('433', 'Town', 'Peasant Half-Orc Female B', '1', 'phof1_a', 'PeasantHOF1a', 'no placed object'),
    '63': ('436', 'Shopkeeper', 'Peasant Half-Orc Female C', '1', 'phof1_b', 'PeasantHOF1b', 'ShopKeeperHalfOrcFemaleA'),
    '64': ('438', 'Prisoner', 'Peasant Half-Orc Female D', '2', 'phof2_c', 'PeasantHOF1c', 'no placed object'),
}
DESIGNS = os.environ.get('MODELS', '1,2').split(',')
rows = {k: v for k, v in ROWS.items() if v[3] in DESIGNS}
text = open(TSV).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
add = [f'{k}\t{v[0]}\t{v[1]}, {v[2]} (PeasantHOF{v[3]} body, {v[5]} skin): DAT class {v[6]}; 3D model mm9_peasanthof{v[3]}, tier {v[4]}'
       for k, v in rows.items() if k not in have]
if add:
    if not text.endswith('\n'):
        text += '\n'
    text += '\n'.join(add) + '\n'
    tmp = TSV + '.tmp_phof'
    open(tmp, 'w').write(text)
    os.chmod(tmp, 0o644)
    os.replace(tmp, TSV)
print('rows added', len(add))

p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN, END = '# >>> mm9_peasanthof_claude', '# <<< mm9_peasanthof_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 half-orc townswomen PeasantHOF1 / PeasantHOF2 (level_generation/creatures/mm9_peasanthof_claude): ONE Meshy body on MM9's
# half-orc female townsfolk skeleton (86 nodes: skirt chains on XCOM_skirt, braid chains, Ponytail) with the PEASANTHOFEMALE
# library (stand, walk, run, conv1, fidget1-3, hattack1 blow 0.5 s, wince1, die1, cowerloop), five-finger MPFB hands,
# mirrored to MM9's true handedness. mm9_peasanthof1: tiers phof1_a (PeasantHOF1a) and phof1_b (PeasantHOF1b: recoloured
# bodice/skirt, her own head paint); mm9_peasanthof2: the same body reshaped as MM9's HOF2 (floor-length dress, kerchief),
# its own paint, tier phof2_c (PeasantHOF1c). NPCbase plays Cower (BaseRun.inc LoopAnim); shopkeeper/NPC141 scripts play none.
"""
for k, v in sorted(rows.items(), key=lambda kv: int(kv[0])):
    legacy, role, name, d, skin, mm9skin, dat = v
    BLOCK += f"""# {role} ({k}, {name}, {mm9skin}, DAT {dat})
- descriptor: MM9 {k} {role}
  model: worlds/mm9/models/mm9_peasanthof{d}.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: STRIDE_WALK
    run_stride_length: STRIDE_RUN
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 0.5}}
      attack_ranged: {{impact: 0.5}}
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
    cower: Cower
    cowerloop: Cower
    fidget1: Fidget
    fidget2: Fidget2
    fidget3: Fidget3
    stand: Standing
  skin: {skin}
"""
BLOCK += END + '\n'
BLOCK = BLOCK.replace('STRIDE_WALK', os.environ.get('STRIDE_WALK', '1.34')).replace('STRIDE_RUN', os.environ.get('STRIDE_RUN', '2.5'))
if not s.endswith('\n'):
    s += '\n'
s += BLOCK
tmp = p + '.tmp_phof'
open(tmp, 'w').write(s)
os.chmod(tmp, 0o644)
os.replace(tmp, p)
print('BOUND', sorted(rows))
