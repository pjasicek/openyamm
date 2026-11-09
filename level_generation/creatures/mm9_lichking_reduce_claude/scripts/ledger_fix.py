#!/usr/bin/env python3
"""One-off repair (2026-11-04): a shared scratchpad helper was overwritten by the Giant agent's copy, so the Igrid row text landed on
the Giant row. Restores the Giant row (reconstructed: status, project, rollback source) and puts Igrid's final row on row 4.
Run from level_generation/creatures under the reduction_ledger flock."""
import os, sys
path = 'REDUCTION_LEDGER.md'; igrid = sys.argv[1]
giant = ('| 2 | Giant | `mm9_giant.glb` | 15,670 | | | reducing (giant-reduce-20261104, 2026-11-04) | `mm9_giant_reduce_claude/` | '
         '`mm9_giant_reduce_claude/before/mm9_giant.glb` (sha256 70612b5aee8e) |')
lines = open(path).read().split('\n')
rows4 = [i for i, l in enumerate(lines) if l.startswith('| 4 | Igrid')]
has2 = [i for i, l in enumerate(lines) if l.startswith('| 2 | Giant')]
assert len(rows4) == 2 and not has2, (rows4, has2)
lines[rows4[0]] = giant; lines[rows4[1]] = igrid
tmp = path + '.tmp_wyrdold_fix'; open(tmp, 'w').write('\n'.join(lines)); os.replace(tmp, path)
print('FIXED', rows4)
