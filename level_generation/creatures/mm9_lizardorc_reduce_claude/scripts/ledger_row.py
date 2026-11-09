#!/usr/bin/env python3
"""Rewrite ledger row 18 (Lizard-Orc) of REDUCTION_LEDGER.md; run inside the flock (re-reads the file, temp file + rename)."""
import os, tempfile
from pathlib import Path
L = Path(__file__).resolve().parents[2] / 'REDUCTION_LEDGER.md'
row = ("| 18 | 1 monster | Lizard-Orc | `mm9_lizardorc.glb` | 13,881 | 11,829 (-14.8 %) | 5,894 / 2,106 / 692 | ready for review (fix pass, chart guard, "
       "UV audit 0) 2026-11-04: r85m (11,801) was installed and rolled back (67 LOD0 UV escapes); f70 = pose-aware mpqem with MP_CHART, "
       "p99 5.44 / max 20.8 mm, head and cutlass byte-identical, hands 0.6/0.65, lames 0.7; plates and arm equal or better, strap as r18; "
       "jitter shoulder-skin p95 fails on the left (sample-set artefact: vertex max never higher); export/mm9_lizardorc_f70.glb (sha256 679ed6df6031), "
       "not installed | `mm9_lizardorc_reduce_claude/` | `mm9_lizardorc_reduce_claude/before/mm9_lizardorc.glb` (sha256 9a8b9244cbb7) |")
lines = L.read_text().split('\n'); hit = [i for i, l in enumerate(lines) if l.startswith('| 18 | 1 monster | Lizard-Orc |')]
assert len(hit) == 1, hit
lines[hit[0]] = row
fd, tmp = tempfile.mkstemp(dir=L.parent); os.write(fd, '\n'.join(lines).encode()); os.close(fd); os.chmod(tmp, 0o664); os.replace(tmp, L)
print('LEDGER row 18 updated')
