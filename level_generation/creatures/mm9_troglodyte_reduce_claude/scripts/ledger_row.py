#!/usr/bin/env python3
"""Replace the Troglodyte's row (46) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only
the line starting with '| 46 | 1 monster | Troglodyte |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = ('| 46 | 1 monster | Troglodyte | `mm9_troglodyte.glb` | 12,010 | 9,926 (-17.4 %; candidate d55: body 6,252 -> 4,168, head '
       '5,758 byte-identical) | 4,955 / 1,783 / 830 (installed 5,996 / 2,157 / 879) | ready for review 2026-11-04 '
       '(troglodyte-reduce-20261104): pose-aware half-edge collapse (mpqem.py, Highwayman copy with texture guard on the tier-A '
       'region mask and the B/C colours; every vertex an installed one), ladder d r55 p99 3.23 / max 12.0 mm (limits 3.6 / 18), '
       'IoU .994, SSIM .995; head primitive (face, mouth, teeth, eyes, neck strip; 48 % of LOD0) kept whole, so only the '
       'already-reduced body could be cut: neck seam, soles, claws, calf spines and head/jaw-pierce faces exact, hands 0.7 '
       '(every finger), rest 0.55; a55 9,702 (-19.2 %) passed the ladder but raised jaw-in-torso 1.3 -> 2.5 cm; gates equal or '
       'better (collapse 39,051 -> 35,370 face-frames, arm/hand, tail/leg pierce, jitter 1 = 1) except head-in-torso Fidget2 '
       '0.6 -> 1.2 cm (5 f), AttackMelee 0.0 -> 0.8 cm; LODs keep claw tips and bounds (installed LOD3 lost 3.5 cm), floor per '
       'clip = LOD0; face pixel-identical in every tier; not installed | `mm9_troglodyte_reduce_claude/` | '
       '`mm9_troglodyte_reduce_claude/before/mm9_troglodyte.glb` (sha256 40b9d4b824d7) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 46 | 1 monster | Troglodyte |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 46 updated')
