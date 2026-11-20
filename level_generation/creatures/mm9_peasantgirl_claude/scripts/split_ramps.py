#!/usr/bin/env python3
"""A ramps json limited to some variants (the human GLB carries pg_g2 + pg_g3, the elf GLB pg_g1e). Args: <in json> <out json> <variant>..."""
import json, sys
R = json.load(open(sys.argv[1])); keep = sys.argv[3:]
R['variants'] = keep
for m in R['materials']: m['ramps'] = {v: m['ramps'][v] for v in keep}
json.dump(R, open(sys.argv[2], 'w')); print('RAMPS', sys.argv[2], keep)
