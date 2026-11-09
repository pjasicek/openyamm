#!/usr/bin/env python3
"""Replace the Ghoul's row (60) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only the line
starting with '| 60 | 1 monster | Ghoul |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = ('| 60 | 1 monster | Ghoul | `mm9_ghoul.glb` | 9,988 | 8,448 (-15.4 %; candidate g60: body 5,304 -> 3,990, head set 4,684 -> '
       '4,458 with only the hair cut 902 -> 676) | 4,213 / 1,497 / 779 (installed 4,983 / 1,774 / 813) | ready for review 2026-11-04 '
       '(ghoul-reduce-20261104): pose-aware half-edge collapse (mpqem.py, Troglodyte/Highwayman copy, texture guard on the region '
       'masks and base colours; every vertex an installed one), ladder g r60 p99 5.87 / max 20.8 mm (limits 5.94 / 29.7), IoU .987, '
       'SSIM .996; exact (56.7 %): face skin, teeth, eyes, skull plug, both flaps with lining and rim, neck seam, soles, claws, the skin '
       'the flaps ride on (a60 8,236 passed the ladder but put the front flap 4 mm into the cut thigh skin in Walking/Running/Dead) and '
       'spots that collapsed in f60; body skin 0.6, hands 0.7 (every finger), hair 0.75; the body was already reduced at the build, '
       'so ~15 % is the limit (body 0.55-0.58 fails the p99); gates equal or better (collapse face-frames 10,638 -> 7,599, no region '
       'worse; arm/hand, flaps identical; detached 0; bone length 0; winding 0) except like-for-like jitter Death R shoulder skin 1.90 -> '
       '2.06 mm/f2 (limit 2.0; vertex-subset statistic, clips identical); LODs keep bounds and floor = LOD0 per clip (installed LOD3 '
       'Dead +1.8 cm); face byte-identical; not installed | `mm9_ghoul_reduce_claude/` | '
       '`mm9_ghoul_reduce_claude/before/mm9_ghoul.glb` (sha256 4d4f30b80e06) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 60 | 1 monster | Ghoul |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 60 updated')
