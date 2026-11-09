#!/usr/bin/env python3
"""Replace the Nosferatu's row in REDUCTION_LEDGER.md (MM9 section). Run under
flock ../claude_shared/locks/reduction_ledger.lock; re-reads the file, edits one row, temp file + rename.
Usage: ledger_row.py '<full row text starting with | 37 | 1 monster | Nosferatu |>'"""
import os, sys, tempfile
from pathlib import Path
path = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
row = sys.argv[1].rstrip('\n')
lines = path.read_text().split('\n')
hits = [i for i, l in enumerate(lines) if l.startswith('| 37 | 1 monster | Nosferatu |') and '`mm9_nosferatu.glb`' in l]
assert len(hits) == 1, hits
assert row.startswith('| 37 | 1 monster | Nosferatu |') and '`mm9_nosferatu.glb`' in row
lines[hits[0]] = row
fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.ledger_')
with os.fdopen(fd, 'w') as f:
    f.write('\n'.join(lines))
os.chmod(tmp, 0o644); os.replace(tmp, path)
print('ROW', row)
