import sys
rows=[]
for line in open(sys.argv[1],encoding='latin-1'):
    c=line.rstrip('\r\n').split('\t')
    if len(c)>16 and c[1].strip() and c[15].strip() in 'ABCD' and c[15].strip():
        rows.append(c)
print(len(rows))
lvl={'A':0,'B':1,'C':2,'D':3}
pools={3:[0,1],4:[0,1,2],5:[1,2,3],6:[3]}
slots=['W1','W2','Miss','Arm','Shld','Helm','Belt','Cape','Gaunt','Boot','Ring','Amul']
for p,ls in pools.items():
    tot=[0]*12
    for c in rows:
        if lvl[c[15].strip()] in ls:
            for v in range(12): tot[v]+=int(c[2+v] or 0)
    print(p, dict(zip(slots,tot)))
for i,c in enumerate(rows,1):
    print(i, c[1].strip(), c[15].strip(), [int(x or 0) for x in c[2:14]], c[14].strip())
