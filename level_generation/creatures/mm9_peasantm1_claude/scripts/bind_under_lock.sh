#!/bin/bash
# Under the shared flock: add rows 43, 56 and 296 to mm9_npc_actor_rows.tsv (re-read inside the lock; only if missing),
# regenerate the MM9 tables, bind the descriptors in actors.yml. Repo root:
#   flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock level_generation/creatures/mm9_peasantm1_claude/scripts/bind_under_lock.sh
set -euo pipefail
T=tools/mm9_import_discovery/mm9_npc_actor_rows.tsv
P=level_generation/creatures/mm9_peasantm1_claude
python3 - "$T" <<'PY'
import os, sys, tempfile
t = sys.argv[1]
text = open(t).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
rows = {
    '43': '43\t358\tCommoner, Peasant Human1 MaleA A (PeasantM1 body, PeasantM1a skin): DAT class CommonerHumanMaleA; 3D model mm9_peasantm1, tier pm1_a',
    '56': '56\t375\tPrisoner, Peasant Human2 MaleD A (PeasantM1 body, PeasantM1b skin): no DAT placement found in the rebuilt maps; 3D model mm9_peasantm1, tier pm1_b',
    '296': '296\t358\tRailTest (PeasantM1 body, PeasantM1a skin, Princess.scr): test row, no placement; 3D model mm9_peasantm1, tier pm1_a',
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
grep -P "^(9043|9056|9296)\t" assets_dev/worlds/mm9/data_tables/monster_descriptors.txt | cut -f1-2
python3 $P/scripts/bind_actors.py $P/scripts/binding.yml "MM9 43 Commoner" "MM9 56 Prisoner" "MM9 296 RailTest"
