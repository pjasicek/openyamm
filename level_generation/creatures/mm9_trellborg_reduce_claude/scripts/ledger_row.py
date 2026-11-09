#!/usr/bin/env python3
"""Rewrite ledger row 43 (Trellborg) of REDUCTION_LEDGER.md; run inside the flock (re-reads the file, temp file + rename)."""
import os, tempfile
from pathlib import Path
L = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
row = ("| 43 | 1 monster | Trellborg | `mm9_trellborg.glb` | 12,305 | 9,781 (-20.5 %) | 4,888 / 1,754 / 583 | ready for review 2026-11-04 "
       "(trellborg-reduce-20261104): ladder m r81 (p99 5.78 / max 27.0 mm, IoU .993, SSIM .996), MeshLab texture weight 8 (REA_TEXW: halved the "
       "paint drift of the three tiers' straps, greaves and fur), club rebuilt on make_club's own lathe and cylinder UVs (576 -> 392, maps unchanged); "
       "face box, ears, nape/neck skin, tusks, neck seam exact (3,242 triangles identical), both fists and both cuffs exact (cut versions creased/kinked), "
       "hair 0.6, body skin shared cut; LODs keep hair tops and death floor contact (LOD3 height = LOD0); gates equal or better: jitter 10 -> 9 fails, "
       "collapse 3,412 -> 2,425 face-frames, grip/club/arm maxima identical (Fidget3 L forearm 1.4 -> 1.5 cm, 0 f > 1 cm), Death club 1.2 mm under "
       "the floor (was 0.0); not installed | `mm9_trellborg_reduce_claude/` | `mm9_trellborg_reduce_claude/before/mm9_trellborg.glb` (sha256 793190d6c9c8) |")
lines = L.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 43 | 1 monster | Trellborg |')]
assert len(hit) == 1, hit
lines[hit[0]] = row
fd, tmp = tempfile.mkstemp(dir=L.parent); os.write(fd, '\n'.join(lines).encode()); os.close(fd); os.chmod(tmp, 0o664); os.replace(tmp, L)
print('LEDGER row 43 updated')
