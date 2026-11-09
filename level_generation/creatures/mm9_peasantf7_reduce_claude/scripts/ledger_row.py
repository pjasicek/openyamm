#!/usr/bin/env python3
"""Replace PeasantF7's row (11) of the "MM9 reduction" ledger with the row text in work/ledger_row.txt; run under the shared flock
(flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py). Re-reads the file, edits only the line
starting with '| 11 | 2 town/animal | Peasant woman with long hair (PeasantF7) |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
P = HERE.parent / 'REDUCTION_LEDGER.md'
KEY = '| 11 | 2 town/animal | Peasant woman with long hair (PeasantF7) |'
ROW = (HERE / 'work' / 'ledger_row.txt').read_text().strip()
assert ROW.startswith(KEY), ROW[:80]
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 11 updated')
