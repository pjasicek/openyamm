#!/usr/bin/env python3
"""Ledger row 21 (Dwarf) of REDUCTION_LEDGER.md's MM9 section: re-read inside the flock, replace the row, temp file + rename.
Run as: flock level_generation/creatures/claude_shared/locks/reduction_ledger.lock python3 <this> (repo root)."""
import os
from pathlib import Path
P = Path('level_generation/creatures/REDUCTION_LEDGER.md'); lines = P.read_text().split('\n')
new = ('| 21 | 1 monster | Dwarf | `mm9_dwarf.glb` | 13,643 | 10,193 | 5,094 / 1,830 / 717 | ready for review (fix pass, chart guard, UV audit 0) 2026-11-04 '
       '(dwarf-reduce-20261104-fix): chart-guarded pose-aware collapse (mpqem MP_CHART=1, tier texture guard, W5 4) r40 -25.3 %, p99 3.74 / max 14.0 mm, '
       'IoU 0.995, SSIM 0.993; UV audit 0 escaping LOD0 faces (r71 had 67); same keep set as r71 (face, eyes, neck, right hand, skirt, '
       'cuffs, belt, plates, axe, bracer ends, soles exact; beard 0.7, helmet 0.75, horns 0.7, left hand 0.75, pants 0.85); every gate '
       'equal to the installed model (rim helmet 0.7 -> 0.4 cm); LODs 1.322 m tall, 0 stretched. Earlier: r71 (9,683) installed and '
       'rolled back 2026-11-04 (UV escapes) | '
       '`mm9_dwarf_reduce_claude/` (`export_mp/mm9_dwarf.glb`) | `mm9_dwarf_reduce_claude/before/mm9_dwarf.glb` (sha256 2bc9e109af9f) |')
idx = [i for i, l in enumerate(lines) if l.startswith('| 21 | ') and '`mm9_dwarf.glb`' in l]
assert len(idx) == 1, idx
lines[idx[0]] = new
tmp = P.with_suffix('.md.tmp_dwarf'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 21 updated')
