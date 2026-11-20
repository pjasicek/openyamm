#!/usr/bin/env python3
"""Set columns of PeasantF5's row (30) in the "MM9 reduction" ledger. Run under the shared flock:
flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_status.py work/ledger_cols.json
JSON keys: after, lods, status, project, rollback (any subset). Re-reads the file, edits only row 30, temp file + rename."""
import json
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
KEY = '| 30 | 2 town/animal | Peasant woman (PeasantF5) |'
cols = json.loads(Path(sys.argv[1]).read_text())
lines = P.read_text().split('\n')
hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, hit
parts = lines[hit[0]].split('|')
# ['', ' 30 ', ' 2 town/animal ', ' Model ', ' File ', ' Before ', ' After ', ' LODs ', ' Status ', ' Project ', ' Rollback ', '']
assert len(parts) == 12, len(parts)
idx = {'after': 6, 'lods': 7, 'status': 8, 'project': 9, 'rollback': 10}
for k, v in cols.items():
    assert '|' not in v and '\n' not in v
    parts[idx[k]] = ' ' + v + ' '
lines[hit[0]] = '|'.join(parts)
tmp = P.with_suffix('.md.tmp_peasantf5'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 30 written')
