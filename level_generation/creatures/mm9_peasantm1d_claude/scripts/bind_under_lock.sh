#!/bin/bash
# Under the shared flock: add rows 22 and 28 to mm9_npc_actor_rows.tsv (re-read inside the lock; only if missing),
# regenerate the MM9 tables, bind the descriptors in actors.yml. Repo root.
set -euo pipefail
T=tools/mm9_import_discovery/mm9_npc_actor_rows.tsv
P=level_generation/creatures/mm9_peasantm1d_claude
python3 - "$T" <<'PY'
import os, sys, tempfile
t = sys.argv[1]
text = open(t).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
add = []
if '22' not in have:
    add.append('22\t340\tCommoner, Peasant Elf MaleA A (PeasantM1d body, PeasantM1c skin): DAT class CommonerElfMaleA; 3D model mm9_pm1d, tier pm1d_c')
if '28' not in have:
    add.append('28\t342\tPrisoner, Peasant Elf MaleD A (PeasantM1d body, PeasantM1d skin): no DAT placement found in the rebuilt maps; 3D model mm9_pm1d, tier pm1d_d')
if add:
    if not text.endswith('\n'): text += '\n'
    text += '\n'.join(add) + '\n'
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(t), prefix='.npc_rows.', suffix='.tsv')
    with os.fdopen(fd, 'w') as f: f.write(text)
    os.chmod(tmp, 0o644); os.replace(tmp, t)
print('rows added', len(add))
PY
python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py 2>&1 | tail -3
python3 $P/scripts/bind_actors.py $P/scripts/binding.yml "MM9 22 Commoner" "MM9 28 Prisoner"
