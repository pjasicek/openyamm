import os
import json, csv
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
O=ROOT + '/output/solo_balance/'
tabs={'nightmare': O+'monsters_nightmare_horizontal_solo.tsv', 'madness': O+'monsters_madness_solo.tsv'}
mon={}
for d,f in tabs.items():
    for r in csv.DictReader(open(f), delimiter='\t'):
        mon[(d, r['map'], int(r['monster_id']))]=r
PACKB={'out02.odm':194,'out03.odm':32,'out04.odm':92,'out07.odm':110,'out08.odm':32,'out05.odm':191,'elemf.odm':74,'pbp.odm':155}
PACKN={'nightmare':3,'madness':4}
res=json.load(open(os.path.join(ROOT, 'output/solo_balance/anchors.json')))
rows=[]
for r in res:
    b=mon[(r['diff'], r['map'], PACKB[r['map']])]
    Lm=int(b['level']); hpB=int(b['hp']); N=PACKN[r['diff']]
    dps=r['applied']*r['hits']/r['attacks']/r['rec']
    w=[(x if x is not None else r['maxhp'], s) for x,s in zip(r['win1']+r['win3'], [1,1,1,3,3])]
    inrate=sum(x for x,_ in w)/sum(s for _,s in w)
    censored=sum(1 for x in r['win1']+r['win3'] if x is None)
    t_each=hpB/dps
    taken=inrate/N*t_each*N*(N+1)/2
    margin=taken/r['maxhp']
    rows.append((r['diff'],r['stage'],r['map'],r['level'],Lm,r['level']/Lm,dps,t_each,inrate,censored,taken,margin))
    print(f"{r['diff']:9} {r['stage']:8} {r['map']:10} Lc{r['level']:4} Lm{Lm:4} ratio {r['level']/Lm:5.2f} DPS {dps:7.0f} TTK(B) {t_each:6.1f}s pack {t_each*N:6.1f}s in {inrate:7.0f}/s{'*' if censored else ' '} TTD(full pack) {r['maxhp']/inrate:6.1f}s  HP used by pack {margin*100:7.0f}%")
json.dump(rows, open(os.path.join(ROOT, 'output/solo_balance/anchor_margins.json'),'w'))
