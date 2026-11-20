import json
def load(p):
    return [l.rstrip('\r\n').split('\t') for l in open(p,encoding='latin-1')]
oy=load('OpenYAMM/assets_dev/engine/data_tables/spells.txt')
mm=load('OpenYAMM/reference/mmmerge/Data/Tables/Spells2.txt')
fo=load('OpenYAMM/reference/mmerge_data_forus/Data/Tables/Spells2.txt')
maw=load('Maw-Mod-MMMerge/Data/Tables/Spells2.txt')
OY={}
for r in oy[1:]:
    if r[0].isdigit() and len(r)>=24:
        OY[int(r[0])]=dict(name=r[2],cost=list(map(int,r[11:15])),delay=list(map(int,r[15:19])),add=int(r[22]),dice=int(r[23]))
def t2(rows):
    d={}
    for i,r in enumerate(rows[1:]):
        if len(r)<11 or r[0]=='' : continue
        d[i]=dict(name=r[0],cost=list(map(int,r[1:5])),delay=list(map(int,r[5:9])),add=int(r[9]),dice=int(r[10]))
    return d
MM=t2(mm);FO=t2(fo);MAW=t2(maw)
out={}
for i in range(1,133):
    out[i]=dict(oy=OY.get(i),mm=MM.get(i),fo=FO.get(i),maw=MAW.get(i))
json.dump(out,open('/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/67306c2b-0ca8-4c66-afad-4546c9e2b3bb/scratchpad/spells/tables.json','w'),indent=0)
# differences OY vs MM
for i in range(1,133):
    o,m,f,w=OY.get(i),MM.get(i),FO.get(i),MAW.get(i)
    if not o or not m: print(i,'missing',bool(o),bool(m)); continue
    if o['name']!=m['name']: print(i,'name',o['name'],'|',m['name'])
    for k in ('cost','delay','add','dice'):
        if o[k]!=m[k] or o[k]!=f[k]: print(i,o['name'],k,'oy',o[k],'mm',m[k],'forus',f[k])
