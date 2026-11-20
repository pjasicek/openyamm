import csv, re, collections, statistics as st
E='/home/pjasicek/github/OpenYAMM/assets_dev/engine/data_tables/'
M='/home/pjasicek/github/OpenYAMM/assets_dev/worlds/mm9/data_tables/'
def rd(p, skip=0):
    lines=open(p,encoding='latin-1').read().splitlines()[skip:]
    return list(csv.DictReader(lines,delimiter='\t'))
eng=[r for r in rd(E+'items.txt',1) if r.get('Item #','').strip().isdigit()]
mm9=rd(M+'items.txt')
# engine tier from random_items weights
w={}
for line in open(E+'random_items.txt',encoding='latin-1').read().splitlines()[4:]:
    c=line.split('\t')
    if c and c[0].isdigit():
        ws=[int(x) if x.strip().isdigit() else 0 for x in c[2:8]]
        if sum(ws): w[c[0]]=sum((i+1)*x for i,x in enumerate(ws))/sum(ws)
def dice(s):
    m=re.fullmatch(r'(\d+)d(\d+)',s.strip())
    return int(m.group(1))*(int(m.group(2))+1)/2 if m else 0
def num(s):
    try: return int(s)
    except: return 0
def wkey(r):
    es=r['Equip Stat']; sk=r['Skill Group']
    if es in('Weapon','Weapon2','Weapon1or2','Missile'):
        h={'Weapon':'1H','Weapon1or2':'1/2H','Weapon2':'2H','Missile':'ranged'}[es]
        return f'{sk} {h}'
    if es=='Armor': return f'Armor {sk}'
    return es
rare=('Artifact','Relic','Special')
def stats(r):
    es=r['Equip Stat']
    if es in('Weapon','Weapon2','Weapon1or2','Missile'):
        return dice(r['Mod1'])+num(r['Mod2']), num(r['Mod2'])
    return num(r['Mod1'])+num(r['Mod2']), 0
print('== ENGINE (MM6-8) normal items: key | tier | avg dmg or AC | +attack | names')
groups=collections.defaultdict(list)
for r in eng:
    if r['material'] in rare: continue
    t=w.get(r['Item #'])
    if t is None: continue
    groups[(wkey(r),round(t))].append(r)
for k in sorted(groups):
    rs=groups[k]
    s=[stats(r) for r in rs]
    print(f'{k[0]:22s} L{k[1]}  {st.mean(x[0] for x in s):5.1f}  +{st.mean(x[1] for x in s):4.1f}  n={len(rs)} price~{int(st.mean(num(r["Value"]) for r in rs))}')
print('\n== MM9 normal items')
g9=collections.defaultdict(list)
for r in mm9:
    if r['material'] in rare or r['Equip Stat'] in('Mscroll','LearnSkill','Misc'): continue
    g9[(wkey(r),int(r['normalized_tier']))].append(r)
for k in sorted(g9):
    rs=g9[k]; s=[stats(r) for r in rs]
    print(f'{k[0]:22s} L{k[1]}  {st.mean(x[0] for x in s):5.1f}  +{st.mean(x[1] for x in s):4.1f}  n={len(rs)} price~{int(st.mean(num(r["Value"]) for r in rs))}  {", ".join(r["Name"] for r in rs)}')
