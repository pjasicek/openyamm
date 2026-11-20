#!/usr/bin/env python3
"""Viewer manifest for a reduction review: every variant GLB in review/viewer, source (r100) and the picked step,
clips and durations read from the GLB. Usage: viewer_manifest.py <title> <picked tag> <source tris> <picked tris>"""
import hashlib, json, re, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
HERE = Path(__file__).resolve().parents[2]; V = HERE / 'review/viewer'
title, tag, src_tris, pick_tris = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
files = sorted(V.glob(f'mm7_*_{tag}.glb'))
doc, binary = read_glb(files[0])
clips = {}
for a in doc['animations']:
    end = max(max(struct.unpack(f'<{doc["accessors"][s["input"]]["count"]}f', accessor_bytes(doc, binary, s['input'])))
              for s in a['samplers'])
    loop = a['name'] in ('Standing', 'Walking', 'Running', 'Fidget', 'Flight', 'Fly', 'Idle', 'Walk', 'Run')
    clips[a['name']] = {'label': a['name'], 'duration': round(end, 6), 'mode': 'loop' if loop else 'once',
                        'provenance': 'source clips (unchanged)', 'anchors': []}
old = HERE / 'work/viewer_manifest_v2c.json'          # m286: keep the v2c manifest's clip provenance and anchors
if old.exists():
    for k, c in json.loads(old.read_text())['clips'].items():
        if k in clips:
            clips[k].update({x: c[x] for x in ('provenance', 'anchors') if x in c})
models = []
for f in files:
    variant = re.match(rf'mm7_(.*)_{tag}\.glb', f.name).group(1)
    for t, label in [('r100', f'v2c · {src_tris:,} tris'), (tag, f'reduced · {pick_tris:,} tris')]:
        g = V / f'mm7_{variant}_{t}.glb'; h = hashlib.sha256(g.read_bytes()).hexdigest()
        models.append({'id': f'{variant}_{t}', 'label': f'{variant} · {label}', 'url': f'{g.name}?v={h[:12]}',
                       'revision': 'mm7_m286_claude_v2c_reduced', 'sha256': h})
default_clip = next((c for c in ('Standing', 'Flight', 'Idle') if c in clips), next(iter(clips)))
manifest = {'revision': 'mm7_m286_claude_v2c_reduced', 'model': f'{title} — v2c vs reduced', 'default_clip': default_clip,
            'default_model': models[1]['id'], 'feedback': 'feedback/user_feedback.json', 'clips': clips,
            'models': models}
(V / 'manifest.json').write_text(json.dumps(manifest, indent=1))
print('MANIFEST', len(models), 'models', list(clips))
