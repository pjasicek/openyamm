#!/usr/bin/env python3
"""Replace the Guard's row (48) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only the line
starting with '| 48 | 1 monster | Guard |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = ('| 48 | 1 monster | Guard | `mm9_guard.glb` | 11,486 | 9,028 (-21.4 %; candidate e55: body 8,680 -> 6,408, head set 2,806 -> 2,620 '
       'with the face/neck skin exact; halberds and plates unchanged) | 4,511 / 1,618 / 534 | ready for review (2026-11-04, guard-reduce-20261104): '
       'pose-aware half-edge collapse (`mpqem.py`, the Highwayman\'s; every vertex an installed vertex, texture guard, linings re-emitted from '
       'their twins, 8 centre-seam orphan linings kept); ladder e r55 p99 4.87 / max 14.4 mm (limits 5.65 / 28.2), IoU .992, SSIM .994, open '
       'edges equal; helmet 0.6 (rim on the face and under the plates exact), hands 0.65 (grip contact, right 2nd/3rd phalanges, junction '
       'exact), boots 0.55, pants 0.6, skirt, belt, buckle, gauntlets + adjacent sleeve, hand-rest and halberd contact exact; gates equal or '
       'better (skirt identical, arm/hand no value worse, grip inside 0.1 -> 0.0 cm, blade Sleep 4 -> 3 f, jitter 0 = 0, detached 0 = 0, '
       'collapse face-frames 13,706 -> 8,110 with +1-2 faces in a few worst frames), LOD3 Death -1.5 cm (installed -0.5); not installed '
       '| `mm9_guard_reduce_claude/` | `mm9_guard_reduce_claude/before/mm9_guard.glb` (sha256 f061fec71854) |')
lines = P.read_text().splitlines(keepends=True)
hits = [i for i, l in enumerate(lines) if l.startswith('| 48 | 1 monster | Guard |')]
assert len(hits) == 1, hits
lines[hits[0]] = ROW + '\n'
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, ''.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('ROW 48 updated')
