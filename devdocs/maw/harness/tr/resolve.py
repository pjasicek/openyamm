import re,sys
T='/home/pjasicek/github/OpenYAMM/assets_dev/engine/data_tables/'
B='/home/pjasicek/github/OpenYAMM/reference/mmerge_data_forus/Data/mmmerge.T.lod/'
def rows(p,skip):
    out={}
    for l in open(p,encoding='latin-1').read().replace('\r','').split('\n')[skip:]:
        c=l.split('\t')
        if c and c[0].strip().isdigit(): out[int(c[0])]=c
    return out
npc=rows(T+'npc.txt',2); bnpc=rows(B+'NPCData.txt',2)
house=rows(T+'house_data.txt',2); bhouse=rows(B+'2DEvents.txt',2)
ms=rows(T+'map_stats.txt',3)
tt=rows(T+'teacher_topics.txt',1)
src=open('/home/pjasicek/github/Maw-Mod-MMMerge/Scripts/Global/zzMAW_MoveTrainers.lua').read()
cur=None; moves=[]
for l in src.split('\n'):
    m=re.search(r'\["([^"]+)"\]',l)
    if m: cur=m.group(1)
    for a,b in re.findall(r'\{(\d+),(\d+)\}',l): moves.append((cur,int(a),int(b)))
def hname(h):
    r=house.get(h)
    if not r: return '?%d'%h
    mi=int(r[3]) if r[3].strip().isdigit() else 0
    mp=ms.get(mi); 
    return '%d %s [%s] map%d=%s'%(h,r[5],r[2],mi,(mp[2]+' '+mp[1]) if mp else '?')
def topics(r):
    t=[]
    for i in range(10,16):
        v=r[i].strip() if i<len(r) else ''
        if v and v!='0':
            v=int(v); x=tt.get(v)
            t.append('%d:%s'%(v,x[1].strip() if x else 'nonteach'))
    return t
for mp,n,h in moves:
    r=npc[n]; br=bnpc[n]
    same = r[:16]==br[:16]
    old=int(r[6])
    print('%s\t%d\t%s\t%s\tOLD %s\tNEW %s\tsame=%s'%(mp,n,r[1],topics(r),hname(old),hname(h),same))
