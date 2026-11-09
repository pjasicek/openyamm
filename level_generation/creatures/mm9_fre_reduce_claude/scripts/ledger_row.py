#!/usr/bin/env python3
"""Replace Fre's row (113) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only the line
whose first column is 113 (columns split on '|'), writes a temp file and renames it. Usage: ledger_row.py <row-text-file>"""
import os, sys, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = Path(sys.argv[1]).read_text().strip()
lines = P.read_text().split('\n')
hit = [i for i, l in enumerate(lines) if l.startswith('|') and l.split('|')[1].strip() == '113' and 'mm9_fre.glb' in l]
assert len(hit) == 1, hit
assert ROW.split('|')[1].strip() == '113'
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 113 updated')
