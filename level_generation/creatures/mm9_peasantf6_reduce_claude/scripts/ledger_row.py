#!/usr/bin/env python3
"""Update PeasantF6's row (12) of the "MM9 reduction" ledger; run under the shared flock
(flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py work/ledger_cols.json). Re-reads the file,
finds the one line whose 2nd/5th columns are '12' and '`mm9_peasantf6.glb`' (columns split on '|'), replaces the After, LODs,
Status, Project and Rollback columns from the JSON, writes a temp file and renames."""
import json
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
NEW = json.loads(Path(sys.argv[1]).read_text())
lines = P.read_text().split('\n')
hit = [i for i, l in enumerate(lines) if l.startswith('|') and len(l.split('|')) >= 12
       and l.split('|')[1].strip() == '12' and l.split('|')[4].strip() == '`mm9_peasantf6.glb`']
assert len(hit) == 1, hit
c = lines[hit[0]].split('|')
for k, idx in (('after', 6), ('lods', 7), ('status', 8), ('project', 9), ('rollback', 10)):
    if k in NEW:
        assert '|' not in NEW[k] and '\n' not in NEW[k]
        c[idx] = f' {NEW[k]} '
lines[hit[0]] = '|'.join(c)
tmp = P.with_suffix('.md.tmp_peasantf6'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 12 written')
