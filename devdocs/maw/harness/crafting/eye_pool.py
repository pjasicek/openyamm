import sys
rows=[l.rstrip('\r\n').split('\t') for l in open(sys.argv[1],encoding='latin-1')]
data=[r for r in rows[4:] if len(r)>15 and r[1].strip()]
slots=['W1','W2','Miss','Arm','Shld','Helm','Belt','Cape','Gaunt','Boot','Ring','Amul']
pool={s:[] for s in slots}
for i,r in enumerate(data):
    lvl=r[15].strip()
    if lvl!='D': continue
    for k,s in enumerate(slots):
        w=int(r[2+k] or 0)
        if w>0: pool[s].append((i+1,r[1].strip(),w))
for s in slots:
    tot=sum(w for _,_,w in pool[s])
    print(f"{s} total={tot}: "+", ".join(f"{b} {n} {100*w/tot:.1f}%" for b,n,w in pool[s]))
print(len(data))
