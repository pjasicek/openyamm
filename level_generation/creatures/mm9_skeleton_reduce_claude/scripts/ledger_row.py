#!/usr/bin/env python3
"""Ledger row 40 (Skeleton) of REDUCTION_LEDGER.md's MM9 section, fix pass: re-read inside the flock, replace the row, temp file +
rename. Run as: flock level_generation/creatures/claude_shared/locks/reduction_ledger.lock python3 <this> (repo root)."""
import os
from pathlib import Path
P = Path('level_generation/creatures/REDUCTION_LEDGER.md'); lines = P.read_text().split('\n')
new = ('| 40 | 1 monster | Skeleton | `mm9_skeleton.glb` | 12,438 | 10,508 (-15.5 %) | 5,019 / 1,741 (LOD3 595 not in chain, as installed) | '
       'ready for review (fix pass, chart guard, UV audit 0) 2026-11-04 (skeleton-reduce-fix-20261104): mpqem per bone piece '
       '(half-edge, every vertex an installed vertex, 293 poses, W5 4, two-tier texture guard, MP_CHART=1 + the audit\'s own '
       'chart test per collapse, joint contacts locked 7 mm, gap growth <= 1 mm), ladder c1 r77 (p99 5.12 / max 9.4 mm, IoU 0.989); '
       'skull face, mandible, teeth, eyes, neck, dagger, tali, small pieces and five sheets exact; dome/ropes 0.7, hands 0.6-0.8, '
       'back panel 0.4 (lining re-emitted); UV audit LOD0 0/0/0; face identical both tiers; gates equal or better (detached: the '
       'installed 4, talus 10.1 -> 9.3 mm). Earlier: h85 installed and rolled back 2026-11-04 (75 faces off the UV charts) | '
       '`mm9_skeleton_reduce_claude/` (candidate `export_c77/mm9_skeleton.glb`) | `mm9_skeleton_reduce_claude/before/mm9_skeleton.glb` (sha256 cf916007ce3a) |')
idx = [i for i, l in enumerate(lines) if l.startswith('| 40 | ') and '`mm9_skeleton.glb`' in l]
assert len(idx) == 1, idx
lines[idx[0]] = new
tmp = P.with_suffix('.md.tmp_skeleton'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 40 updated')
