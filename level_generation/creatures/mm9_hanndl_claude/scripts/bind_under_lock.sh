#!/bin/bash
# Under the shared flock (flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock <this script>): add row 260 to
# mm9_npc_actor_rows.tsv (re-read inside the lock; only if missing), regenerate the MM9 tables, bind "MM9 260 Hanndl". Repo root.
set -euo pipefail
T=tools/mm9_import_discovery/mm9_npc_actor_rows.tsv
P=level_generation/creatures/mm9_hanndl_claude
python3 - "$T" <<'PY'
import os, sys, tempfile
t = sys.argv[1]
text = open(t).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
add = []
if '260' not in have:
    add.append('260\t555\tHanndl the Gate Keeper (PeasantM6 body without the bell cuffs = Hanndl.abc, Hanndl skin); Arslegard City, the Great Gate, the Hall of the Gods; 3D model mm9_hanndl')
if add:
    if not text.endswith('\n'): text += '\n'
    text += '\n'.join(add) + '\n'
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(t), prefix='.npc_rows.', suffix='.tsv')
    with os.fdopen(fd, 'w') as f: f.write(text)
    os.chmod(tmp, 0o644); os.replace(tmp, t)
print('rows added', len(add))
PY
python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py 2>&1 | tail -3
python3 $P/scripts/bind_actors.py $P/scripts/binding.yml "MM9 260 Hanndl"
