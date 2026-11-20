import os
import csv
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
BASE=ROOT + '/assets_dev/engine/data_tables/monster_data.txt'
PATCH=ROOT + '/assets_dev/engine/rulesets/maw/patches/monster_data.txt'
def load(maw=True):
    rows={}
    for i,line in enumerate(open(BASE, encoding='latin-1')):
        if i < 3: continue
        f=line.rstrip('\n').split('\t')
        if not f[0].strip().isdigit(): continue
        rows[int(f[0])]=f
    if maw:
        for i,line in enumerate(open(PATCH, encoding='latin-1')):
            if i==0: continue
            k,c,v=(line.rstrip('\n').split('\t')+['',''])[:3]
            if not k.strip().isdigit(): continue
            NAMED={'AC':5,'Att%':20,'Bonus':16,'EXP':6,'HP':4,'LVL':3,'Pref':15,'Special':38,'Treasure':7}
            col=int(c.lstrip('#')) if c.startswith('#') else NAMED[c]
            r=rows.get(int(k))
            if r is None: continue
            while len(r)<=col: r.append('')
            r[col]=v
    out={}
    for k,f in rows.items():
        g=lambda i: f[i] if i < len(f) else ''
        out[k]=dict(id=k,name=g(1),picture=g(2),level=g(3),hp=g(4),ac=g(5),fly=g(9),move=g(10),speed=g(13),rec=g(14),
                    bonus=g(16),type1=g(17),dmg1=g(18),miss1=g(19),att2pct=g(20),type2=g(21),dmg2=g(22),miss2=g(23),
                    spl1pct=g(24),spl1=g(25),spl2pct=g(26),spl2=g(27),special=g(38))
    return out
