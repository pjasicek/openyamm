#!/usr/bin/env python3
"""Set the half-orc women's rows (111 HOF1, 112 HOF2) of the "MM9 reduction" ledger from a JSON file
{"111": {col_index: text}, "112": {...}}: re-read inside the shared flock, split each row on '|', replace the given columns, write a
temp file and rename. Run as
flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_rows.py work/rows.json"""
import json
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
FILES = {'111': '`mm9_peasanthof1.glb`', '112': '`mm9_peasanthof2.glb`'}
vals = json.loads(Path(sys.argv[1]).read_text())
lines = P.read_text().split('\n')
for row, cols in vals.items():
    pre = f'| {row} | 2 town/animal | Half-orc women'
    hit = [i for i, l in enumerate(lines) if l.startswith(pre)]
    assert len(hit) == 1, (row, hit)
    c = lines[hit[0]].split('|')
    assert len(c) == 12 and c[4].strip() == FILES[row], c
    for k, v in cols.items():
        assert '\n' not in v and '|' not in v
        c[int(k)] = ' ' + v + ' '
    lines[hit[0]] = '|'.join(c)
    print('ROW', row, 'written')
tmp = P.with_suffix('.md.tmp_peasanthof'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P)
