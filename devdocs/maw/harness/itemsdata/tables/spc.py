import sys
sys.path.insert(0, sys.argv[1])
import tt
WS = ' \t\n\v\f\r'
def entries(p):
    rows, _ = tt.parse(p)
    out = []
    for li, r in enumerate(rows):
        c = lambda i: r[i].strip(WS) if i < len(r) else ''
        if c(0) == '' or c(1) == '' or c(0) == 'Bonus Stat':
            continue
        out.append((li + 1, r))
    return out
for p in sys.argv[2:]:
    e = entries(p)
    print(p.split('/')[-2], len(e))
    for i, (li, r) in enumerate(e, 1):
        if i > 70 or i < 3:
            print('  ', i, 'line', li, [x.strip(WS) for x in r[:17]])
