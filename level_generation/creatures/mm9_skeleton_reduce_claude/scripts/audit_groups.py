#!/usr/bin/env python3
"""Which decimation group each LOD0 face flagged by reduction_uv_audit.py came from: the audit's face index is the row of the
primitive's triangles in work/<mp npz> (swap_mp.py keeps the order); each row is looked up in the sweep snapshots of the step
mp_plan.py picked. Usage: audit_groups.py <audit json> <mp npz name> <TAG json name>  -> prints {group: faces} and writes
work/fix/raise_<tag>.json (groups to step back one ratio)"""
import json, sys, os
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
aud = json.load(open(sys.argv[1])); mp = np.load(HERE / 'work' / f'{sys.argv[2]}.npz'); pk = json.load(open(HERE / 'work' / f'{sys.argv[3]}.json'))
SN = np.load(HERE / 'work' / 'fix' / f"sweep_T{os.environ.get('SFX', '')}.npz")
hits = {}
for lod in aud['nodes']['Skel'][:1]:
    for pr in lod:
        for f in pr.get('faces_list', []):
            t = tuple(sorted(mp[pr['material']][f['face']].tolist())); found = None
            for gid, r in pk['pick'].items():
                if r >= 1.0:
                    continue
                S = SN[f'g{gid}_r{int(round(r * 100))}']
                if any(tuple(sorted(x)) == t for x in S.tolist()):
                    found = gid; break
            hits.setdefault(found, []).append(f['face'])
print({k: len(v) for k, v in hits.items()})
json.dump({k: pk['pick'][k] for k in hits if k is not None}, open(HERE / 'work' / 'fix' / f"raise_{sys.argv[3]}.json", 'w'))
