#!/usr/bin/env python3
"""Replace the Lesser Demon's row (44) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only
the line starting with '| 44 | 1 monster | Lesser Demon |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = ('| 44 | 1 monster | Lesser Demon | `mm9_lesserdemon.glb` | 12,295 | 10,099 (-17.9 %; candidate j r66: body 7,519 -> 5,797, '
       'head 4,776 -> 4,302 with snout/eyes/mouth/teeth/tongue/horn roots exact; talons 1,248 -> 550) | 4,977 / 1,725 / 1,013 '
       '(installed 6,080 / 2,125 / 926) | ready for review (2026-11-04): mpqem.py (Highwayman copy) + seam slides on the talon tubes; '
       'skin/plates 0.66, cranium 0.7, horns 0.8; shoulder skin and arm-contact faces kept for the gates; ladder p99 6.81 / max 35.6 mm '
       '(limits 7.23 / 36.15); gates equal or better (collapse 47,334 -> 40,089, jitter same 3, detached same 11) except arm/hand Death '
       'L 3.9 -> 4.5 and R 1.6 -> 2.0 cm read off talon-against-talon faces (winding number: not inside); LODs keep the 2.66 m height '
       'and the floor (installed LOD2/3 lost the back spike) | `mm9_lesserdemon_reduce_claude/` | '
       '`mm9_lesserdemon_reduce_claude/before/mm9_lesserdemon.glb` (sha256 416e255ad769) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 44 | 1 monster | Lesser Demon |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 44 updated')
