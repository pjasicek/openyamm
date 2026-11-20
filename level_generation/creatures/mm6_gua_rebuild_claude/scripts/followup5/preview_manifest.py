#!/usr/bin/env python3
"""Private before/after page for follow-up 5 (a copy of the audit compare viewer): left = the installed guard, right = a
candidate body + halberd. Args: <candidate body glb> <candidate halberd glb>  -> review/followup5/preview/manifest.json"""
import json, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[2]; PV = HERE / 'review' / 'followup5' / 'preview'
src = json.load(open(HERE.parent / 'audit_mm678_20261111' / 'compare_viewer' / 'manifest.json'))
e = next(x for x in src['models'] if x['stem'] == 'mm6_gua')
rel = lambda p: os.path.relpath(Path(p).resolve(), PV)
inst = HERE.parents[2] / 'assets_source' / 'worlds' / 'mm6' / 'models'
e['before'] = rel(inst / 'mm6_gua.glb'); e['after'] = rel(sys.argv[1]); e['notes'] = []
for t in e['tiers']:
    t['before'] = json.loads(json.dumps(t['after']))
    t['before']['attachments'] = [{'url': rel(inst / 'mm6_gua_halberd.glb'), 'node': 'Xbase'}]
    t['after']['attachments'] = [{'url': rel(sys.argv[2]), 'node': 'Xbase'}]
json.dump({'models': [e]}, open(PV / 'manifest.json', 'w'), indent=1)
print('PREVIEW', PV / 'manifest.json')
