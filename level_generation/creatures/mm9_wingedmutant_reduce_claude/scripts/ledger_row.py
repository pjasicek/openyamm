#!/usr/bin/env python3
"""Ledger row 36 (Winged Mutant) of REDUCTION_LEDGER.md's MM9 section: re-read inside the flock, replace the row, temp file +
rename. Run as: flock level_generation/creatures/claude_shared/locks/reduction_ledger.lock python3 <this> (repo root)."""
import os
from pathlib import Path
P = Path('level_generation/creatures/REDUCTION_LEDGER.md'); lines = P.read_text().split('\n')
new = ('| 36 | 1 monster | Winged Mutant | `mm9_wingedmutant.glb` | 12,599 | 11,445 (-9.2 %) | 5,720 / 2,053 / 834 | ready for review '
       '(fix pass, chart guard, UV audit 0) 2026-11-04 (wingedmutant-reduce-fix-20261104): mpqem MP_CHART=1 + tier texture guard, '
       'W5 4, ladder c r85; hair 0.6 target (guards stop at 0.76), membrane 0.85, feet 0.85; face set, body, claw tips, helper-heavy '
       'membrane, knuckles, hair lock tips kept; back copies re-emitted from exact twins; non-hair p99 4.03 / max 11.7 mm, hair p99 '
       '11.7 / max 25 mm, IoU 0.997, SSIM 0.995; UV audit 0 LOD0 escapes; gates no worse. **Below the ~15 % floor: no guarded step '
       'saves 15 % (best -9.2 %); orchestrator may record kept.** Earlier s82 (-14.8 %) installed and rolled back for 72 UV escapes | '
       '`mm9_wingedmutant_reduce_claude/` (candidate `export_mp/mm9_wingedmutant.glb`) | `mm9_wingedmutant_reduce_claude/before/mm9_wingedmutant.glb` (sha256 441ffa7890ae) |')
idx = [i for i, l in enumerate(lines) if l.startswith('| 36 | ') and '`mm9_wingedmutant.glb`' in l]
assert len(idx) == 1, idx
lines[idx[0]] = new
tmp = P.with_suffix('.md.tmp_wingedmutant'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 36 updated')
