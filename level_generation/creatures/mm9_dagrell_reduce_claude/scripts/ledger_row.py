#!/usr/bin/env python3
"""Replace the Dagrell's row (87) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only the
line starting with '| 87 | 1 monster | Dagrell |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
L = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
KEY = '| 87 | 1 monster | Dagrell |'
ROW = ('| 87 | 1 monster | Dagrell | `mm9_dagrell.glb` | 7,518 | 7,518 (kept) | unchanged | kept (no useful gain) 2026-11-04 '
       '(dagrell-reduce-20261104): body already cut to 0.45 at the build (14,920 -> 7,564); 136 thin rigid bone pieces; exact set '
       '(head/jaw/neck pieces, teeth and spurs, thin spikes, claws/toes, soles) 51.4 %; pose-aware mpqem.py (Terror copy, texture guard '
       'on region mask + base colour), limits for 1.866 m p99 5.6 / max 28 mm: a (body one group, W5 5) r70 6,422 -14.6 % p99 7.41 IoU '
       '.980 fail, r65 6,238 -17 % p99 8.78 fail; b (+ cranium .7, W5 3) r76 6,510 -13.4 % p99 6.07 fail, r72 6,364 -15.4 % p99 6.76 '
       'fail | `mm9_dagrell_reduce_claude/` | not needed (`mm9_dagrell_reduce_claude/before/mm9_dagrell.glb`, sha256 cef0f1ca0c18) |')
lines = L.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=L.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, 0o644); os.replace(tmp, L); print('ROW 87 written')
