#!/usr/bin/env python3
"""Replace PeasantF3's row (7) of the "MM9 reduction" ledger; run under the shared flock
(flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py work/ledger_row.txt). Re-reads the file,
edits only the line starting with '| 7 | 2 town/animal | Peasant woman with veil (PeasantF3) |', writes a temp file and renames."""
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = Path(sys.argv[1]).read_text().strip()
assert ROW.startswith('| 7 | 2 town/animal | Peasant woman with veil (PeasantF3) |') and '\n' not in ROW
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 7 | 2 town/animal | Peasant woman with veil (PeasantF3) |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
tmp = P.with_suffix('.md.tmp_peasantf3'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 7 written')
