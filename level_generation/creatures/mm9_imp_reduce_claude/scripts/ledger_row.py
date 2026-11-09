#!/usr/bin/env python3
"""Replace the Imp's row (79) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only the
line starting with '| 79 | 1 monster | Imp |', writes a temp file and renames it. imp-reduce-20261104."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
KEY = '| 79 | 1 monster | Imp |'
ROW = ('| 79 | 1 monster | Imp | `mm9_imp.glb` | 8,080 | 7,002 (-13.3 %, below the ~15 % bar; candidate p80: body 4,817 -> 3,807, '
       'head 3,263 -> 3,195 with only the cranium cut) | 3,498 / 1,258 / 407 (installed 4,037 / 1,452 / 473) | ready for review '
       '2026-11-04 (imp-reduce-20261104), orchestrator may record kept (no useful gain): pose-aware half-edge collapse (mpqem.py, '
       'Bigfoot/Lesser Demon copy, seam slides on every cut group, Mummy chart guard, texture guard on region mask, base colour and '
       'metal/roughness; every vertex an installed one); protected share 55 % (face, ears, horns, eyes, teeth, neck seam, '
       'belt/buckle/flap/wrist bands, claws, tail, soles, the whole trident fist (308), shin-wrap contact exact); hands 0.6, feet and '
       'cranium 0.65, rest 0.8; ladder p r80 p99 3.50 / max 10.5 mm (limits 3.53 / 17.6 at 1.176 m), IoU .995, SSIM .996; nothing '
       'reached -15 % with the fist kept (n80 -14.6 % cut the fist); UV chart escapes 0; gates: arm/hand no clip worse, trident '
       'identical, jitter no new fail (installed Death2 fail stays, lower), stretch/bones/winding/flat equal, flap detach 4.1 -> 2.3 '
       'cm; LODs keep claw/horn/tail tips (68/68 snapped), installed LOD3 float (up to +1.8 cm) gone; FACE_NOTE; not installed | '
       '`mm9_imp_reduce_claude/` | `mm9_imp_reduce_claude/before/mm9_imp.glb` (sha256 82117ae94fca) |')
FACE = os.environ.get('FACE_NOTE', 'face pixel-identical in every tier')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, hit
lines[hit[0]] = ROW.replace('FACE_NOTE', FACE)
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('ROW', hit[0] + 1)
