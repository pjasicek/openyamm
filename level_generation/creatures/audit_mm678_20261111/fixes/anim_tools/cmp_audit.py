#!/usr/bin/env python3
"""Clips whose motion_audit numbers differ between two runs: cmp_audit.py <before.json> <after.json>."""
import json,sys
b=json.load(open(sys.argv[1]))['clips']
a=json.load(open(sys.argv[2]))['clips']
st_b={k:v['bad_pct'] for k,v in b['Standing']['deform'].items()} if 'Standing' in b else {}
for c in a:
    if c not in b: print('NEW',c,{k:v['bad_pct'] for k,v in a[c]['deform'].items()}); continue
    db={k:v['bad_pct'] for k,v in b[c]['deform'].items()}; da={k:v['bad_pct'] for k,v in a[c]['deform'].items()}
    ex=[k for k in ('peak_speed','amp_p90','body_share','hand_inside_pct','loop_pop') if b[c].get(k)!=a[c].get(k)]
    if db!=da or ex: print(c, db, '->', da, {k:(b[c].get(k),a[c].get(k)) for k in ex})
print('compared',len(a))
