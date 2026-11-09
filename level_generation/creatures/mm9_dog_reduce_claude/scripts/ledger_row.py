#!/usr/bin/env python3
"""Edit the Dog row (83) of the "MM9 reduction" ledger; run under the shared flock
(flock level_generation/creatures/claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py ...).
Re-reads the file, splits the one row on '|', sets the named columns, writes a temp file and renames it.
Usage: ledger_row.py --after TEXT --lods TEXT --status TEXT --project TEXT --rollback TEXT (any subset)."""
import argparse, os, tempfile
from pathlib import Path
L = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
KEY = '| 91 | 2 town/animal | Dog |'
COLS = {'after': 6, 'lods': 7, 'status': 8, 'project': 9, 'rollback': 10}
ap = argparse.ArgumentParser()
for k in COLS:
    ap.add_argument('--' + k)
a = ap.parse_args()
lines = L.read_text().split('\n')
hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, hit
cells = lines[hit[0]].split('|')
assert len(cells) == 12, (len(cells), cells)
for k, c in COLS.items():
    v = getattr(a, k)
    if v is not None:
        assert '|' not in v
        cells[c] = ' ' + v + ' '
lines[hit[0]] = '|'.join(cells)
fd, tmp = tempfile.mkstemp(dir=L.parent, prefix='.ledger_')
os.write(fd, '\n'.join(lines).encode())
os.close(fd)
os.chmod(tmp, 0o644)
os.replace(tmp, L)
print('ROW:', lines[hit[0]][:300])
