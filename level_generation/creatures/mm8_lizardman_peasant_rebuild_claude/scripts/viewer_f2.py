#!/usr/bin/env python3
"""Follow-up 2 (2026-11-12) review viewer: tier GLBs of a candidate (<glb> -> review/viewer/m400_<t>_f2.glb through
viewer_variants.py) beside the rebuild (m400_<t>_new) and the model before it (m400_<t>_before); every clip of the
candidate. Usage: viewer_f2.py <glb>"""
import hashlib, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb  # noqa: E402
HERE = Path(__file__).resolve().parents[1]; V = HERE / 'review/viewer'
src = Path(sys.argv[1]).resolve()
subprocess.run([sys.executable, str(HERE / 'scripts/viewer_variants.py'), str(src), 'f2'], check=True,
               capture_output=True)
doc, _ = read_glb(src)
def dur(an):
    return round(max(doc['accessors'][s['input']]['max'][0] for s in an['samplers']), 6)
loops = {"Standing", "Walk", "Run", "Sprint"}
clips = {an['name']: {'label': an['name'], 'duration': dur(an), 'mode': 'loop' if an['name'] in loops else 'once',
                      'provenance': 'follow-up 2 retarget', 'anchors': []} for an in doc['animations']}
models = []
for tier in ('a', 'b', 'c'):
    for tag, label, extra in (('f2', 'follow-up 2', {}), ('new', 'rebuild 2026-11-11', {}),
                              ('before', 'before the rebuild', {'clip_map': {'Attack': 'Walk'}})):
        f = V / f'm400_{tier}_{tag}.glb'
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        models.append({**extra, 'id': f'm400_{tier}_{tag}', 'label': f'm400_{tier} · {label}',
                       'url': f'{f.name}?v={h[:12]}', 'revision': 'followup-2', 'sha256': h})
json.dump({'revision': 'followup-2', 'model': 'MM8 lizardman peasant - original clips retargeted onto the rebuild',
           'default_clip': 'Standing', 'feedback': 'feedback/user_feedback.json', 'default_model': 'm400_a_f2',
           'models': models, 'clips': clips}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models), 'models', len(clips), 'clips')
