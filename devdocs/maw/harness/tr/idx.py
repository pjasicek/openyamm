exec(open("common.py").read())
import collections
by=collections.defaultdict(list)
for n,r in npc.items():
    for i in range(10,16):
        v=r[i].strip() if i<len(r) else ''
        if v.isdigit() and int(v) in tt: by[int(v)].append(n)
for t in sorted(tt):
    if 'Alchemy' in tt[t][1] or 'Learning' in tt[t][1] or 'Armsmaster' in tt[t][1] or 'Regen' in tt[t][1] or 'Dodg' in tt[t][1] or 'Unarmed' in tt[t][1] or 'Monster' in tt[t][1] or 'Vampire' in tt[t][1] or 'Elf' in tt[t][1] or 'Dragon' in tt[t][1]:
        print(t,tt[t][1].strip(),'skill',tt[t][2],'m',tt[t][3])
        for n in by[t]:
            h=int(npc[n][6]); print('   ',n,npc[n][1],'->',hname(h))
