#!/usr/bin/env python3
"""Replace the Gezzampt's row (57) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only the
line starting with '| 57 | 1 monster | Gezzampt |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
KEY = '| 57 | 1 monster | Gezzampt |'
ROW = ('| 57 | 1 monster | Gezzampt | `mm9_gezzampt.glb` | 10,152 | 7,992 (-21.3 %; candidate f57: body 6,346 -> 4,418, head 3,806 -> '
       '3,574 with face skin, eyes, teeth, ears, horns and neck seam exact) | 3,995 / 1,597 / 595 (installed 5,076 / 1,826 / 605) | '
       'ready for review 2026-11-04 (gezzampt-reduce-20261104): pose-aware half-edge collapse (mpqem.py, Troglodyte/Highwayman copy, '
       'texture guard on region mask + base colour; every vertex an installed one); protected share 42.3 %; mane, fists, hooves 0.7, '
       'rest 0.57; ankle/hock helper (`Foot_h`, `HorseLink_h`) faces exact; ladder f r57 p99 7.18 / max 17.7 mm (limits 7.61 / 38 '
       'at 2.537 m), IoU .995, SSIM .997; gates: collapse face-frames 7,598 -> 6,442 (a few regions +1 face), arm/hand 0 cm both, '
       'jitter 12 -> 13 fails (shoulder-skin p95 over the smaller vertex subset; clips and skinning identical, vertex max not higher), '
       'detached/winding/bones/flat 0; LODs keep bounds and ear/horn tips, corpse sinks 2.0 cm at LOD3 (installed 0.7); face '
       'pixel-identical in every tier; not installed | `mm9_gezzampt_reduce_claude/` | '
       '`mm9_gezzampt_reduce_claude/before/mm9_gezzampt.glb` (sha256 ecfc476765d1) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('ROW', hit[0] + 1)
