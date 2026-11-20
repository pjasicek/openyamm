"""Replace Ebora's row in REDUCTION_LEDGER.md (call under the flock). Usage: ledger_row.py '<full row text>'"""
import os, sys, tempfile
path = os.path.join(os.path.dirname(__file__), '../../REDUCTION_LEDGER.md')
path = os.path.realpath(path)
row = sys.argv[1]
lines = open(path).read().split('\n')
hits = [i for i, l in enumerate(lines) if l.startswith('| 3 |') and 'Ebora / Concubine' in l and '`mm9_ebora.glb`' in l]
assert len(hits) == 1, hits
lines[hits[0]] = row
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
with os.fdopen(fd, 'w') as f:
    f.write('\n'.join(lines))
os.chmod(tmp, os.stat(path).st_mode & 0o777)
os.replace(tmp, path)
print('ledger row updated')
