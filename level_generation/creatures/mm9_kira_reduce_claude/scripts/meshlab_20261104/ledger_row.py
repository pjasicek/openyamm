#!/usr/bin/env python3
"""Replace Kira's row in REDUCTION_LEDGER.md (MM9 reduction table), temp file + rename. Run inside
flock claude_shared/locks/reduction_ledger.lock. Usage: ledger_row.py '<full new row>'"""
import os, sys, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
lines = P.read_text().split('\n'); hits = [i for i, l in enumerate(lines) if ('| Kira the Cold | `mm9_kira.glb`' in l)]
assert len(hits) == 1, hits
lines[hits[0]] = sys.argv[1]
fd, tmp = tempfile.mkstemp(dir=P.parent); os.write(fd, '\n'.join(lines).encode()); os.close(fd); os.chmod(tmp, 0o664); os.replace(tmp, P)
print('ROW', sys.argv[1])
