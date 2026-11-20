import re, json
F='/home/pjasicek/github/Maw-Mod-MMMerge/Scripts/General/zzMaw-Monsters.lua'
src=open(F,encoding='latin1').read().split('\n')
occ={}
sect=None
for i in range(962,1592):
    l=src[i]
    if l.startswith('--MM'): sect=l[2:].strip()
    m=re.match(r'^\["([^"]*)"\]',l)
    if m:
        v=re.findall(r'\["(Low|Mid|High)"\]\s*=\s*([0-9.]+)',src[i+1])
        occ.setdefault(m.group(1),[]).append((i+1,sect,{k:float(x) for k,x in v}))
def load(path,hl):
    rows=[]
    for ln in open(path,encoding='latin1').read().replace('\r','').split('\n'):
        c=ln.split('\t')
        if c and c[0].strip().isdigit(): rows.append((int(c[0]),c[1],c[2].strip()))
    return rows
oy=load('/home/pjasicek/github/OpenYAMM/assets_dev/engine/data_tables/map_stats.txt',2)
maw=load('zmawT/mapstats.txt',2)
L={}
for ln in open('lua/maps.tsv'):
    p=ln.rstrip('\n').split('\t')
    if p[0]=='L': L[p[1]]=tuple(float(x) for x in p[2:5])
res={}
for name in L:
    oyf=[(i,f) for i,n,f in oy if n==name and i<1000]
    mwf=[(i,f) for i,n,f in maw if n==name]
    res[name]={'oy':oyf,'maw':mwf,'occ':occ[name],'eff':L[name]}
json.dump(res,open('resolve.json','w'),indent=0)
un=[n for n in res if not res[n]['oy']]
print('unresolved in OY:',un)
print('unresolved in MAW:',[n for n in res if not res[n]['maw']])
print('oy!=maw:',[(n,res[n]['oy'],res[n]['maw']) for n in res if res[n]['oy']!=res[n]['maw']])
# maps (maw mapstats) without mapLevels entry
names=set(L)
print('MAW mapstats rows w/o mapLevels:',[(i,n,f) for i,n,f in maw if n not in names])
