#!/bin/bash
# Under the shared flock: add row 59 to mm9_npc_actor_rows.tsv (re-read inside the lock; only if missing), regenerate the MM9
# tables, bind the descriptor in actors.yml. Repo root:
#   flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock level_generation/creatures/mm9_peasanthom2_claude/scripts/bind_under_lock.sh
set -euo pipefail
T=tools/mm9_import_discovery/mm9_npc_actor_rows.tsv
P=level_generation/creatures/mm9_peasanthom2_claude
python3 - "$T" <<'PY'
import os, sys, tempfile
t = sys.argv[1]
text = open(t).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
rows = [('59', '445', 'Shopkeeper, Peasant Half-Orc Male C (PeasantHOM2 body = PeasantHOM1 mesh, PeasantHOM2a skin): DAT class ShopkeeperHalfOrcMaleC not placed (the one half-orc shopkeeper object is ShopKeeperHalfOrcMaleA); 3D model mm9_phom1, tier phom2_a')]
add = ['\t'.join(r) for r in rows if r[0] not in have]
if add:
    if not text.endswith('\n'): text += '\n'
    text += '\n'.join(add) + '\n'
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(t), prefix='.npc_rows.', suffix='.tsv')
    with os.fdopen(fd, 'w') as f: f.write(text)
    os.chmod(tmp, 0o644); os.replace(tmp, t)
print('rows added', len(add))
PY
python3 tools/mm9_import_discovery/generate_mm9_monster_tables.py 2>&1 | tail -3
python3 $P/scripts/bind_actors.py $P/scripts/binding.yml "MM9 59 Shopkeeper"
