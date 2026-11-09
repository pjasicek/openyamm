#!/usr/bin/env python3
"""Replace the Ghost's row (50) of the MM9 reduction ledger. Run inside the ledger flock; re-reads the file, edits one row,
writes a temp file and renames. Usage: flock <lock> python3 ledger_row.py"""
import os, tempfile
from pathlib import Path
L = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = ("| 50 | 1 monster | Ghost | `mm9_ghost.glb` | 11,166 | 8,430 (-24.5 %; candidate E r45: robe 1,570 -> 750 plus its lining, "
       "jacket 1,336 -> 838, sleeves 1,289 -> 941, linen 995 -> 827, hands 1,178 -> 1,096, head 3,228 byte-identical) | "
       "4,193 / 1,890 / 731 (installed 5,459 / 1,900 / 720) | ready for review 2026-11-04 (ghost-reduce-20261104): pose-aware "
       "half-edge collapse (mpqem.py, Highwayman copy with texture guard on base colour + alpha and the region mask; every vertex an "
       "installed one) on the Ghost's own pre-mirror runtime LOD0, then its runtime tail (lining and blend order rebuilt by "
       "finish_blend.py; r100 reproduces the installed meshes byte for byte); ladder E r45 p99 1.24 / max 11.5 mm (limits 4.4 / 22), "
       "IoU .998, SSIM .997; robe 34 % of free faces, jacket 45 %, sleeves 70 %, linen 75 %, hands 65 % target (fingertips, "
       "junction, hand-to-hand exact); belt/trims, collar bowl, cuffs, hand-contact faces and the whole head kept; gates equal or "
       "better (collapse face-frames 3,694 -> 1,877, arm/hand equal, wrist identical, jitter 0 = 0, order within 1 point, winding 0) "
       "except Death forearm 2.3 -> 2.4 cm (1 shrinking frame) and hands-in-head AttackMelee L 7 -> 9 frames (same 5.2 cm); LODs keep "
       "height and floor per clip (installed LOD3 had lost 8.7 cm of crown, rebuilt head LOD3 keeps it); face pixel-identical in every "
       "tier; not installed | `mm9_ghost_reduce_claude/` | `mm9_ghost_reduce_claude/before/mm9_ghost.glb` (sha256 801c07a3272b) |")
lines = L.read_text().split('\n')
idx = [i for i, l in enumerate(lines) if l.startswith('| 50 | 1 monster | Ghost |')]
assert len(idx) == 1, idx
lines[idx[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=L.parent, prefix='.ledger_')
with os.fdopen(fd, 'w') as f:
    f.write('\n'.join(lines))
os.chmod(tmp, os.stat(L).st_mode & 0o777); os.replace(tmp, L)
print('LEDGER row 50 updated')
