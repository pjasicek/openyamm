#!/usr/bin/env python3
"""Replace the Nobleman's row (53) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only
the line starting with '| 53 | 1 monster | Nobleman |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = ('| 53 | 1 monster | Nobleman | `mm9_nobleman.glb` | 10,727 | 8,119 (-24.3 %; candidate d52: limbs 2,869 -> 1,955, '
       'torso 4,106 -> 3,072, head 3,752 -> 3,092 with face skin/neck/eyes exact, hair split off the one head shell and cut to 65 %) '
       '| 4,058 / 1,457 / 541 | ready for review (2026-11-04): pose-aware half-edge collapse (Highwayman mpqem.py copy, texture guard; '
       'every vertex an installed vertex); ladder d r52 p99 4.99 / max 22.2 mm (limits 5.50 / 27.5), IoU .993, SSIM .996; a55 (-31.7 %) '
       'passed the ladder but moved jitter shoulder skin and the Fidget hand contact, so shoulder skin, hand contact, neck seam, mantle '
       'rim and throat seam kept exactly; gates equal or better except Fidget R frames over 1 cm 13 -> 14 (depth 1.6 both) and a few '
       'worst-frame collapse counts +1..+3 (total face-frames 27,909 -> 25,206), jitter output identical, skirt identical; LOD height and '
       'floor kept with protected points | `mm9_nobleman_reduce_claude/` | '
       '`mm9_nobleman_reduce_claude/before/mm9_nobleman.glb` (sha256 f820e51d08fc) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 53 | 1 monster | Nobleman |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 53 updated')
