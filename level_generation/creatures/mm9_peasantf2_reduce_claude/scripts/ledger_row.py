#!/usr/bin/env python3
"""Replace PeasantF2's row (9) of the "MM9 reduction" ledger; run under the shared flock
(flock level_generation/creatures/claude_shared/locks/reduction_ledger.lock python3 scripts/ledger_row.py <row file>).
Re-reads the ledger, edits only the line starting with '| 9 | 2 town/animal | Peasant woman with braid (PeasantF2) |',
writes a temp file and renames it. The new row text is read from the given file (one line)."""
import os, sys
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = Path(sys.argv[1]).read_text().strip()
assert ROW.startswith('| 9 | 2 town/animal | Peasant woman with braid (PeasantF2) |') and '\n' not in ROW
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 9 | 2 town/animal | Peasant woman with braid (PeasantF2) |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
tmp = P.with_name(P.name + '.tmp_pf2'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P)
print('LEDGER row 9 written')
