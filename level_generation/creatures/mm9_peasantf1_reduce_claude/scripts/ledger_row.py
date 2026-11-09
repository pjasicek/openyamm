#!/usr/bin/env python3
"""Replace PeasantF1's row (14) of the "MM9 reduction" ledger; run under the shared flock
(flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py work/ledger_row.txt). Re-reads the file,
edits only the line starting with '| 14 | 2 town/animal | Peasant woman (PeasantF1) |', writes a temp file and renames."""
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = Path(sys.argv[1]).read_text().strip()
assert ROW.startswith('| 14 | 2 town/animal | Peasant woman (PeasantF1) |') and '\n' not in ROW
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 14 | 2 town/animal | Peasant woman (PeasantF1) |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
tmp = P.with_suffix('.md.tmp_peasantf1'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 14 written')
