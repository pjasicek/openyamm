import sys, collections
lines=[l.rstrip('\r\n').split('\t') for l in open(sys.argv[1],encoding='latin-1')]
hdr=None
for r in lines:
    if r and r[0].strip()=='220': hdr=r; break
cols=[(i,int(c)) for i,c in enumerate(hdr) if i>=7 and c.strip().isdigit()]
rows={}; names={}
i=0
while i<len(lines):
    r=lines[i]
    if r and r[0].strip().isdigit():
        rid=int(r[0]); names[rid]=r[1].strip()
        row=list(r)
        while len(row)<=cols[-1][0] and i+1<len(lines) and lines[i+1] and not lines[i+1][0].strip().isdigit():
            row+=lines[i+1][1:]; i+=1
        rows[rid]=row
    i+=1
cells=collections.Counter(); res={}
for rid,row in rows.items():
    for ci,tid in cols:
        c=row[ci].strip() if ci<len(row) else ''
        cells[c if not c.isdigit() else 'num']+=1
        if c.isdigit(): res[(rid,tid)]=int(c)
print(cells.most_common(10))
pairs={}
asym=[]
for (a,b),v in res.items():
    k=tuple(sorted((a,b)))
    if (b,a) in res and res[(b,a)]!=v: asym.append((a,b,v,res[(b,a)]))
    pairs.setdefault(k,set()).add(v)
print('directed',len(res),'unordered',len(pairs),'asym',asym[:5])
for (a,b),v in sorted(pairs.items()):
    print(a,names.get(a),'+',b,names.get(b),'=',sorted(v),[names.get(x) for x in v], 'oneway' if (b,a) not in res or (a,b) not in res else '')
# other cells
for rid,row in rows.items():
    for ci,tid in cols:
        c=row[ci].strip() if ci<len(row) else ''
        if c and c.lower()!='no' and not c.isdigit(): print('odd',rid,tid,c)
