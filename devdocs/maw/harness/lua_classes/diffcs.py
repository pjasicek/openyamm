import sys
def load(p):
    rows=[l.rstrip('\n').replace('\r','').split('\t') for l in open(p,encoding='latin-1')]
    hdr=rows[0][1:]
    d={}
    for r in rows[1:]:
        if not r or not r[0]: continue
        d[r[0]]=r[1:]
    return hdr,d
bh,bd=load(sys.argv[1]); mh,md=load(sys.argv[2])
names=list(bd.keys())
for sk in names:
    if sk not in md: continue
    ch=[]
    for i,c in enumerate(bh):
        if i>=len(mh): break
        b=bd[sk][i] if i<len(bd[sk]) else ''
        m=md[sk][i] if i<len(md[sk]) else ''
        nb={"-":"0","=":"0","":"0","B":"N"}.get(b,b); nm={"-":"0","=":"0","":"0","B":"N"}.get(m,m)
        if nb!=nm: ch.append(f"{c} {b}>{m}")
    if ch: print(f"{sk}: "+", ".join(ch))
print("--- new classes")
for sk in md:
    row=md[sk][53:65]
    if any(x not in ('-','') for x in row):
        print(sk, ' '.join(row))
