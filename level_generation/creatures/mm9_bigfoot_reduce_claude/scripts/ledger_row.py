#!/usr/bin/env python3
"""Replace the Bigfoot's row (64) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only the
line starting with '| 64 | 1 monster | Bigfoot |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
KEY = '| 64 | 1 monster | Bigfoot |'
ROW = ('| 64 | 1 monster | Bigfoot | `mm9_bigfoot.glb` | 9,442 | 7,320 (-22.5 %; candidate d55: body 5,784 -> 3,898, head 3,658 -> '
       '3,422 with face skin, eyes, ears, neck seam and neck rim exact) | 3,660 / 1,461 / 601 (installed 4,720 / 1,698 / 565) | '
       'ready for review 2026-11-04 (bigfoot-reduce-20261104): pose-aware half-edge collapse (mpqem.py, Lesser Demon copy, texture '
       'guard on region mask incl. the saddle alpha + base colour in every tier; every vertex an installed one); protected share 39.9 %; '
       'hood, hands, feet 0.7, crown 0.75, rest 0.55; soles, wrist junction and `Foot_h` helper faces exact; ladder d r55 p99 7.51 / '
       'max 29.8 mm (limits 7.61 / 38 at 2.537 m), IoU .994, SSIM .995; gates: collapse face-frames 8,540 -> 5,110 (a few regions +1 '
       'face), arm/hand 0 frames > 1 cm both (worst 0.8 -> 0.7 cm), jitter 27 -> 26 strict / 20 -> 20 relative (shoulder-skin p95 over '
       'the smaller vertex subset; clips and skinning identical, vertex max not higher), detached/winding/bones/flat 0; LODs keep '
       'bounds, protected points snapped (158/158), floor equal or better than installed (LOD3 Death -2.08 -> -0.16 cm); face '
       'pixel-identical in every tier; not installed | `mm9_bigfoot_reduce_claude/` | '
       '`mm9_bigfoot_reduce_claude/before/mm9_bigfoot.glb` (sha256 1169fc94eae5) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('ROW', hit[0] + 1)
