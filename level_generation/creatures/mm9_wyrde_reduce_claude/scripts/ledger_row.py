#!/usr/bin/env python3
"""Set columns of the Wyrdes' row (10) of the "MM9 reduction" ledger. Run under the shared flock:
flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py work/ledger_cols.json
The JSON maps column index (0 = '#', 5 = After, 6 = LODs, 7 = Status, 8 = Project, 9 = Rollback) to text.
Re-reads the file, splits on '|', edits only the row whose '#' is 10 and file is mm9_wyrde.glb, temp file + os.replace."""
import json
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
cols = {int(k): v for k, v in json.loads(Path(sys.argv[1]).read_text()).items()}
lines = P.read_text().split('\n')
hit = [i for i, l in enumerate(lines) if l.startswith('|') and len(l.split('|')) > 5
       and l.split('|')[1].strip() == '10' and 'mm9_wyrde.glb' in l.split('|')[4]]
assert len(hit) == 1, hit
parts = lines[hit[0]].split('|')
for k, v in cols.items():
    parts[k + 1] = ' ' + v + ' '
lines[hit[0]] = '|'.join(parts)
tmp = P.with_suffix('.md.tmp_wyrde'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print(lines[hit[0]])
