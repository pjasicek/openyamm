import sys
sys.path.insert(0, sys.argv[1])
import tt
WS = ' \t\n\v\f\r'
def load(p):
    rows, _ = tt.parse(p)
    return rows
def keyed(rows):
    return {int(r[0].strip(WS)): r for r in rows if r and r[0].strip(WS).isdigit()}
a = load(sys.argv[2]); b = load(sys.argv[3])
mode = sys.argv[4]
if mode == 'id':
    A = keyed(a); B = keyed(b)
    print('onlyA', sorted(set(A)-set(B))[:20], 'onlyB', sorted(set(B)-set(A))[:20])
    for k in sorted(set(A) & set(B)):
        n = max(len(A[k]), len(B[k]))
        c = lambda r, i: r[i].strip(WS) if i < len(r) else ''
        d = [(i, c(A[k], i)[:50], c(B[k], i)[:50]) for i in range(n) if c(A[k], i) != c(B[k], i)]
        if d: print(k, d)
else:
    for i in range(max(len(a), len(b))):
        ra = a[i] if i < len(a) else None; rb = b[i] if i < len(b) else None
        if ra != rb: print(i, ra, '\n   ', rb)
