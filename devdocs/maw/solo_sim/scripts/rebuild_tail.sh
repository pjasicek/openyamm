#!/bin/bash
set -e
D="$(cd "$(dirname "$0")" && pwd)"
S="${SOLO_SIM_DIR:-$(cd "$D/../../../.." && pwd)/output/maw_solo_sim}"
export SOLO_SIM_DIR="$S"
cd $S
python3 - <<'EOF'
import json, re, glob
import os
S=os.environ['SOLO_SIM_DIR']
pm=json.load(open(S+'/pool_meta.json'))
meta={}; outs={s:open(f'{S}/out_route_{s}.jsonl','w') for s in range(1,6)}
for f in [f'{S}/pool_out_{dk}.jsonl' for dk in ('normal','maw','hard','hell','nightmare','doom','insanity','madness')]:   # not the talent variants (pool_out_v1_*, ...)
    for l in open(f):
        d=json.loads(l); m=pm[d['id']]; seed=m['seed']
        nid=re.sub(r'\|s\d+','|route',d['id']); d['id']=nid
        mm=dict(m); mm['mtag']='route'; meta[nid]=mm
        outs[seed].write(json.dumps(d)+'\n')
for o in outs.values(): o.close()
json.dump(meta, open(S+'/meta_route.json','w'))
EOF
python3 "$D"/talent_route.py   # talent tree v2 rows (route_v2L, route_v2L300) for the generic-pack tables
for s in 1 2 3 4 5; do
  for v in "" "MAW_FLAT=1" "OPENER=3"; do env META=meta_route.json $v python3 "$D"/sim.py $S out_route_$s.jsonl > /dev/null & done
done
wait
python3 "$D"/agg_route.py
python3 - <<'EOF'
import json, statistics
import os
S=os.environ['SOLO_SIM_DIR']
def export(R):
    out=[]
    for r in R:
        modes={k:v for k,v in r['dps'].items() if 'sustained' not in k}
        bm=max(modes, key=modes.get)
        sus={k.replace(' sustained',''):round(v) for k,v in r['dps'].items() if 'sustained' in k}
        f=lambda n:[n['dead'], round(n['minhp']*100), round(n['time'],1), n['drinks']]
        out.append(dict(b=r['build'],L=r['Lc'],d=r['diff'],m=r['mtag'],M=r['M'],P=r['P'],hp=round(r['hp']),sp=round(r['sp']),
            dm=bm,dv=round(modes[bm]),sus=sus,mh=round(r['monhp']),md=round(r['mondmg']),
            t1=round(r['ttk1'],1),inc=round(r['inc'],2),im=round(r['inc_mag'],2),rg=round(r['regen'],2),pot=round(r['pot'],1),
            n4=f(r['n4']),n10=f(r['n10']),n10p=f(r['n10p']),
            mx=r['maxn'],lo=r['maxn_lo'],hi=r['maxn_hi'],mxf=r['maxn_mawflat'],mxo=r['maxn_opener'],
            sk=r['skills'] if r['mtag'] in ('pace','route') else None))
    return out
old=json.load(open(S+'/page/data.json'))
pt={}
for dk in ('normal','maw','hard','hell','nightmare','doom','insanity','madness'):
    snaps={}; finals=[]; trajs={}
    for l in open(f'{S}/route/out_{dk}.jsonl'):
        d=json.loads(l)
        if d['kind']=='snapshot' and d['stage']>0: snaps.setdefault(d['stage'],[]).append(d)
        if d['kind']=='trajectory': finals.append(d['final_level']); trajs[d['seed']]=d['maps']
    e={'final':round(statistics.median(finals))}
    for st,s in snaps.items():
        if len(s) < 3: continue
        med=lambda k: statistics.median(x[k] for x in s)
        tot=[x['xp_kills']+x['xp_completion']+x['xp_quests'] for x in s]
        e[str(st)]=dict(n=len(s),maps=round(med('maps_cleared')),kills=round(med('kills')),chests=round(med('chests')),
                        items=round(med('items_seen')),cubes=round(statistics.median(x['materials'].get('1070',0) for x in s)),
                        gems=round(statistics.median(sum(v for k,v in x['materials'].items() if 1041<=int(k)<=1060) for x in s)),
                        qshare=round(100*statistics.median(x['xp_quests']/t for x,t in zip(s,tot))))
    pt[dk]=e
rows=export(json.load(open(S+'/data_route.json')))+export(json.load(open(S+'/data.json')))
json.dump(dict(rows=rows,labels=old['labels'],pt=pt,real=json.load(open(S+'/data_real.json'))), open(S+'/page/data.json','w'), separators=(',',':'))
print('page data', len(rows))
EOF
