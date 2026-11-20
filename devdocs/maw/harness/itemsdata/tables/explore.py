import sys
sys.path.insert(0, sys.argv[1])
import tt
S = sys.argv[2]; D = sys.argv[3]
for name, p in [('base', S+'/base/ITEMS.txt'), ('maw', S+'/maw/ITEMS.txt'), ('ours', D+'/items.txt')]:
    for enc in ['latin-1', 'utf-8']:
        try:
            rows, q = tt.parse(p, enc)
        except Exception as e:
            print(name, enc, 'ERR', e); continue
        ids = [r[0] for r in rows if r and r[0].strip().isdigit()]
        widths = {}
        for r in rows: widths[len(r)] = widths.get(len(r), 0) + 1
        print(name, enc, 'rows', len(rows), 'idrows', len(ids), 'unterminated', q, 'min', ids[0], 'max', ids[-1],
              'dups', len(ids) - len(set(ids)), 'widths', sorted(widths.items())[:12])
        nonid = [(i, r[:3]) for i, r in enumerate(rows) if not (r and r[0].strip().isdigit())]
        print('  nonid', nonid[:10], len(nonid))
        ints = [int(x) for x in ids]
        gaps = [(a, b) for a, b in zip(ints, ints[1:]) if b != a + 1]
        print('  gaps', gaps[:20])
        break
