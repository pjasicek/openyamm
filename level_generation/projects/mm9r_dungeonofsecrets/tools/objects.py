import json, sys
from collections import Counter
objs=json.load(open('work/dat_objects.json'))
skip={"Rotation","OpenStartSound","OpenBusySound","OpenStopSound","CloseStartSound","CloseBusySound","CloseStopSound","SoundPos","SoundRadius","JiggleSound","LockJiggleCount","LockJigglePct","LockJiggleSpeed","Waveform","Mass","Volume","Name","ScriptParams","ScriptName"}
by={}
for o in objs: by.setdefault(o['class'],[]).append(o)
out=[]
for c,l in by.items():
    if c in ('Light','AmbientSound'): continue
    keys=set().union(*[o['properties'].keys() for o in l])
    default={}
    for k in keys:
        cnt=Counter(json.dumps(o['properties'].get(k)) for o in l)
        default[k]=cnt.most_common(1)[0][0]
    out.append(f"## {c} ({len(l)}) defaults: " + json.dumps({k:json.loads(v) for k,v in default.items() if k not in skip and v not in ('\"\"','0','0.0','[0.0, 0.0, 0.0]')}))
    for o in l:
        p=o['properties']
        d={k:v for k,v in p.items() if k not in skip and json.dumps(v)!=default.get(k) and v not in ("",)}
        d['Pos']=p.get('Pos')
        out.append(f"{o['index']} {o['name']!r}: " + json.dumps(d))
open('work/objects.txt','w').write("\n".join(out)+"\n")
