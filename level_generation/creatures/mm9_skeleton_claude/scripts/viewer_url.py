#!/usr/bin/env python3
"""Review viewer URL, optionally opened on a tier. Args: [model id]"""
import json, sys
from pathlib import Path
from urllib.parse import quote
H = Path(__file__).resolve().parents[1]; m = json.load(open(H / 'review/viewer/manifest.json'))
u = f'http://127.0.0.1:8912/level_generation/creatures/{H.name}/review/viewer/'
if len(sys.argv) > 1 and sys.argv[1] != '-':
    sh = next(x['sha256'] for x in m['models'] if x['id'] == sys.argv[1])
    u += '#' + quote(json.dumps({'clip': m['default_clip'], 'model_sha256': sh}))
print(u)
