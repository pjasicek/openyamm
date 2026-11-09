#!/usr/bin/env python3
"""Replace the Basilisk's row (77) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only the
line starting with '| 77 | 1 monster | Basilisk |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
KEY = '| 77 | 1 monster | Basilisk |'
ROW = ('| 77 | 1 monster | Basilisk | `mm9_basilisk.glb` | 8,132 | 8,132 (kept) | unchanged | kept (no useful gain) 2026-11-04 '
       '(basilisk-reduce-20261104): body already cut to 0.5 (head 0.7) at the build (15,606 -> 8,132); exact set (eyes, teeth and gum '
       'pieces, whole jaw, face in front of the eyes, crown horns, claws, soles) 39.5 %; pose-aware mpqem.py (Lesser Demon copy with '
       'seam slides, texture guard on region mask + base colour), limits for the 1.125 m standing height p99 3.38 / max 16.9 mm: '
       'a (toes .7, frill .8, cranium .75) r65 6,626 -18.5 % p99 11.7 fail; c (body only) r90 7,842 -3.6 % p99 2.53 / max 30.3 '
       '(front foot, AttackMelee) fail, r80 -7.2 % p99 5.21 fail; d (frill .8 + cranium .75 only) -2.5 % pass; e (toes .8 only) -2.4 % '
       'pass; f (all relaxed + error lock) r90 7,416 -8.8 % p99 4.38 fail, r80 7,136 -12.2 % p99 5.84 fail; MeshLab texture weight 4 '
       'with the same keep set r90 p99 6.1 / max 50 fail. Error spread over legs, feet, flank (large faces already) | '
       '`mm9_basilisk_reduce_claude/` | not needed (`mm9_basilisk_reduce_claude/before/mm9_basilisk.glb`, sha256 dfa6cf2385d6) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('ROW', hit[0] + 1)
