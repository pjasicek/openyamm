import re,statistics as st,collections
def load(p):
    L=open(p,encoding='latin-1').read().splitlines()
    hdr=L[1].split('\t'); out=[]
    for l in L[3:]:
        c=l.split('\t')
        if len(c)<20 or not c[0].strip().isdigit(): continue
        try: lvl=int(c[3]); hp=int(c[4]); ac=int(c[5]); xp=int(c[6])
        except: continue
        if lvl<=0: continue
        out.append(dict(id=int(c[0]),name=c[1],pic=c[2],lvl=lvl,hp=hp,ac=ac,xp=xp,c=c))
    return hdr,out
def dmg(s):
    m=re.match(r'\s*(\d+)[dD](\d+)\s*([+-]\s*\d+)?',s or '')
    if not m: return 0
    return int(m.group(1))*(int(m.group(2))+1)/2+(int(m.group(3).replace(' ','')) if m.group(3) else 0)
H='/home/pjasicek/github/OpenYAMM/assets_dev/'
hdr,eng=load(H+'engine/data_tables/monster_data.txt')
_,mm9=load(H+'worlds/mm9/data_tables/monster_data.txt')
print([ (i,h) for i,h in enumerate(hdr)][:30])
di=[i for i,h in enumerate(hdr) if h.strip()=='Damage']
print('damage cols',di)
mm9=[m for m in mm9 if not re.search(r'Commoner|Town|Shopkeeper|Prisoner|Guard|Peasant',m['name'])]
bands=[(1,5),(6,10),(11,15),(16,20),(21,30),(31,40),(41,55),(56,80),(81,200)]
def row(ms):
    if not ms: return '   -'
    return f"n={len(ms):3d} HP {st.median(m['hp'] for m in ms):5.0f} AC {st.median(m['ac'] for m in ms):3.0f} dmg {st.median(dmg(m['c'][di[0]]) for m in ms):5.1f} XP {st.median(m['xp'] for m in ms):6.0f}"
for a,b in bands:
    e=[m for m in eng if a<=m['lvl']<=b]; n=[m for m in mm9 if a<=m['lvl']<=b]
    print(f'L{a:3d}-{b:3d} ENG {row(e)} | MM9 {row(n)}')
print()
for m in sorted(mm9,key=lambda m:m['lvl']):
    print(m['id'],m['name'][:24].ljust(24),m['lvl'],m['hp'],m['ac'],m['xp'],m['c'][di[0]],'|',m['c'][di[1]] if len(di)>1 else '', '|', m['c'][7][:20])

print('\n=== treasure & resist by band')
def tre(s):
    s=s.strip(); gold=0; ch=0; tl=0
    m=re.match(r'(?:(\d+)%)?(?:(\d+)[dD](\d+))?\+?(?:L(\d))?',s)
    if not m: return 0,0,0
    pct=int(m.group(1)) if m.group(1) else (100 if m.group(4) else 0)
    if m.group(2): gold=int(m.group(2))*(int(m.group(3))+1)/2
    return gold, pct if m.group(4) else 0, int(m.group(4) or 0)
def res(m):
    vals=[]
    for v in m['c'][28:38]:
        try: vals.append(int(v))
        except: vals.append(0)
    return st.mean(vals), sum(1 for v in vals if v>=200)
for a,b in bands:
    for tag,src in (('ENG',eng),('MM9',mm9)):
        ms=[m for m in src if a<=m['lvl']<=b]
        if not ms: continue
        t=[tre(m['c'][7]) for m in ms]
        r=[res(m) for m in ms]
        print(f'L{a}-{b} {tag} gold avg {st.mean(x[0] for x in t):6.0f}  item chance avg {st.mean(x[1] for x in t):4.0f}%  avg TL(when item) {st.mean([x[2] for x in t if x[2]] or [0]):.1f}  res mean {st.mean(x[0] for x in r):4.0f} immune-schools {st.mean(x[1] for x in r):.2f}')
