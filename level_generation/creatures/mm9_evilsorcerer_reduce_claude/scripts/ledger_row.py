"""Replace this project's own row (26, mm9_evilsorcerer.glb) of REDUCTION_LEDGER.md; run inside the ledger flock from
level_generation/creatures. Usage: ledger_row.py '<new row>'"""
import os, sys
path = 'REDUCTION_LEDGER.md'; new = sys.argv[1]
lines = open(path).read().split('\n')
idx = [i for i, l in enumerate(lines) if '| `mm9_evilsorcerer.glb` |' in l and l.startswith('| 26 |')]
assert len(idx) == 1, idx
lines[idx[0]] = new
tmp = path + '.tmp_evilsorcerer'; open(tmp, 'w').write('\n'.join(lines)); os.replace(tmp, path); print('ROW', new)
