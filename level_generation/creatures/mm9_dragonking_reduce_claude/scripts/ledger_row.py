#!/usr/bin/env python3
"""Edit only the Dragon King row (35) of the MM9 reduction ledger; run under the shared flock.
Usage: ledger_row.py <after> <lods> <status> [project] [rollback]  (empty string keeps the column)."""
import os, sys, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
lines = P.read_text().split('\n')
hit = [i for i, l in enumerate(lines) if l.startswith('| 35 |') and 'Dragon King' in l and 'mm9_dragonking.glb' in l]
assert len(hit) == 1, hit
cols = lines[hit[0]].split('|')
# cols: '', ' 35 ', prio, name, file, before, after, lods, status, project, rollback, ''
assert len(cols) == 12, len(cols)
for idx, val in zip((6, 7, 8, 9, 10), sys.argv[1:]):
    if val:
        cols[idx] = ' ' + val + ' '
lines[hit[0]] = '|'.join(cols)
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('ledger row 35:', lines[hit[0]][:200])
