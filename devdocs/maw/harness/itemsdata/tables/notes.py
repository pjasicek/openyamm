import sys, difflib
sys.path.insert(0, sys.argv[1])
import tt
S = sys.argv[2]
def load(p):
    rows, _ = tt.parse(p)
    return {int(r[0]): r for r in rows if r and r[0].strip().isdigit()}
B = load(S+'/base/ITEMS.txt'); M = load(S+'/maw/ITEMS.txt')
for k in sorted(B):
    a = B[k][16].strip(); b = M[k][16].strip()
    if a == b: continue
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ops = [o for o in sm.get_opcodes() if o[0] != 'equal']
    print(k, B[k][2], B[k][8], ' || '.join('%s %r->%r' % (t, a[i1:i2], b[j1:j2]) for t, i1, i2, j1, j2 in ops)[:400])
# raw-only
for k in sorted(B):
    if [c.strip() for c in B[k]] == [c.strip() for c in M[k]] and B[k] != M[k]:
        print('RAW', k, [(i, B[k][i], M[k][i]) for i in range(len(B[k])) if B[k][i] != M[k][i]])
