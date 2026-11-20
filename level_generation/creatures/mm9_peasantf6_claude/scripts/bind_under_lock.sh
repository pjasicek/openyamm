#!/bin/bash
# Under the shared flock: add rows 17 and 19 to mm9_npc_actor_rows.tsv (re-read inside the lock; only if missing), regenerate the MM9
# tables, bind the descriptors in actors.yml. Repo root:
#   flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock level_generation/creatures/mm9_peasantf6_claude/scripts/bind_under_lock.sh
set -euo pipefail
T=tools/mm9_import_discovery/mm9_npc_actor_rows.tsv
P=level_generation/creatures/mm9_peasantf6_claude
python3 - "$T" <<'PY'
import os, sys, tempfile
t = sys.argv[1]
text = open(t).read()
have = {l.split('\t')[0] for l in text.splitlines() if l.strip()}
rows = [('17', '334', 'Town, Peasant Elf FemaleB A (PeasantF6 body = PeasantF5 + hair bob, braid and elf ears, PeasantF6a skin): DAT class TownElfFemaleA; 3D model mm9_peasantf6, tier pf6_a'),
        ('19', '337', 'Shopkeeper, Peasant Elf FemaleC A (PeasantF6 body, PeasantF6b skin): DAT class ShopkeeperElfFemaleA; 3D model mm9_peasantf6, tier pf6_b')]
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
python3 $P/scripts/bind_actors.py $P/scripts/binding.yml "MM9 17 Town" "MM9 19 Shopkeeper"
