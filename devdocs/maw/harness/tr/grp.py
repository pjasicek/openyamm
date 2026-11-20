exec(open("common.py").read())
import re, collections
src=open('/home/pjasicek/github/Maw-Mod-MMMerge/Scripts/Global/zzMAW_MoveTrainers.lua').read().split('\n')
cur=None; moves=[]
for i,l in enumerate(src):
    m=re.search(r'\["([^"]+)"\]',l)
    if m: cur=m.group(1)
    for a,b in re.findall(r'\{(\d+),(\d+)\}',l): moves.append((cur,int(a),int(b),i+1))
home_map={172:'out06',173:'out06',174:'out06',175:'out03',176:'out02',177:'out03',178:'d17',179:'d17',180:'d17',
 214:'out04',215:'out07',216:'out01',530:'7out02',531:'out09',532:'7out03',533:'7out02',534:'out09',535:'7out03',536:'7out04',537:'out14',538:'7out02'}
g=collections.OrderedDict()
for mp,n,h,ln in moves:
    g.setdefault(n,[]).append((mp,h,ln))
short={'Thieves guild':'thieves','Merc Guild':'merc','Tavern':'tavern','Temple':'temple','Training':'training','House':'house'}
rows=[]
for n in sorted(g):
    r=npc[n]; home=int(r[6])
    t=None
    for i in range(10,16):
        v=r[i].strip()
        if v.isdigit() and int(v) in tt: t=int(v); break
    adds=['%s %d %s'%(mp.replace('.odm','').replace('.blv',''),h,house[h][5]) for mp,h,ln in g[n] if h!=home]
    rest=[mp.replace('.odm','').replace('.blv','') for mp,h,ln in g[n] if h==home]
    rows.append('| %d %s | %s (%d) | %d %s, %s | %s | %s |'%(n,r[1].strip(),tt[t][1].strip(),t,home,house[home][5],home_map[n],'; '.join(adds),', '.join(rest) or '-'))
print('\n'.join(rows))
print(max(len(x) for x in rows))
