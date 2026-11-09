#!/usr/bin/env python3
"""Replace the Highwayman's row (28) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only
the line starting with '| 28 | 1 monster | Highwayman |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = ('| 28 | 1 monster | Highwayman | `mm9_highwayman.glb` | 13,094 | 9,916 (-24.3 %; candidate m4 r57: limbs 4,856 -> 3,334, '
       'torso 3,650 -> 2,430, head 3,928 -> 3,492 with face/neck/eyes exact, weapons 660 kept) | 4,954 / 1,781 / 588 | '
       'ready for review (2026-11-04): pose-aware half-edge collapse (mpqem.py from the Banshee; every vertex an installed vertex, '
       'linings re-emitted from their twins, texture guard) after the MeshLab ladder stopped at -21 % (Death2 groin); ladder m4 r57 '
       'p99 4.74 / max 25.5 mm (limits 5.57 / 27.8), IoU .994, SSIM .995; hands/hair 0.65, skirt 0.7, boots 0.6, belt and grip contact '
       'exact; gates equal or better (collapse face-frames 26,046 -> 17,972, skirt identical, grip identical, jitter 7 -> 7), '
       'LOD floor/height kept with protected points | `mm9_highwayman_reduce_claude/` | '
       '`mm9_highwayman_reduce_claude/before/mm9_highwayman.glb` (sha256 1923e3d405f8) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 28 | 1 monster | Highwayman |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 28 updated')
