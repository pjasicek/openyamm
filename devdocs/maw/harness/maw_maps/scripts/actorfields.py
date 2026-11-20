import sys, yaml
from collections import Counter
A=yaml.safe_load(open(sys.argv[1]))['initial_state']; B=yaml.safe_load(open(sys.argv[2]))['initial_state']
for sec in ('actors','sprite_objects'):
    la, lb = A.get(sec) or [], B.get(sec) or []
    c=Counter(); ex={}
    for x,y in zip(la,lb):
        for k in x:
            if x[k]!=y.get(k):
                c[k]+=1; ex.setdefault(k, (x[k], y.get(k)))
    print(sec, len(la), len(lb), dict(c), {k:(str(v[0])[:60], str(v[1])[:60]) for k,v in ex.items()})
