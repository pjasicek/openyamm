#!/usr/bin/env python3
"""Replace the Thrall's row (63) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only
the line starting with '| 63 | 1 monster | Thrall |', writes a temp file and renames it."""
import os
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = ('| 63 | 1 monster | Thrall | `mm9_thrall.glb` | 9,517 | 7,741 (-18.7 %; candidate h65: limbs 3,990 -> 2,634, torso 1,969 -> 1,631, '
       'head 3,558 -> 3,476 with face skin/eyes exact, hair shell 0.8) | 3,869 / 1,386 / 470 | ready for review 2026-11-04 '
       '(thrall-reduce-20261104): pose-aware half-edge collapse (Lesser Demon mpqem.py with seam slides on the MPFB hands + three-tier '
       'texture guard; every vertex an installed one), ladder h r65 p99 5.06 / max 20.4 mm (limits 5.38 / 26.9), IoU .994, SSIM .996; '
       'face skin 29 % of LOD0 and the body already cut at the build, so the body fails at ~0.65 whatever is locked; hands 0.5 '
       '(every finger; 0.35 reached 7,541 but faceted the fingertips), hair 0.8 (0.6 put a dark sliver on the bald crown), skirt 0.7, '
       'shoulder skin and Fidget2/Hit2 hand contact kept (jitter); gates equal or better (jitter output identical, 13 = 13; arm/hand '
       'identical except Walking R 1.6 -> 0.9 cm; collapse 6,176 -> 5,737 face-frames) except skirt AttackMelee3 0 -> 0.7 cm (4 f), '
       'AttackRanged 0.1 -> 0.6 cm; LODs keep height and floor per clip (installed LOD3 floated 1.8 cm dead); face pixel-identical in '
       'every tier; not installed | `mm9_thrall_reduce_claude/` | `mm9_thrall_reduce_claude/before/mm9_thrall.glb` (sha256 f01a6779a95f) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 63 | 1 monster | Thrall |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
tmp = P.with_suffix('.md.tmp_thrall'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 63 written')
