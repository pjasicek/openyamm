#!/usr/bin/env python3
"""Rewrite ledger row 33 (Half-Orc) of REDUCTION_LEDGER.md; run inside the flock (re-reads the file, temp file + rename)."""
import os, tempfile
from pathlib import Path
L = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
row = ("| 33 | 1 monster | Half-Orc | `mm9_dookmilitia.glb` | 12,906 | 10,168 (-21.2 %) | 5,071 / 1,822 / 603 | ready for review (fix pass, "
       "chart guard, UV audit 0) 2026-11-04: pose-aware half-edge collapse with MP_CHART=1 and the tier texture guard (mpqem M1 r55, "
       "p99 4.69 / max 17.2 mm, IoU .993, SSIM .994), first pass's keep set (face/eyes/neck exact, hood 0.6, hands 0.6/0.65, skirt "
       "0.75; cuffs, buckle, caps, linings, boot rims, sword kept); every LOD0 vertex is an installed vertex; UV audit LOD0 0 "
       "escaping (first pass 73); gates equal except Dead +0.23 cm and grip wrap -15 deg on ring/pinky; LOD3 Death2 -7.7 mm; "
       "LOD1 audit escapes 133/167 vs installed 80/122 (Blender LOD decimate). Earlier: c479p installed and rolled back "
       "(UV escapes); not installed | `mm9_dookmilitia_reduce_claude/` | "
       "`mm9_dookmilitia_reduce_claude/before/mm9_dookmilitia.glb` (sha256 8a60c4575c2e) |")
lines = L.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 33 | 1 monster | Half-Orc |')]
assert len(hit) == 1, hit
lines[hit[0]] = row
fd, tmp = tempfile.mkstemp(dir=L.parent); os.write(fd, '\n'.join(lines).encode()); os.close(fd); os.chmod(tmp, 0o664); os.replace(tmp, L)
print('LEDGER row 33 updated')
