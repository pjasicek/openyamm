#!/usr/bin/env python3
"""Set Skraelos' MM9 reduction ledger row (row 29, `mm9_skraelos.glb`) columns After / LODs / Status / Project /
Rollback. Run under flock ../claude_shared/locks/reduction_ledger.lock (re-reads the file inside the lock; temp file +
os.replace). Usage: ledger_row.py '<after>' '<lods>' '<status>' ['<project>' '<rollback>']"""
import os
import sys
import tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
lines = P.read_text().split('\n')
hits = [i for i, l in enumerate(lines) if '| Skraelos (row 257)' in l and '`mm9_skraelos.glb`' in l]
assert len(hits) == 1, hits
c = lines[hits[0]].split('|')
assert c[1].strip() == '29' and '`mm9_skraelos.glb`' in c[4], c
vals = sys.argv[1:]
for k, v in zip((6, 7, 8, 9, 10), vals):
    c[k] = f' {v} '
lines[hits[0]] = '|'.join(c)
fd, tmp = tempfile.mkstemp(dir=P.parent); os.write(fd, '\n'.join(lines).encode()); os.close(fd); os.chmod(tmp, 0o664); os.replace(tmp, P)
print(lines[hits[0]])
