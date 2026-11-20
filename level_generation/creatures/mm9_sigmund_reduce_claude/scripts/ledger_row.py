#!/usr/bin/env python3
"""Replace Sigmund's row (27) of the "MM9 reduction" ledger; run under the shared flock
(flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py work/ledger_row.txt). Re-reads the file
inside the lock, edits only the line whose first columns (split on '|') are 27 / Sigmund the Stressed, temp file + os.replace."""
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = Path(sys.argv[1]).read_text().strip()
assert '\n' not in ROW


def key(line):
    c = line.split('|')
    return (c[1].strip(), c[3].strip(), c[4].strip()) if len(c) > 5 else None


K = ('27', 'Sigmund the Stressed', '`mm9_sigmund.glb`')
assert key(ROW) == K, key(ROW)
lines = P.read_text().split('\n')
hit = [i for i, l in enumerate(lines) if l.startswith('|') and key(l) == K]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
tmp = P.with_suffix('.md.tmp_sigmund')
tmp.write_text('\n'.join(lines))
os.replace(tmp, P)
print('ROW 27 written')
