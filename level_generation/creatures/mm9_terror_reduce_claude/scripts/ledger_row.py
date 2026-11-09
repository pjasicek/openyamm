#!/usr/bin/env python3
"""Replace the Terror's row (73) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only the
line starting with '| 73 | 1 monster | Terror |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
L = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
KEY = '| 73 | 1 monster | Terror |'
ROW = ('| 73 | 1 monster | Terror | `mm9_terror.glb` | 8,441 | 8,441 (kept) | unchanged | kept (no useful gain) 2026-11-04 '
       '(terror-reduce-20261104): body already cut to 0.48 at the build; exact set (4 eyes, 12 teeth, tongue, 1,156-face mouth bag, '
       'face front/lids/lips, tentacle-tip mouths, toe claws, soles) 53.6 %; pose-aware mpqem.py (Lesser Demon copy, texture guard on '
       'region mask + base colour), limits for 2.934 m p99 8.8 / max 44 mm: a (tentacles .6 seam slides, W5 3) r60 6,899 -18 % p99 15.3 '
       'fail; b (all one group, cranium .7) r75 7,449 -11.8 % p99 9.55 fail, r68 p99 11.5 fail; c (calves/feet .85, cranium .85) r70 '
       '7,465 -11.6 % p99 10.3 fail. Error spread over calves, thighs, feet, tentacles and cranium (err_by_bone), no single lockable spot | '
       '`mm9_terror_reduce_claude/` | not needed (`mm9_terror_reduce_claude/before/mm9_terror.glb`, sha256 8324935491f2) |')
lines = L.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=L.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, 0o644); os.replace(tmp, L); print('ROW 73 written')
