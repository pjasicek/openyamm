import sys, os
path = 'REDUCTION_LEDGER.md'; new = sys.argv[1]
lines = open(path).read().split('\n')
idx = [i for i, l in enumerate(lines) if '| `mm9_giant.glb` |' in l and l.startswith('| 2 |')]
assert len(idx) == 1, idx
lines[idx[0]] = new
tmp = path + '.tmp_giant'; open(tmp, 'w').write('\n'.join(lines)); os.replace(tmp, path); print('ROW', new)
