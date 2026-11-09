#!/usr/bin/env python3
"""Set PeasantF8's row (41) of the "MM9 reduction" ledger from a JSON file {col_index: text}: re-read inside the shared flock, split the
row on '|', replace the given columns, write a temp file and rename. Run as
flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row41.py work/row41.json"""
import json
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
PRE = '| 41 | 2 town/animal | Peasant elf woman (PeasantF8) |'
vals = json.loads(Path(sys.argv[1]).read_text())
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(PRE)]
assert len(hit) == 1, hit
c = lines[hit[0]].split('|')
assert len(c) == 12 and c[4].strip() == '`mm9_peasantf8.glb`', c
for k, v in vals.items():
    assert '\n' not in v and '|' not in v
    c[int(k)] = ' ' + v + ' '
lines[hit[0]] = '|'.join(c)
tmp = P.with_suffix('.md.tmp_peasantf8'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 41 written')
