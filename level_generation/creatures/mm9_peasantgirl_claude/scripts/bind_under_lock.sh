#!/bin/bash
# Under the shared flock: add rows 71, 72 and 74 to mm9_npc_actor_rows.tsv (re-read inside the lock; only if missing), regenerate the MM9
# tables, write the actors.yml block mm9_peasantgirl_claude (replaced if present). Repo root:
#   flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock level_generation/creatures/mm9_peasantgirl_claude/scripts/bind_under_lock.sh
set -euo pipefail
T=tools/mm9_import_discovery/mm9_npc_actor_rows.tsv
python3 - "$T" <<'PY'
import os, sys, tempfile
t = sys.argv[1]
text = open(t).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
rows = {
    '71': '71\t595\tCommoner Child, Peasant Human2 Child A (PeasantGirl2 body, PeasantGirl2 skin): DAT class CommonerChildHuman2ChildA; 3D model mm9_peasantgirl, tier pg_g2',
    '72': '72\t596\tTownsfolk Child, Peasant Human2 Child B (PeasantGirl3 = PeasantGirl2 body, PeasantGirl3 skin): no placed DAT object; 3D model mm9_peasantgirl, tier pg_g3',
    '74': '74\t331\tTownsfolk Child, Peasant Elf Child B (PeasantGirl1e = PeasantGirl2 body + elf ears, PeasantGirl1 skin): no placed DAT object; 3D model mm9_peasantgirl1e, tier pg_g1e',
}
add = [v for k, v in rows.items() if k not in have]
if add:
    if not text.endswith('\n'): text += '\n'
    text += '\n'.join(add) + '\n'
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(t), prefix='.npc_rows.', suffix='.tsv')
    with os.fdopen(fd, 'w') as f: f.write(text)
    os.chmod(tmp, 0o644); os.replace(tmp, t)
print('rows added', len(add))
PY
python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py 2>&1 | tail -3
grep -P "^(9071|9072|9074)\t" assets_dev/worlds/mm9/data_tables/monster_descriptors.txt | cut -f1-2
python3 - <<'PY'
import os
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN = '# >>> mm9_peasantgirl_claude'; END = '# <<< mm9_peasantgirl_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 human girl family (level_generation/creatures/mm9_peasantgirl_claude): one Meshy body on MM9's child-girl skeleton (PEASANTGIRL2/3/1E
# share it: 60 joints with eight skirt chains, + 15 finger bones per side on MPFB child hands + 5 half-joint helpers), the PEASANTCHILDGIRL
# clip library the child scripts play (NPCbase converse / cower; YanmirChild and NPC312 play none), mirrored to true handedness. One body
# paint with region ramps (dress, vest, skin) and a head colour per girl (three different children). The elf girl (row 74) is the same body
# with procedural elf ears in its own GLB, mm9_peasantgirl1e. No attack clip in the library is used: attacks play Fidget (children flee).
"""
for row, role, model, skin, label in (('71', 'Commoner Child', 'mm9_peasantgirl', 'pg_g2', 'Commoner Child (71, Peasant Human2 Child A, PeasantGirl2, DAT CommonerChildHuman2ChildA)'),
                                      ('72', 'Townsfolk Child', 'mm9_peasantgirl', 'pg_g3', 'Townsfolk Child (72, Peasant Human2 Child B, PeasantGirl3, no placed object)'),
                                      ('74', 'Townsfolk Child', 'mm9_peasantgirl1e', 'pg_g1e', 'Townsfolk Child (74, Peasant Elf Child B, PeasantGirl1e, no placed object)')):
    BLOCK += f"""# {label}
- descriptor: MM9 {row} {role}
  model: worlds/mm9/models/{model}.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 0.62
    run_stride_length: 1.55
    look: {{nodes: [Bip01 Neck, Bip01 Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
    events:
      attack_melee: {{impact: 1.0}}
      attack_ranged: {{impact: 1.0}}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Fidget
    attack_ranged: Fidget
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  script_clips:
    talk: Talk
    conv: Talk
    cower: Cower
    stand: Standing
  skin: {skin}
"""
BLOCK += END + '\n'
tmp = p + '.tmp_pg'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.chmod(tmp, os.stat(p).st_mode & 0o777)
os.replace(tmp, p)
print('bound MM9 71 Commoner Child, MM9 72 Townsfolk Child, MM9 74 Townsfolk Child')
PY
