#!/usr/bin/env python3
"""Replace the Zombie's row (51) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only
the line starting with '| 51 | 1 monster | Zombie |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = ('| 51 | 1 monster | Zombie | `mm9_zombie.glb` | 11,060 | 8,570 (-22.5 %; candidate i r55: body 3,628 -> 2,440, '
       'head 4,694 -> 4,310 with face skin/teeth/eyes/plug/neck seam exact, torso 2,738 -> 1,820 with the tatter lining rebuilt) | '
       '4,255 / 1,503 / 493 | ready for review (2026-11-04): pose-aware half-edge collapse (Highwayman mpqem.py: every vertex an '
       'installed vertex, tatter lining re-emitted from its twins, texture guard on base colour + region mask / torso tiers); '
       'ladder i r55 p99 5.26 / max 24.5 mm (limits 5.38 / 26.9), IoU .989, SSIM .996; hands/hair locks 0.65, scalp (hair-painted '
       'head skin) 0.8, tatter 0.7, bones 0.75; hand-to-hand and hand-on-trouser contact faces exact; gates equal or better except '
       'single-face collapse counts (armpit_L/elbow_R 0 -> 1) and Death2 tatter frames 24 -> 27 (installed failure); '
       'collapse face-frames 21,925 -> 17,319, arm/hand equal or better, jitter 8 -> 8; LOD heights/floor equal to LOD0 | '
       '`mm9_zombie_reduce_claude/` | `mm9_zombie_reduce_claude/before/mm9_zombie.glb` (sha256 cabff291d0b6) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 51 | 1 monster | Zombie |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 51 updated')
