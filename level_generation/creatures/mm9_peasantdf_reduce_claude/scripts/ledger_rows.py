#!/usr/bin/env python3
"""Edit the peasant dwarf women's rows (17, 23, 24, 25) of the "MM9 reduction" ledger. Run under the shared flock:
flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_rows.py work/ledger_rows.json
The JSON maps row number -> {column index: new text}; columns split on '|' (index 1 = '#'). Re-reads the file inside
the lock, edits only those rows, writes a temp file and renames."""
import json
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
EDITS = json.loads(Path(sys.argv[1]).read_text())
FILES = {'17': 'mm9_peasantdf3.glb', '23': 'mm9_peasantdf1.glb', '24': 'mm9_peasantdf2.glb', '25': 'mm9_peasantdf4.glb'}
lines = P.read_text().split('\n')
start = next(i for i, l in enumerate(lines) if l.startswith('## MM9 reduction'))
for row, cols in EDITS.items():
    assert row in FILES, row
    hit = [i for i in range(start, len(lines)) if lines[i].startswith(f'| {row} | ')]
    assert len(hit) == 1, (row, hit)
    parts = lines[hit[0]].split('|')
    assert FILES[row] in parts[4], (row, parts[4])
    for c, text in cols.items():
        parts[int(c)] = f' {text} '
    lines[hit[0]] = '|'.join(parts)
    print(lines[hit[0]][:300])
tmp = P.with_suffix('.md.tmp_peasantdf'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P)
