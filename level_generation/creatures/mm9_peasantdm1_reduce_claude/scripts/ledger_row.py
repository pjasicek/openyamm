#!/usr/bin/env python3
"""Set columns of the PeasantDM1 row (86) of the "MM9 reduction" ledger. Run under the shared flock:
flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py 'after=..' 'lods=..' 'status=..' 'project=..' 'rollback=..'
Re-reads the file inside the lock, splits columns on '|', edits only row 86, temp file + os.replace."""
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
COL = {'after': 6, 'lods': 7, 'status': 8, 'project': 9, 'rollback': 10}
lines = P.read_text().split('\n')
hit = [i for i, l in enumerate(lines) if len(l.split('|')) > 5 and l.split('|')[1].strip() == '86'
       and 'mm9_peasantdm1.glb' in l.split('|')[4]]
assert len(hit) == 1, hit
cells = lines[hit[0]].split('|')
for arg in sys.argv[1:]:
    k, v = arg.split('=', 1)
    cells[COL[k]] = ' ' + v + ' ' if v else ' '
lines[hit[0]] = '|'.join(cells)
tmp = P.with_suffix('.md.tmp_peasantdm1'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P)
print(lines[hit[0]])
