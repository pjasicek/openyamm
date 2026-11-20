"""Compact view of review/armour_gate_<tag>.json: failing entries (cm > tol) per clip. Args: <tag> [tol cm]"""
import json, sys
r = json.load(open(f'review/armour_gate_{sys.argv[1]}.json')); tol = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
for c, d in r.items():
    rows = [f"{n[4:]}.{k}={v[0]}@{v[1]}({v[2]}{' ' + str(v[3]) if len(v) > 3 and v[3] and len(sys.argv) > 3 else ''})" for n, x in d.items() for k, v in x.items() if v[0] > tol]
    print(c, len(rows), ' '.join(rows))
