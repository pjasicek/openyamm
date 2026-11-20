M='/home/pjasicek/github/Maw-Mod-MMMerge/Data/Tables/'
B='/home/pjasicek/github/OpenYAMM/reference/mmerge_data_forus/Data/Tables/'
O='/home/pjasicek/github/OpenYAMM/assets_dev/engine/data_tables/'
def rd(p):
    return [l.split('\t') for l in open(p,encoding='latin-1').read().replace('\r','').split('\n')]
import sys
which=sys.argv[1]
if which=='cs':
    b=rd(B+'Class Skills.txt'); m=rd(M+'Class Skills.txt'); z=rd(M+'Class Skillz.txt')
    hb=b[0]; hm=m[0]
    print('base cols',len(hb),'maw cols',len(hm))
    # class names by index from MAW Class HP SP
    hp=rd(M+'Class HP SP.txt'); names=[r[0] for r in hp[1:] if r and r[0]]
    bs={r[0]:r for r in b[1:] if r and r[0]}; ms={r[0]:r for r in m[1:] if r and r[0]}
    zs={}
    for i,r in enumerate(z[1:]):
        if r and r[0]: zs[i]=r
    order=[r[0] for r in m[1:] if r and r[0]]
    # base vs MAW Class Skills
    print('# Class Skills.txt base->MAW changes (class index: name)')
    for si,sk in enumerate(order):
        ch=[]
        for c in range(1,54):
            bv=bs[sk][c].strip() if c<len(bs[sk]) else ''
            mv=ms[sk][c].strip() if c<len(ms[sk]) else ''
            if bv!=mv: ch.append('%s %s>%s'%(names[c-1],bv,mv))
        if ch: print(si,sk,': ',', '.join(ch))
    print('# new classes 53-64 in MAW Class Skills.txt')
    for si,sk in enumerate(order):
        print(si,sk, ' '.join(ms[sk][c].strip() if c<len(ms[sk]) else '?' for c in range(54,66)))
    print('# Class Skillz rows 0-38 vs MAW Class Skills (N==B, = == -)')
    for si,sk in enumerate(order):
        zr=zs[si]; ch=[]
        for c in range(1,66):
            zv=zr[c].strip() if c<len(zr) else ''
            mv=ms[sk][c].strip() if c<len(ms[sk]) else ''
            nz={'N':'B','=':'-'}.get(zv,zv)
            if nz!=mv: ch.append('%s cs=%s z=%s'%(names[c-1],mv,zv))
        if ch: print(si,sk,': ',', '.join(ch))
    print('# Class Skillz rows >=39 non-empty')
    for si in sorted(zs):
        if si<39: continue
        r=zs[si]; cells=[(names[c-1],r[c].strip()) for c in range(1,min(len(r),66)) if r[c].strip() not in ('=','','-','0')]
        if cells: print(si,r[0],cells)
elif which=='rz':
    z=rd(M+'Race Skillz.txt'); h=z[0]
    for i,r in enumerate(z[1:]):
        if not r or not r[0]: continue
        cells=[(h[c],r[c].strip()) for c in range(1,len(r)) if r[c].strip() not in ('=','')]
        if cells: print(i,r[0],cells)
elif which=='rs':
    b=rd(B+'Race Skills.txt'); m=rd(M+'Race Skills.txt')
    hb=b[0]; hm=m[0]
    print(len(hb),len(hm))
    bs={r[0]:r for r in b[1:] if r and r[0]}; ms={r[0]:r for r in m[1:] if r and r[0]}
    kinds=['general']+['kind%d'%k for k in range(1,21)]
    races=['Human','Vampire','DarkElf','Minotaur','Troll','Dragon','Undead','Elf','Goblin','Dwarf','Zombie']
    for sk in ms:
        ch=[]
        for c in range(1,max(len(ms[sk]),len(bs.get(sk,[])))):
            bv=bs[sk][c].strip() if sk in bs and c<len(bs[sk]) else ''
            mv=ms[sk][c].strip() if c<len(ms[sk]) else ''
            if bv!=mv: ch.append('%s/%s %r>%r'%(races[(c-1)%11],kinds[(c-1)//11],bv,mv))
        if ch: print(sk,': ',', '.join(ch))
elif which=='ss':
    b=rd(B+'Class Starting Skills.txt'); m=rd(M+'Class Starting Skills.txt')
    bs={r[0]:r for r in b[1:] if r and r[0]}; ms={r[0]:r for r in m[1:] if r and r[0]}
    tier1={0:'Archer',2:'Cleric',4:'DarkElf',5:'Dragon',6:'Druid',8:'Knight',10:'Minotaur',11:'Monk',13:'Paladin',15:'Ranger',17:'Thief',19:'Troll',20:'Vampire',21:'Sorcerer',22:'Necromancer',24:'Peasant',26:'Seraphim(53)',28:'DeathKnight(56)',29:'Shaman(59)',31:'Elementalist(62)'}
    for k in sorted(tier1):
        c=k+1
        ch=[]; full=[]
        for sk in ms:
            bv=bs[sk][c].strip() if sk in bs and c<len(bs[sk]) else ''
            mv=ms[sk][c].strip() if c<len(ms[sk]) else ''
            if bv!=mv: ch.append('%s %r>%r'%(sk,bv,mv))
            if mv in ('F','C'): full.append('%s=%s'%(sk,mv))
        print('k%d %s: %s'%(k,tier1[k],'; '.join(ch)))
        if k>=26: print('   full:',' '.join(full))
    # also other columns
    for c in range(1,34):
        k=c-1
        if k in tier1: continue
        ch=[]
        for sk in ms:
            bv=bs[sk][c].strip() if sk in bs and c<len(bs[sk]) else ''
            mv=ms[sk][c].strip() if c<len(ms[sk]) else ''
            if bv!=mv: ch.append('%s %r>%r'%(sk,bv,mv))
        if ch: print('NONTIER k%d: %s'%(k,'; '.join(ch)))
elif which=='ssz':
    z=rd(M+'Class Starting Skillz.txt'); h=z[0]
    for i,r in enumerate(z[1:]):
        if i<39 or not r or not r[0]: continue
        cells=[(h[c],r[c].strip()) for c in range(1,len(r)) if r[c].strip() not in ('0','')]
        if cells: print(i,r[0],cells)
    # compare rows 0-38 with Class Starting Skills
    m=rd(M+'Class Starting Skills.txt'); ms=[r for r in m[1:] if r and r[0]]
    for i in range(39):
        r=z[1+i]; s=ms[i]
        for c in range(1,min(len(r),len(s))):
            a={'0':'-','1':'C','2':'F'}.get(r[c].strip(),r[c].strip()); bb=s[c].strip()
            if a!=bb: print('diff',i,r[0],c-1,r[c],s[c])
