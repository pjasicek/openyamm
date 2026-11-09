#!/usr/bin/env python3
"""Replace the Mummy's row (66) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only the
line starting with '| 66 | 1 monster | Mummy |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = ('| 66 | 1 monster | Mummy | `mm9_mummy.glb` | 9,397 | 6,781 (-27.8 %; candidate e r48: body 6,190 -> 3,574 with hands '
       '1,346 -> 808 and the band/thigh/arm strips exact, head set 3,207 exact: face, hood, eyes) | 3,568 / 1,363 / 592 | '
       'ready for review (2026-11-04): pose-aware half-edge collapse (mpqem.py, Lesser Demon copy: every vertex an installed vertex, '
       'seam slides, per-tier texture guard, texture weight 4) + new stretch and chart guards (UV triangles stay on the installed '
       'charts: builds b-d smeared a chevron on the Embalmed forearm); ladder e r48 p99 4.50 / max 19.3 mm (limits 5.45 / 27.2), '
       'IoU .991, SSIM .996; hands 0.6; gates equal or better except Resurrect (script) knee_L 2 -> 4 and band-through-chest depth '
       'AttackMelee2 9.4 -> 10.0 cm (installed fault, same frames); creature strip_gate.py bug found (head triangles on body vertices), '
       'fixed copy used; LODs: per-material ratios, height/floor equal to LOD0, no stretched face | `mm9_mummy_reduce_claude/` | '
       '`mm9_mummy_reduce_claude/before/mm9_mummy.glb` (sha256 529f6652cc7b) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 66 | 1 monster | Mummy |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 66 updated')
