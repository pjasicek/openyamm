#!/usr/bin/env python3
"""forad-reduce2: see-through (hole px per zone, worst over clips) and Forad's sleeve gate, installed vs a candidate.
Usage: see_compare.py <tag>  (review/gates_before vs review/gates_<tag>)"""
import json, sys
t = sys.argv[1]
J = lambda k, f: json.load(open(f'review/gates_{k}/{f}.json'))
a, b = J('before', 'see_through'), J(t, 'see_through')
zones = sorted({z for c in a['clips'].values() for z in c['zones']})
for z in zones:
    wa = max((c['zones'].get(z, {}).get('hole_max', 0), n) for n, c in a['clips'].items())
    wb = max((c['zones'].get(z, {}).get('hole_max', 0), n) for n, c in b['clips'].items())
    diff = [(n, a['clips'][n]['zones'].get(z, {}).get('hole_max', 0), b['clips'][n]['zones'].get(z, {}).get('hole_max', 0))
            for n in a['clips'] if a['clips'][n]['zones'].get(z, {}).get('hole_max', 0) != b['clips'][n]['zones'].get(z, {}).get('hole_max', 0)]
    print(f'SEE {z:12s} worst {wa[0]:4d} ({wa[1]}) -> {wb[0]:4d} ({wb[1]})  changed clips {diff}')
try:
    a, b = J('before', 'sleeve_gate'), J(t, 'sleeve_gate')
    for s_ in ('L', 'R'):
        for v in a['views']:
            wa = max((c[s_]['see'][v]['max_px'], n) for n, c in a['clips'].items()); wb = max((c[s_]['see'][v]['max_px'], n) for n, c in b['clips'].items())
            fa = sum(c[s_]['see'][v]['frames'] for c in a['clips'].values()); fb = sum(c[s_]['see'][v]['frames'] for c in b['clips'].values())
            print(f'SLEEVE {s_} {v:8s} worst px {wa[0]:4d} ({wa[1]}) -> {wb[0]:4d} ({wb[1]}), frames {fa} -> {fb}')
        pa = max(c[s_]['poke_max'] for c in a['clips'].values()); pb = max(c[s_]['poke_max'] for c in b['clips'].values())
        print(f'SLEEVE {s_} poke max {pa} -> {pb}')
except FileNotFoundError as e:
    print('SLEEVE missing', e)
