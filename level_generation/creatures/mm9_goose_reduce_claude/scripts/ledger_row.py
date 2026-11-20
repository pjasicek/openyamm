#!/usr/bin/env python3
"""Edit one row of the "MM9 reduction" ledger; run under the shared flock
(flock level_generation/creatures/claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py --key '| 95 |' ...).
Re-reads the file, splits the one row on '|', sets the named columns, writes a temp file and renames it."""
import argparse, os, tempfile
from pathlib import Path
L = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
COLS = {'after': 6, 'lods': 7, 'status': 8, 'project': 9, 'rollback': 10}
ap = argparse.ArgumentParser(); ap.add_argument('--key', required=True); ap.add_argument('--model', required=True)
for k in COLS:
    ap.add_argument('--' + k)
a = ap.parse_args()
lines = L.read_text().split('\n')
hit = [i for i, l in enumerate(lines) if l.startswith(a.key) and f'`{a.model}`' in l]
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
os.write(fd, '\n'.join(lines).encode()); os.close(fd); os.chmod(tmp, 0o644); os.replace(tmp, L)
print('ROW:', lines[hit[0]][:400])
