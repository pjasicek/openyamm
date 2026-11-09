#!/usr/bin/env python3
"""Ledger row 56 (Skeleton Warrior / Master) of REDUCTION_LEDGER.md's MM9 section: re-read inside the flock, replace the row,
temp file + rename. Run as: flock level_generation/creatures/claude_shared/locks/reduction_ledger.lock python3 <this> (repo root)."""
import os
from pathlib import Path
P = Path('level_generation/creatures/REDUCTION_LEDGER.md'); lines = P.read_text().split('\n')
new = ('| 56 | 1 monster | Skeleton Warrior / Master | `mm9_skelwar.glb` | 10,484 | 8,838 (-15.7 %) | 3,668 / 1,350 / 578 (LOD3 = installed: '
       'every rebuild lost the thighs) | ready for review 2026-11-04 (skelwar-reduce-20261104): each rigid piece cut alone (texture '
       'weight 4, fold/volume/self-intersection/joint-gap checks, inflation), ladder d r95 (p99 4.97 / max 14.45 mm, IoU 0.992); skull '
       'face (visible cranium, mandible, eyes, teeth, neck), scimitar, grip faces, horns, brow insignia, pieces <= 30 faces kept '
       'exactly; cuirass 0.6, spine 0.7, boots 0.7, bracers 0.7, femurs/humeri 0.6, gauntlets 0.6-0.7, skirt plates 0.7-0.9, helmet '
       'shell 0.8 (linings rebuilt 1,574 -> 1,448); face pixel-identical in both tiers; skirt gate equal or better in every clip; '
       'arm gate +1 frame in AttackMelee2/Hit/ResurrectSpell (same contacts in renders); body was pre-cut per part at assembly, so '
       'no deeper cut | `mm9_skelwar_reduce_claude/` | `mm9_skelwar_reduce_claude/before/mm9_skelwar.glb` (sha256 56ac1e125ce8) |')
idx = [i for i, l in enumerate(lines) if l.startswith('| 56 | ') and '`mm9_skelwar.glb`' in l]
assert len(idx) == 1, idx
lines[idx[0]] = new
tmp = P.with_suffix('.md.tmp_skelwar'); tmp.write_text('\n'.join(lines)); os.replace(tmp, P); print('ROW 56 updated')
