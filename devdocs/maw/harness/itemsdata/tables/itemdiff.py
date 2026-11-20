import sys
sys.path.insert(0, sys.argv[1])
import tt
S = sys.argv[2]; D = sys.argv[3]
def load(p):
    rows, _ = tt.parse(p)
    hdr = rows[1]
    m = {}
    for r in rows:
        if r and r[0].strip().isdigit():
            m[int(r[0].strip())] = r
    return hdr, m
hb, B = load(S+'/base/ITEMS.txt'); hm, M = load(S+'/maw/ITEMS.txt'); ho, O = load(D+'/items.txt')
print('hdr base==maw', hb == hm, 'ours hdr', ho[17:])
def cell(r, i): return r[i].strip() if i < len(r) else ''
def diffs(a, b, n=17):
    return [(i, cell(a, i), cell(b, i)) for i in range(n) if cell(a, i) != cell(b, i)]
which = sys.argv[4]
if which == 'bm':
    X, Y = B, M
else:
    X, Y = B, O
print('only in first', sorted(set(X) - set(Y)), 'only in second', sorted(set(Y) - set(X)))
rawonly = 0
for k in sorted(set(X) & set(Y)):
    d = diffs(X[k], Y[k])
    if not d:
        if X[k][:17] != Y[k][:17]: rawonly += 1
        continue
    print(k, cell(X[k], 2), '|', '; '.join('%s: %r -> %r' % (hb[i], a[:60], b[:60]) for i, a, b in d))
print('rawonly', rawonly)
