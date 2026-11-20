M='/home/pjasicek/github/Maw-Mod-MMMerge/Data/Tables/'
B='/home/pjasicek/github/OpenYAMM/reference/mmerge_data_forus/Data/Tables/'
def rd(p): return [l.split('\t') for l in open(p,encoding='latin-1').read().replace('\r','').split('\n')]
b=rd(B+'Class Skills.txt'); m=rd(M+'Class Skills.txt'); z=rd(M+'Class Skillz.txt')
hp=rd(M+'Class HP SP.txt'); names=[r[0] for r in hp[1:] if r and r[0]]
ours={'Fire':'Fire','Leather':'Leather'}
bs={r[0]:r for r in b[1:] if r and r[0]}
ms={r[0]:r for r in m[1:] if r and r[0]}
order=[r[0] for r in m[1:] if r and r[0]]
norm=lambda v:{'N':'B','=':'-','':'-'}.get(v,v)
tot=0
out=[]
for si,sk in enumerate(order):
    zr=z[1+si]; ch=[]
    for c in range(1,54):
        bv=bs[sk][c].strip(); zv=norm(zr[c].strip()); mv=ms[sk][c].strip()
        if bv!=zv:
            flag='' if mv==zv else '*'
            ch.append('%s %s→%s%s'%(names[c-1],bv,zv,flag)); tot+=1
    if ch: out.append('| %s | %s |'%(sk,', '.join(ch)))
print('\n'.join(out)); print('total',tot)
print()
newn=names[53:65]
print('| Skill | '+' | '.join(newn)+' |')
for si,sk in enumerate(order):
    zr=z[1+si]
    print('| %s | %s |'%(sk,' | '.join(norm(zr[c].strip()) for c in range(54,66))))
for si in (50,51,52,53):
    zr=z[1+si]
    print('| %d | %s |'%(si,' | '.join(norm(zr[c].strip()) for c in range(54,66))))
# rows 50-53 for classes 0-52
for si,nm in ((50,'Cover'),(51,'ManaShield'),(52,'Enlightenment'),(53,'Retaliation')):
    zr=z[1+si]
    print(nm, ', '.join('%s %s'%(names[c-1],norm(zr[c].strip())) for c in range(1,54) if norm(zr[c].strip())!='-'))
