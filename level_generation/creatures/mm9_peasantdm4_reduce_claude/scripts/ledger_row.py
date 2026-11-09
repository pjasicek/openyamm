#!/usr/bin/env python3
"""Replace PeasantDM4's row (32) of the "MM9 reduction" ledger; run under the shared flock
(flock ../claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py work/ledger_row.txt). Re-reads the file,
edits only the line whose first column is 32 and whose file column is mm9_peasantdm4.glb, temp file + rename."""
import os
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = Path(sys.argv[1]).read_text().strip()
assert ROW.startswith('| 32 |') and 'mm9_peasantdm4.glb' in ROW and '\n' not in ROW
lines = P.read_text().split('\n')
hit = [i for i, l in enumerate(lines) if l.startswith('|') and len(l.split('|')) > 5
       and l.split('|')[1].strip() == '32' and 'mm9_peasantdm4.glb' in l.split('|')[4]]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
tmp = P.with_suffix('.md.tmp_peasantdm4'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 32 written')
