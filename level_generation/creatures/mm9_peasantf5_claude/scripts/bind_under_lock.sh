#!/bin/bash
# Under the shared flock: add rows 34, 36 and 41 to mm9_npc_actor_rows.tsv (re-read inside the lock; only if missing), regenerate the MM9
# tables, write the actors.yml block mm9_peasantf5_claude (replaced if present). Repo root:
#   flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock level_generation/creatures/mm9_peasantf5_claude/scripts/bind_under_lock.sh
set -euo pipefail
T=tools/mm9_import_discovery/mm9_npc_actor_rows.tsv
python3 - "$T" <<'PY'
import os, sys, tempfile
t = sys.argv[1]
text = open(t).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
rows = {
    '34': '34\t356\tShopkeeper, Peasant Human1 FemaleC B (PeasantF5 body, PeasantF5a skin): DAT class ShopkeeperHuman1FemaleB, no placement in the rebuilt maps; 3D model mm9_peasantf5, tier pf5_a',
    '36': '36\t376\tCommoner, Peasant Human2 FemaleA A (PeasantF5 body, PeasantF5b skin): DAT class CommonerHuman2FemaleA; 3D model mm9_peasantf5, tier pf5_b',
    '41': '41\t383\tShopkeeper, Peasant Human2 FemaleC B (PeasantF5 body, PeasantF5a skin): DAT class ShopkeeperHuman2FemaleB, no placement in the rebuilt maps; 3D model mm9_peasantf5, tier pf5_a',
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
grep -P "^(9034|9036|9041)\t" assets_dev/worlds/mm9/data_tables/monster_descriptors.txt | cut -f1-2
python3 - <<'PY'
import os
p = 'assets_dev/worlds/mm9/models/actors.yml'
s = open(p).read()
BEGIN = '# >>> mm9_peasantf5_claude'; END = '# <<< mm9_peasantf5_claude'
if BEGIN in s:
    a = s.index(BEGIN); b = s.index(END) + len(END) + 1; s = s[:a] + s[b:]
BLOCK = BEGIN + """
# MM9 PeasantF5 body (level_generation/creatures/mm9_peasantf5_claude): the human townswoman in a pointed coif. Meshy body on PEASANTF5.abc's
# human female skeleton (73 joints, skirt chains keyed as MM9 keys them, 15 finger bones per side on MPFB hands under procedural bracelets), the
# MM9 PeasantFemale clip library, whole model mirrored to true handedness. One body paint with region ramps (pinafore, skirt), a head colour per
# tier (the two skins are two women). Clips MM9's scripts play: NPCbase.scr (Converse -> conv1-3, BaseRun LoopAnim Cower); NPC92/181/182,
# Shopkeeper.scr and retainer.scr play no animation. No attack clip in the library: attacks play Fidget (peasants flee).
"""
for row, role, skin, label in (('36', 'Commoner', 'pf5_b', 'Commoner, Peasant Human2 FemaleA A (row 36, skin PeasantF5b, DAT CommonerHuman2FemaleA)'),
                               ('34', 'Shopkeeper', 'pf5_a', 'Shopkeeper, Peasant Human1 FemaleC B (row 34, skin PeasantF5a, no placement)'),
                               ('41', 'Shopkeeper', 'pf5_a', 'Shopkeeper, Peasant Human2 FemaleC B (row 41, skin PeasantF5a, no placement)')):
    BLOCK += f"""# {label}
- descriptor: MM9 {row} {role}
  model: worlds/mm9/models/mm9_peasantf5.glb
  scale: 100.0
  yaw_offset: -1.570796327
  animation:
    run: Running
    stride_length: 1.0
    run_stride_length: 1.6
    look: {{nodes: [FHP Neck, FHP Head], max_yaw_degrees: 60, max_pitch_degrees: 35}}
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
    cower: Cower
    conv1: Conv1
    conv2: Talk
    conv3: Conv3
    stand: Standing
  skin: {skin}
"""
BLOCK += END + '\n'
tmp = p + '.tmp_pf5'
open(tmp, 'w').write(s.rstrip('\n') + '\n' + BLOCK)
os.chmod(tmp, os.stat(p).st_mode & 0o777)
os.replace(tmp, p)
print('bound MM9 36 Commoner, MM9 34 Shopkeeper, MM9 41 Shopkeeper')
PY
