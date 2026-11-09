#!/usr/bin/env python3
"""Replace the Lich King's row (6) of the "MM9 reduction" ledger; run under the shared flock
(flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py work/ledger_row.txt). Re-reads the file,
edits only the line starting with '| 6 | 3 unique | Lich King |', writes a temp file and renames."""
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
KEY = '| 6 | 3 unique | Lich King |'
ROW = Path(sys.argv[1]).read_text().strip()
assert ROW.startswith(KEY) and '\n' not in ROW
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, hit
cols = lines[hit[0]].split('|'); assert len(cols) == len(ROW.split('|')), (len(cols), len(ROW.split('|')))
lines[hit[0]] = ROW
tmp = P.with_suffix('.md.tmp_lichking'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 6 written')
