#!/usr/bin/env python3
"""Rewrite ledger row 34 (Clan Soldier, fix pass) of REDUCTION_LEDGER.md; run inside the flock (re-reads the file, temp file + rename)."""
import os, tempfile
from pathlib import Path
L = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
row = ("| 34 | 1 monster | Clan Soldier | `mm9_clansoldier.glb` | 12,869 | 10,077 (-21.7 %) | 5,037 / 1,811 / 603 | ready for review "
       "(fix pass, chart guard, UV audit 0) 2026-11-04 (clansoldier-fix-20261104): chart-guarded mpqem h r45 (MP_CHART=1, tier texture "
       "guard, MP_W5=4; p99 5.39 / max 18.7 mm, IoU .995, SSIM .997), every corner an installed vertex, linings re-emitted as exact twins; "
       "face/neck/eyes 3,612 triangles identical, weapons byte-identical; kept: d72 set + hand/forearm contact (460) + skirt-thigh "
       "contact (338); hands 0.6, helmet 0.45, skirt rest 0.7, boots 0.7, pants 0.55. UV audit LOD0 0 escaping in every primitive. "
       "Gates as installed (arm, skirt, grip, blades, detached, orient, texture) except jitter Death L/R 2.13/2.62 -> 2.42/2.88 "
       "(same-mesh 2.10/2.57, below installed; 3 fails both), single-face collapse maxima, LOD1-3 seam sliver stretch (pre-existing in "
       "LOD0) kept for Dead floor contact. Previous d72 (9,635) installed and rolled back (UV escapes); not installed | "
       "`mm9_clansoldier_reduce_claude/` (candidate `export_mp/mm9_clansoldier.glb`, sha256 79abc5b0be33) | "
       "`mm9_clansoldier_reduce_claude/before/mm9_clansoldier.glb` (sha256 487e28a9084b) |")
lines = L.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 34 | 1 monster | Clan Soldier |')]
assert len(hit) == 1, hit
lines[hit[0]] = row
fd, tmp = tempfile.mkstemp(dir=L.parent); os.write(fd, '\n'.join(lines).encode()); os.close(fd); os.chmod(tmp, 0o664); os.replace(tmp, L)
print('LEDGER row 34 updated')
