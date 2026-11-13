import json,sys
d=json.load(open('/home/pjasicek/github/OpenYAMM/output/studio_cal/mm8_d05/compare/report.json'))
print(json.dumps(d['totals']))
print(d['notes'])
ss=d['sectors']
print(json.dumps(ss[0])[:500])
for s in sorted(ss,key=lambda s:s.get('score',0)):
    print({k:(round(v,2) if isinstance(v,float) else v) for k,v in s.items() if not isinstance(v,(list,dict))})
print('tex pairs',json.dumps(d['texture_pairs'])[:1500])
print('missing',json.dumps(d['floor_missing_in_rebuild'])[:800])
print('only',json.dumps(d['floor_only_in_rebuild'])[:800])
n=int(sys.argv[1]) if len(sys.argv)>1 else 12
for w in d['worst_points'][:n]: print(json.dumps(w)[:700])
