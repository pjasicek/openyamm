import sys, json
def load(path, hdr_line):
    lines = open(path, encoding='latin1').read().replace('\r','').split('\n')
    hdr = [h.strip() for h in lines[hdr_line].split('\t')]
    rows = {}
    order = []
    for ln in lines:
        c = ln.split('\t')
        if c and c[0].strip().isdigit():
            k = int(c[0])
            if k in rows: k = (k, len(order))
            rows[k] = [x.strip() for x in c]
            order.append(k)
    return hdr, rows, order
which = sys.argv[1]
B='/home/pjasicek/github/OpenYAMM/reference/mmerge_data_forus/Data/mmmerge.T.lod/'
O='/home/pjasicek/github/OpenYAMM/assets_dev/engine/data_tables/'
if which=='mon':
    hb, b, bo = load(B+'MONSTERS.txt', 1); hm, m, mo = load('zmawT/MONSTERS.txt', 1); ho, o, oo = load(O+'monster_data.txt', 1)
else:
    hb, b, bo = load(B+'MapStats.txt', 2); hm, m, mo = load('zmawT/mapstats.txt', 2); ho, o, oo = load(O+'map_stats.txt', 2)
print('headers equal base/maw', hb==hm, 'base/oy', hb==ho[:len(hb)], len(hb), len(ho))
for i,(x,y) in enumerate(zip(hb,ho)):
    if x!=y: print('hdr diff col',i,repr(x),repr(y))
print('ids base', len(b), 'maw', len(m), 'oy', len(o))
print('only base', [k for k in b if k not in m]); print('only maw', [k for k in m if k not in b])
out=[]
for k in bo:
    if k not in m: continue
    rb, rm = b[k], m[k]
    n=max(len(rb),len(rm))
    rb=rb+['']*(n-len(rb)); rm=rm+['']*(n-len(rm))
    ro = o.get(k)
    diffs=[]
    for i in range(n):
        if rb[i]!=rm[i]:
            col = hb[i] if i < len(hb) else f'col{i}'
            ov = ro[i] if ro and i < len(ro) else None
            diffs.append((i, col, rb[i], rm[i], ov))
    if diffs:
        out.append({'id':k,'name':rb[1],'extra':rb[2] if which=='mon' else rb[2],'diffs':diffs,
                    'oy_same_row': bool(ro) and ro[1]==rb[1], 'oy_row_eq_base': bool(ro) and ro[:len(rb)]==rb[:len(ro)]})
json.dump(out, open(which+'_diff.json','w'), indent=0)
print('rows changed', len(out))
from collections import Counter
print(Counter(d[1] for r in out for d in r['diffs']))
# oy vs base divergence for all rows
dv=0
for k in bo:
    if k in o:
        rb=b[k]; ro=o[k]
        if ro[:len(rb)]!=rb: dv+=1
print('oy rows diverging from base (any col):', dv)
