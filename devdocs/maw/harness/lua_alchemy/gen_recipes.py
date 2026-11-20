import sys, collections
lines=[l.rstrip('\r\n').split('\t') for l in open('lod/POTION.TXT',encoding='latin-1')]
hdr=[r for r in lines if r and r[0].strip()=='220'][0]
cols=[(i,int(c)) for i,c in enumerate(hdr) if i>=7 and c.strip().isdigit()]
rows={}; i=0
while i<len(lines):
    r=lines[i]
    if r and r[0].strip().isdigit():
        rid=int(r[0]); row=list(r)
        while len(row)<=cols[-1][0] and i+1<len(lines) and lines[i+1] and not lines[i+1][0].strip().isdigit():
            row+=lines[i+1][1:]; i+=1
        rows[rid]=row
    i+=1
names={}
for l in open('lod/ITEMS.txt',encoding='latin-1'):
    f=l.split('\t')
    if f and f[0].isdigit(): names[int(f[0])]=f[2]
mast={}
for l in open('/home/pjasicek/github/Maw-Mod-MMMerge/Data/Tables/Potion settings.txt',encoding='latin-1'):
    f=l.rstrip('\r\n').split('\t')
    if f[0].isdigit() and f[2].isdigit(): mast[int(f[1])]=int(f[2])
targets={c for _,c in cols}
pairs={}
for rid,row in rows.items():
    if rid not in targets: continue
    for ci,tid in cols:
        c=row[ci].strip() if ci<len(row) else ''
        if c.isdigit():
            k=tuple(sorted((rid,tid)))
            assert pairs.get(k,int(c))==int(c); pairs[k]=int(c)
mn=['None','Novice','Expert','Master','Grandmaster']
tier={1:'secondary',2:'tertiary',3:'white',4:'black'}
out=[]
for (a,b),res in sorted(pairs.items(), key=lambda kv:(mast.get(kv[1],0),kv[1],kv[0])):
    m=mast.get(res,0)
    t='black' if res>=252 else ('white' if res>=240 else ('tertiary' if res>=228 else 'secondary'))
    out.append(f"  - {{a: {a}, b: {b}, result: {res}, mastery: {mn[m]}, tier: {t}}}  # {names[a]} + {names[b]} = {names[res]}")
print(len(pairs), file=sys.stderr)
print("\n".join(out))
