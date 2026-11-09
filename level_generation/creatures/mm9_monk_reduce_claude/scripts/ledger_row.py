"""Replace the Monk's row (16, `mm9_monk.glb`) of REDUCTION_LEDGER.md. Run inside
flock claude_shared/locks/reduction_ledger.lock from level_generation/creatures; the file is re-read here.
Usage: ledger_row.py "<full new row>" """
import sys, os
path = 'REDUCTION_LEDGER.md'; new = sys.argv[1]
lines = open(path).read().split('\n')
idx = [i for i, l in enumerate(lines) if '| `mm9_monk.glb` |' in l and l.startswith('| 16 |')]
assert len(idx) == 1, idx
assert new.startswith('| 16 |') and '`mm9_monk.glb`' in new
lines[idx[0]] = new
tmp = path + '.tmp_monk'; open(tmp, 'w').write('\n'.join(lines)); os.replace(tmp, path); print('ROW', new)
