import json, statistics, collections
from simdir import S, CODE
SEEDS=(1,2,3,4,5)
meta=json.load(open(S+'/meta_route.json'))
def load(prefix): return [{(r['build'],r['Lc'],r['diff'],r['mtag']):r for r in json.load(open(f'{S}/results_{prefix}out_route_{s}.json'))} for s in SEEDS]
base=load(''); mawflat=load('mawflat_'); opener=load('opener_')
outs=[collections.defaultdict(dict) for _ in SEEDS]
for i,s in enumerate(SEEDS):
    for l in open(f'{S}/out_route_{s}.jsonl'):
        d=json.loads(l); m=meta[d['id']]
        outs[i][(m['build'],m['Lc'],m['diff'],m['mtag'])][m['spell'] or 'none']=d
def best_dps(g):
    d=next(iter(g.values())); v={'melee':d['emp_melee_per_attack']/d['emp_melee_recovery']}
    if d['ranged_dps']>v['melee']*1.2: v['bow']=d['ranged_dps']
    if d['breath_recovery']: v['breath (area)']=d['breath_per_attack']/d['breath_recovery']
    for sp,dd in g.items():
        if sp!='none' and dd['spell_dps']>0:
            sus=dd['spell_dps']*min(1,dd['sp_per_s']*dd['spell_recovery_s']/dd['spell_cost']) if dd['spell_cost'] else dd['spell_dps']
            v[sp]=dd['spell_dps']; v[sp+' sustained']=sus
    return v
med=lambda xs: statistics.median(xs)
rows=[]
allkeys=set().union(*[set(x) for x in base])
for key in allkeys:
    have=[i for i in range(len(base)) if key in base[i] and key in outs[i]]
    if len(have)<3: continue
    b,Lc,diff,mtag=key
    rs=[base[i][key] for i in have]
    g0=outs[have[0]][key]; d0=next(iter(g0.values()))
    dps=[best_dps(outs[i][key]) for i in have]
    modes=dps[0].keys()
    row=dict(build=b,label=rs[0]['label'],Lc=Lc,diff=diff,mtag=mtag,M=round(med([r['M'] for r in rs])),P=round(med([r['P'] for r in rs])),
        skills=rs[0]['skills'],
        hp=med([r['hp'] for r in rs]), sp=med([next(iter(o[key].values()))['sp'] for o in outs]),
        dps={k:med([x.get(k,0) for x in dps]) for k in modes},
        monhp=rs[0]['monhp'], mondmg=rs[0]['mondmg'],
        landed=med([r['landed'] for r in rs]), inc=med([r['inc_pct'] for r in rs]), inc_mag=med([r['inc_mag_pct'] for r in rs]),
        regen=med([r['regen_pct'] for r in rs]), ttk1=med([r['ttk1'] for r in rs]),
        pot=med([r['potion_heal_pct'] for r in rs]),
        leech=d0['leech_melee'], taken=med([next(iter(o[key].values()))['taken_phys'] for o in outs]),
        hit_on_me=d0['hit_on_me'], flat=d0['flat_cut'], flat_maw=round(d0['flat_cut']*d0['flat_maw_factor']),
        maxn=med([r['maxn'] for r in rs]), maxn_lo=min(r['maxn'] for r in rs), maxn_hi=max(r['maxn'] for r in rs),
        maxn_mawflat=med([mawflat[i][key]['maxn'] for i in have]), maxn_opener=med([opener[i][key]['maxn'] for i in have]))
    for N in (4,10):
        for suf in ('','p','m'):
            fs=[r[f'n{N}{suf}'] for r in rs]
            row[f'n{N}{suf}']=dict(dead=sum(f['dead'] for f in fs), minhp=med([f['minhp'] for f in fs]),
                                   time=med([f['time'] for f in fs]), drinks=med([f['drinks'] for f in fs]))
    rows.append(row)
json.dump(rows, open(S+'/data_route.json','w'))
print(len(rows))
