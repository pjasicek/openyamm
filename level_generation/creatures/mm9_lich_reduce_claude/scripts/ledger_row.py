#!/usr/bin/env python3
"""Replace the Lich's row (62) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only the line
starting with '| 62 | 1 monster | Lich |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = ('| 62 | 1 monster | Lich | `mm9_lich.glb` | 9,601 | 7,983 (-16.9 %; candidate E r80: cloak 2,250 -> 1,800, robe 759 -> 413 '
       'plus its lining 759 -> 413, hands 1,319 -> 1,079 (every finger kept), boots 640 -> 532, belt 239 -> 191, pants 280 -> 240; '
       'skull 3,000, neck bones and medallion byte-identical) | 3,990 / 1,433 / 476 (installed 4,798 / 1,725 / 573) | '
       'ready for review 2026-11-04 (lich-reduce-20261104): pose-aware half-edge collapse (mpqem.py, Highwayman copy: every vertex an '
       'installed vertex, texture guard on both tiers; linings re-emitted from their twins with each source face\'s own lining UV '
       'chart, lining-seam twins locked); prep_v2 had already decimated the cloth, so the cut is shallow: ladder E r80 p99 5.09 / '
       'max 20.7 mm (limits 5.57 / 27.9), IoU .995, SSIM .995 (r75 fails p99 6.15); hands 0.65 target (stopped at 71 %, junction, '
       'hand-to-hand and hand-rest contact exact), robe 0.5, hood/belt 0.8, boots 0.75 above the soles; gates equal or better '
       '(arm/hand same hand depths, forearm within +0.2 cm; jitter 6 = 6; sleeve see-through worst 23 -> 24 px; detached 0; winding 0; '
       'flat 0.00; texture atlas 56.8 % = 56.8 %); LODs keep height and floor (protected points); face pixel-identical; '
       'not installed | `mm9_lich_reduce_claude/` | `mm9_lich_reduce_claude/before/mm9_lich.glb` (sha256 ddf1889fe680) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 62 | 1 monster | Lich |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 62 updated')
