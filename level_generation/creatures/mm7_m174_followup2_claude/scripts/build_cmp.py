#!/usr/bin/env python3
"""A private copy of the audit's before/after compare viewer whose sides are any two GLBs (follow-up 2, 2026-11-12).

    build_cmp.py <out dir> <stem in the audit manifest> <label>=<before glb>:<after glb> [...]

Writes <out dir>/index.html (the audit page, import map re-pointed) and a manifest with one entry per label, the
tiers, clips and attachments taken from the audit manifest's <stem> entry. Open
http://127.0.0.1:8912/<out dir>/?role=walking#<label>.
"""
import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CMP = ROOT / 'level_generation/creatures/audit_mm678_20261111/compare_viewer'

out = Path(sys.argv[1]).resolve()
stem = sys.argv[2]
out.mkdir(parents=True, exist_ok=True)
manifest = json.loads((CMP / 'manifest.json').read_text())
entry = next(m for m in manifest['models'] if m['stem'] == stem)


def rel(p):
    return os.path.relpath(Path(p).resolve(), out)


def rebase(url):
    return rel(CMP / url)


models = []
for arg in sys.argv[3:]:
    label, paths = arg.split('=', 1)
    before, after = paths.split(':')
    e = copy.deepcopy(entry)
    e['stem'] = label
    e['name'] = f"{entry['name']} · {label}"
    e['before'] = rel(before)
    e['after'] = rel(after)
    e['notes'] = [{'stream': 'clips', 'status': label, 'text': f'left {before}, right {after}'}]
    for t in e['tiers']:
        for side in ('before', 'after'):
            for a in t[side].get('attachments', []):
                a['url'] = rebase(a['url'])
    models.append(e)
(out / 'manifest.json').write_text(json.dumps({'models': models}, indent=1))
vendor = rel(ROOT / 'level_generation/creatures/mm6_goblin/review_20261006/vendor')
html = (CMP / 'index.html').read_text().replace('../../mm6_goblin/review_20261006/vendor', vendor)
(out / 'index.html').write_text(html)
print('CMP', out.relative_to(ROOT))
