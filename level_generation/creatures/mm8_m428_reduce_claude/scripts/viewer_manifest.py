#!/usr/bin/env python3
"""Reduction viewer manifest: installed (r100) and picked tier GLBs in review/viewer, clips and native frame anchors
taken from the production viewer's manifest (mm8_m428_claude/review/viewer/manifest.json; same folder depth, so the
sprite paths stay valid). Usage: viewer_manifest.py <picked tag> <source tris> <picked tris>"""
import hashlib, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review/viewer'
tag, src_tris, pick_tris = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
prod = json.loads((HERE.parent / 'mm8_m428_claude/review/viewer/manifest.json').read_text())
rev = 'reduce-1'; models = []
for tier, colour in (('a', 'green'), ('b', 'blue'), ('c', 'red')):
    for t, label in (('r100', f'installed · {src_tris:,} tris'), (tag, f'reduced {tag[1:]} % · {pick_tris:,} tris')):
        g = V / f'mm8_m428_{tier}_{t}.glb'; h = hashlib.sha256(g.read_bytes()).hexdigest()
        models.append({'id': f'm428_{tier}_{t}', 'label': f'Tier {tier.upper()} ({colour}) · {label}', 'revision': rev,
                       'url': f'{g.name}?v={h[:12]}', 'sha256': h})
manifest = {'revision': rev, 'model': f'MM8 Dark Elf Peasant (female) — installed vs reduced {tag[1:]} %',
            'default_model': f'm428_a_{tag}', 'default_clip': 'Standing', 'feedback': '../feedback/user_feedback.json',
            'models': models, 'clips': prod['clips']}
(V / 'manifest.json').write_text(json.dumps(manifest, indent=1))
print('MANIFEST', len(models), 'models', list(prod['clips']))
