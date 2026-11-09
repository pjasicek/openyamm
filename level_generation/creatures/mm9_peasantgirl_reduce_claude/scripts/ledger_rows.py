#!/usr/bin/env python3
"""Set the status (and optionally After / LODs / Project / Rollback) of the peasant-girl rows (15, 20) of the
"MM9 reduction" ledger. Run under the shared flock:
  flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_rows.py work/ledger_rows.json
JSON: {"15": {"after": "...", "lods": "...", "status": "...", "project": "...", "rollback": "..."}, "20": {...}}
Re-reads the file, edits only rows 15 and 20 (columns split on '|'), writes a temp file and renames."""
import json
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
upd = json.loads(Path(sys.argv[1]).read_text())
FILES = {'15': '`mm9_peasantgirl1e.glb`', '20': '`mm9_peasantgirl.glb`'}
lines = P.read_text().split('\n')
for num, u in upd.items():
    hit = [i for i, l in enumerate(lines) if l.startswith(f'| {num} | 2 town/animal | Peasant girls')]
    assert len(hit) == 1, (num, hit)
    cols = lines[hit[0]].split('|')
    # ['', ' 15 ', ' 2 town/animal ', ' model ', ' file ', ' before ', ' after ', ' lods ', ' status ', ' project ', ' rollback ', '']
    assert len(cols) == 12 and cols[4].strip() == FILES[num], cols
    for key, idx in (('after', 6), ('lods', 7), ('status', 8), ('project', 9), ('rollback', 10)):
        if key in u:
            cols[idx] = ' ' + u[key] + ' ' if u[key] else ' '
    lines[hit[0]] = '|'.join(cols)
    print(lines[hit[0]])
tmp = P.with_suffix('.md.tmp_peasantgirl'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P)
