#!/usr/bin/env python3
"""A private copy of the audit's before/after compare viewer for a model the audit manifest does not list
(robefix 2026-11-12; ../../mm6_sor1_followup2_claude/scripts/build_cmp.py does the same for listed models).

    build_cmp.py <out dir> <world> <model stem> <label>=<before glb>:<after glb> [...]

Tiers (skin, scale, yaw, attachments, clips) come from the working copy's actors.yml for both sides, through the audit
viewer's build.py. Open http://127.0.0.1:8912/<out dir>/?role=run#<label>.
"""
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CMP = ROOT / 'level_generation/creatures/audit_mm678_20261111/compare_viewer'
spec = importlib.util.spec_from_file_location('cmp_build', CMP / 'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

out = Path(sys.argv[1]).resolve()
world, stem = sys.argv[2], sys.argv[3]
out.mkdir(parents=True, exist_ok=True)
model = f'worlds/{world}/models/{stem}.glb'
binds = build.bindings((ROOT / f'assets_dev/worlds/{world}/models/actors.yml').read_text())[model]


def rel(p):
    return os.path.relpath(Path(p).resolve(), out)


def side(b):
    return {'skin': b['skin'], 'scale': b['scale'], 'yaw': b['yaw'], 'clips': b['clips'],
            'attachments': [{'url': rel(ROOT / 'assets_source' / a['model']), 'node': a['node']} for a in b['attachments']]}


models = []
for arg in sys.argv[4:]:
    label, paths = arg.split('=', 1)
    before, after = paths.split(':')
    models.append({'stem': label, 'worlds': [world], 'name': re.sub(r'\s+[A-Ca-c]$', '', binds[0]['descriptor']) + f' · {label}',
                   'before': rel(before), 'after': rel(after), 'streams': ['clips'],
                   'notes': [{'stream': 'clips', 'status': label, 'text': f'left {before}, right {after}'}],
                   'tiers': [{'descriptor': b['descriptor'], 'before': side(b), 'after': side(b)} for b in binds]})
(out / 'manifest.json').write_text(json.dumps({'models': models}, indent=1))
vendor = rel(ROOT / 'level_generation/creatures/mm6_goblin/review_20261006/vendor')
(out / 'index.html').write_text((CMP / 'index.html').read_text().replace('../../mm6_goblin/review_20261006/vendor', vendor))
print('CMP', out.relative_to(ROOT))
