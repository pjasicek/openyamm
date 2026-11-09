#!/usr/bin/env python3
"""Replace the Honk female's row (65) of the "MM9 reduction" ledger; run under the shared flock. Re-reads the file, edits only
the line starting with '| 65 | 1 monster | Honk (female) |', writes a temp file and renames it."""
import os, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
ROW = ('| 65 | 1 monster | Honk (female) | `mm9_honkf.glb` | 9,431 | 8,141 (-13.7 %; fix pass n r70: body set 2,621 -> 2,279, head + hands '
       'set 6,810 -> 5,862 with head shell, eyes, neck seam and the gold goose piece (beak, eye) exact) | 4,069 / 1,464 / 485 | '
       'ready for review (fix pass, chart guard, UV audit 0) (2026-11-04): h r70 (7,901) was installed and rolled back (83 LOD0 faces off '
       'the charts: goose eye gone, scales smeared); mpqem.py now has the Imp/Mummy chart guard; same keep set + chart guard gave 8,003 '
       '(-15.1 %, k r70) but a straighter, darker beak, so the goose piece is kept too; reduction_uv_audit.py LOD0 escaping 0 (was 83; '
       'LOD1-3 near the installed file\'s own decimate escapes); ladder p99 2.93 / max 17.6 mm, IoU .997, SSIM .995; gates as h r70: '
       'collapse face-frames 30,385 -> 29,601, robe/sleeve/forearm-poke identical, hair equal or fewer, jitter 0 -> 0, arm/hand Death R '
       '0.0 -> 0.2 cm and Fidget2 R forearm 0.0 -> 0.4 cm (0 frames over 1 cm); LOD height and floor equal to LOD0; headdress close-ups '
       'both tiers read (review/hat_n70_{a,b}.png); export sha256 ef804653a269 | `mm9_honkf_reduce_claude/` | '
       '`mm9_honkf_reduce_claude/before/mm9_honkf.glb` (sha256 9fd961fe94ef) |')
lines = P.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 65 | 1 monster | Honk (female) |')]
assert len(hit) == 1, hit
lines[hit[0]] = ROW
fd, tmp = tempfile.mkstemp(dir=P.parent, prefix='.ledger_'); os.write(fd, '\n'.join(lines).encode()); os.close(fd)
os.chmod(tmp, os.stat(P).st_mode & 0o777); os.replace(tmp, P); print('LEDGER row 65 updated')
