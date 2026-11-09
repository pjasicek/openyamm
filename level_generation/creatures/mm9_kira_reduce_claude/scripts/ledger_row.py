#!/usr/bin/env python3
"""Set Kira's MM9 reduction ledger row (row 1, `mm9_kira.glb`) columns After / LODs / Status. Run under
flock ../claude_shared/locks/reduction_ledger.lock (re-reads the file inside the lock; temp file + os.replace).
Usage: ledger_row.py '<after>' '<lods>' '<status>'"""
import os
import sys
import tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
lines = P.read_text().split('\n')
hits = [i for i, l in enumerate(lines) if '| Kira the Cold | `mm9_kira.glb`' in l]
assert len(hits) == 1, hits
c = lines[hits[0]].split('|')
assert c[1].strip() == '1' and '`mm9_kira.glb`' in c[4]
c[6], c[7], c[8] = (f' {x} ' for x in sys.argv[1:4])
lines[hits[0]] = '|'.join(c)
fd, tmp = tempfile.mkstemp(dir=P.parent); os.write(fd, '\n'.join(lines).encode()); os.close(fd); os.chmod(tmp, 0o664); os.replace(tmp, P)
print(lines[hits[0]])
