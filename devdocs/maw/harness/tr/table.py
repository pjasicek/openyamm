exec(open("common.py").read())
import re
src=open('/home/pjasicek/github/Maw-Mod-MMMerge/Scripts/Global/zzMAW_MoveTrainers.lua').read().split('\n')
cur=None; moves=[]
for i,l in enumerate(src):
    m=re.search(r'\["([^"]+)"\]',l)
    if m: cur=m.group(1)
    for a,b in re.findall(r'\{(\d+),(\d+)\}',l): moves.append((cur,int(a),int(b),i+1))
mapname={r[2]:r[1] for r in ms.values() if len(r)>2}
def teach(r):
    for i in range(10,16):
        v=r[i].strip() if i<len(r) else ''
        if v.isdigit() and int(v) in tt: return int(v), tt[int(v)][1].strip()
    return None,''
print('relocations')
n=0
for mp,npcid,h,ln in moves:
    r=npc[npcid]; home=int(r[6])
    if home==h: continue
    n+=1
    t,tn=teach(r)
    hr=house[h]; hh=house[home]
    print('| %d | %s | %s (topic %d) | %d %s (%s) | %s %s | %d %s (%s) | %d |'%(npcid,r[1].strip(),tn,t,home,hh[5],hh[2],mp,mapname.get(mp,''),h,hr[5],hr[2],ln))
print(n)
print('restores')
for mp,npcid,h,ln in moves:
    r=npc[npcid]; home=int(r[6])
    if home!=h: continue
    print('%d %s -> %d %s on %s (line %d)'%(npcid,r[1].strip(),h,house[h][5],mp,ln))
print(len(moves))
