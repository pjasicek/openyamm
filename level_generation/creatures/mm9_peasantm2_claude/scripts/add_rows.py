#!/usr/bin/env python3
"""Append PeasantM2's rows to tools/mm9_import_discovery/mm9_npc_actor_rows.tsv (run under the mm9_actors_yml flock, repo root; temp +
rename). Rows already present are left alone."""
import os, tempfile
from pathlib import Path
P = Path('tools/mm9_import_discovery/mm9_npc_actor_rows.tsv')
ROWS = {44: '44\t359\tCommoner, Peasant Human1 MaleA B (PeasantM2 body, PeasantM2b skin): DAT class CommonerHuman1MaleB; 3D model mm9_peasantm2, tier pm2_b',
        50: '50\t367\tCommoner, Peasant Human2 MaleA A (PeasantM2 body, PeasantM2a skin): DAT class CommonerHuman2MaleA; 3D model mm9_peasantm2, tier pm2_a'}
s = P.read_text(); have = {int(l.split('\t')[0]) for l in s.splitlines()[1:] if l.strip()}
add = [ROWS[k] for k in ROWS if k not in have]
if not s.endswith('\n'): s += '\n'
s += ''.join(r + '\n' for r in add)
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.rows_', suffix='.tsv')
with os.fdopen(fd, 'w') as f: f.write(s)
os.chmod(tmp, 0o644); os.replace(tmp, P)
print('ROWS added', [r.split('\t')[0] for r in add], 'present before', sorted(k for k in ROWS if k in have))
