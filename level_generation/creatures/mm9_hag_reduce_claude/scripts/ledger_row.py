#!/usr/bin/env python3
"""Replace the Old Hag's row (72) of the "MM9 reduction" ledger; run under the shared flock
(flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py work/ledger_row.txt). Re-reads the file,
edits only the line whose first cell is 68 and model is Yrsa, writes a temp file and renames."""
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = Path(sys.argv[1]).read_text().strip()
assert '\n' not in ROW
def key(line):
    c = [x.strip() for x in line.split('|')]
    return len(c) > 4 and c[1] == '72' and c[3] == 'Old Hag'
assert key(ROW)
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if key(l)]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
tmp = P.with_suffix('.md.tmp_hag'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 72 written')
