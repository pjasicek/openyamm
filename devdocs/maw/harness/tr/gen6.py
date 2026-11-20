import textwrap
M='/home/pjasicek/github/Maw-Mod-MMMerge/Data/Tables/'
B='/home/pjasicek/github/OpenYAMM/reference/mmerge_data_forus/Data/Tables/'
def rd(p): return [l.split('\t') for l in open(p,encoding='latin-1').read().replace('\r','').split('\n')]
b=rd(B+'Class Skills.txt'); m=rd(M+'Class Skills.txt'); z=rd(M+'Class Skillz.txt')
hp=rd(M+'Class HP SP.txt'); names=[r[0] for r in hp[1:] if r and r[0]]
names=[n if n!='n/u' else 'n/u' for n in names]
bs={r[0]:r for r in b[1:] if r and r[0]}; ms={r[0]:r for r in m[1:] if r and r[0]}
order=[r[0] for r in m[1:] if r and r[0]]
norm=lambda v:{'N':'B','=':'-','':'-'}.get(v,v)
def cname(c):
    n=names[c-1]
    if n=='n/u': return 'n/u(%d)'%(c-1)
    if n=='Dark ArchMage': return 'DarkArchMage'
    return n
out=[]
def wrap(prefix, items):
    s=prefix+', '.join(items)
    return textwrap.fill(s, width=118, subsequent_indent='  ', break_long_words=False, break_on_hyphens=False)
tot=0; dead=0
for si,sk in enumerate(order):
    zr=z[1+si]; ch=[]
    for c in range(1,54):
        bv=bs[sk][c].strip(); zv=norm(zr[c].strip()); mv=ms[sk][c].strip()
        if bv!=zv:
            ch.append('%s %s→%s%s'%(cname(c),bv,zv,'' if mv==zv else '*')); tot+=1
            if mv!=zv: dead+=1
    if ch: out.append(wrap('- %s: '%sk, ch))
open('cs_diff.md','w').write('\n'.join(out)+'\n')
print(tot,dead)
ab=['Ser','Ang','Arch','DK','DL','LK','Sha','Sek','Mar','Ele','EA','MoE']
rows=['| Skill | '+' | '.join(ab)+' |','|---|'+'---|'*12]
for si,sk in enumerate(order):
    zr=z[1+si]
    rows.append('| %s | %s |'%(sk,' | '.join(norm(zr[c].strip()) for c in range(54,66))))
for si,nm in ((50,'Cover (new)'),(51,'ManaShield (new)'),(52,'Enlightenment (new)'),(53,'Retaliation (new)')):
    zr=z[1+si]
    rows.append('| %s | %s |'%(nm,' | '.join(norm(zr[c].strip()) for c in range(54,66))))
open('cs_new.md','w').write('\n'.join(rows)+'\n')
ext=[]
for si,nm in ((50,'Cover'),(51,'ManaShield'),(52,'Enlightenment'),(53,'Retaliation')):
    zr=z[1+si]
    ext.append(wrap('- %s: '%nm, ['%s %s'%(cname(c),norm(zr[c].strip())) for c in range(1,54) if norm(zr[c].strip())!='-']))
open('cs_ext.md','w').write('\n'.join(ext)+'\n')
