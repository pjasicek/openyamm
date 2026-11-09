#!/usr/bin/env python3
"""Set columns of PeasantM3's row (55) of the "MM9 reduction" ledger; run under the shared flock:
flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py work/ledger_cols.json
The JSON maps column index (1-based after the leading '|': 5 After, 6 LODs, 7 Status, 8 Project, 9 Rollback) to text.
Re-reads the file inside the lock, edits only the row whose File column is `mm9_peasantm3.glb`, temp file + os.replace."""
import json
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
cols = {int(k): v for k, v in json.loads(Path(sys.argv[1]).read_text()).items()}
lines = P.read_text().split('\n')
hit = [i for i, l in enumerate(lines) if l.startswith('| 55 |') and '`mm9_peasantm3.glb`' in l]
assert len(hit) == 1, hit
parts = lines[hit[0]].split('|')
assert parts[4].strip() == '`mm9_peasantm3.glb`', parts[4]
for k, v in cols.items():
    assert '|' not in v and '\n' not in v
    parts[k + 1] = ' ' + v + ' '
lines[hit[0]] = '|'.join(parts)
tmp = P.with_suffix('.md.tmp_peasantm3'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print(lines[hit[0]])
