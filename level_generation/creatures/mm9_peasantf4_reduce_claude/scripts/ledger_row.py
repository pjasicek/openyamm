#!/usr/bin/env python3
"""Replace PeasantF4's row (8) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only the line
starting with '| 8 | 2 town/animal | Peasant hooded woman (PeasantF4) |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
KEY = '| 8 | 2 town/animal | Peasant hooded woman (PeasantF4) |'
ROW = (KEY + ' `mm9_peasantf4.glb` | 14,948 | 12,312 (-17.6 %; candidate m7 r50: body 9,406 -> 7,178, head set 5,542 -> 5,134 with the '
       'whole head comp exact) | 6,032 / 2,170 / 988 (installed 7,343 / 2,640 / 880) | ready for review (2026-11-04, peasantf4-reduce-20261104): '
       'pose-aware half-edge collapse (mpqem.py, Highwayman copy; every vertex an installed one, texture guard on tone + region mask and both '
       'face tiers); hood and sleeve-tube linings re-emitted from the cut outer cloth through the asm twin map; kept exactly: head comp (face, '
       'eyes, neck seam, hidden skull), hidden old hood, the job-8 rims, sleeve caps and bodice hole fills, placket column, painted bodice trims '
       '(apron band, collar), F1 short sleeves, hidden skirt lining, soles; hands 0.6, hood 0.7, skirt 0.7, sleeve tube 0.8, MPFB arm 0.75, '
       'bodice 0.5; ladder p99 ~2.8 / max ~17 mm (limits 5.2 / 26), IoU .998, SSIM .997; LOD0 UV escapes 0; face pixel-identical both tiers; '
       'gates equal or better (collapse 27,518 -> 23,957, arm/hand, robe, short-sleeve poke identical, hood/tube 0 frames > 1 cm, see-through '
       'sleeve R 2 = 2 px, no magenta back faces) except collar see-through 907 -> 949 px (Death from the feet) and single-face collapse rises; '
       'LOD3 keeps the hood top (installed lost 4 cm) and the floor; 7 configurations, below the ~25 % of a plain cut because the fixes and '
       'trims are kept | `mm9_peasantf4_reduce_claude/` | `mm9_peasantf4_reduce_claude/before/mm9_peasantf4.glb` (sha256 bccd88d7a334) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith(KEY)]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 8 updated')
