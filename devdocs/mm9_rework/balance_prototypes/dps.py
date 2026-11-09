import re,statistics as st
H='/home/pjasicek/github/OpenYAMM/assets_dev/'
def load(p):
    out=[]
    for l in open(p,encoding='latin-1').read().splitlines()[3:]:
        c=l.split('\t')
        if len(c)<28 or not c[0].strip().isdigit(): continue
        try: lvl=int(c[3]); hp=int(c[4]); rec=float(c[14] or 0); spd=float(c[13] or 0)
        except: continue
        if lvl<=0: continue
        out.append(dict(id=int(c[0]),name=c[1],lvl=lvl,hp=hp,rec=rec,spd=spd,c=c))
    return out
def dmg(s):
    m=re.match(r'\s*(\d+)[dD](\d+)\s*([+-]\s*\d+)?',s or '')
    if not m:
        try: return float(s)
        except: return 0
    return int(m.group(1))*(int(m.group(2))+1)/2+(int(m.group(3).replace(' ','')) if m.group(3) else 0)
def pct(s):
    try: return float(s)/100
    except: return 0
def hitp(ac,lvl):
    U=max(1,ac+2*lvl+10); need=ac+5  # roll in 1..U, hit if roll > need (bonus 0)
    return max(0,U-need)/U
def stats(m):
    c=m['c']; d1=dmg(c[18]); d2=dmg(c[22]); a2=pct(c[20])
    d=d1*(1-a2)+d2*a2
    ac=int(2.5*m['lvl']+15)
    rec=m['rec'] if m['rec']>0 else 100
    ranged = (c[19].strip() not in ('','0'))
    spell = pct(c[24]) if c[25].strip() not in ('','0') else 0
    return d, d*hitp(ac,m['lvl'])/rec*100, ranged, spell, rec
eng=load(H+'engine/data_tables/monster_data.txt')
mm9=[m for m in load(H+'worlds/mm9/data_tables/monster_data.txt') if not re.search(r'Commoner|Town|Shopkeeper|Prisoner|Guard|Peasant|Cow|Goat|Hen|Rooster|Pig|Ewe|Ram|cat|dog|mouse|Fish|RailTest',m['name']) and dmg(m['c'][18])>0]
bands=[(1,5),(6,10),(11,15),(16,20),(21,30),(31,40),(41,55),(56,80),(81,120)]
print('band     | ENG dmg/hit  dmg per 100 rec-ticks  rec  ranged spell% | MM9 same | ratio DPS')
for a,b in bands:
    r=[]
    for src in (eng,mm9):
        xs=[stats(m) for m in src if a<=m['lvl']<=b]
        r.append((len(xs),st.median(x[0] for x in xs),st.median(x[1] for x in xs),st.median(x[4] for x in xs),sum(x[2] for x in xs)/len(xs),st.mean(x[3] for x in xs)))
    e,n=r
    print(f'L{a:3d}-{b:3d} | {e[1]:5.1f} {e[2]:6.2f} {e[3]:5.0f} {e[4]*100:3.0f}% {e[5]*100:3.0f}% | n={n[0]:2d} {n[1]:5.1f} {n[2]:6.2f} {n[3]:5.0f} {n[4]*100:3.0f}% {n[5]*100:3.0f}% | {n[2]/e[2]:4.2f}')
# spells skill/mastery
def spl(m):
    s=m['c'][25].strip()
    mm=re.match(r'([^,]+),\s*(\w+)\s*,\s*(\d+)',s)
    return (mm.group(1).strip(),mm.group(2),int(mm.group(3))) if mm else None
print()
for a,b in bands:
    for tag,src in (('ENG',eng),('MM9',mm9)):
        sp=[spl(m) for m in src if a<=m['lvl']<=b and spl(m)]
        if sp: print(tag,f'L{a}-{b}',len(sp),'casters; skill med',st.median(x[2] for x in sp),' masteries',{k:sum(1 for x in sp if x[1]==k) for k in set(x[1] for x in sp)})
