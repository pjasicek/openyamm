#!/usr/bin/env python3
"""Viewer manifest for Bjarni (one skin): copies export/mm9_bj.glb to review/viewer/bj.glb and writes the manifest.
Usage: make_viewer_bj.py <revision>"""
import hashlib, json, struct, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
V = HERE / 'review' / 'viewer'
LOOPS = {'Standing', 'Walking', 'Running', 'Dead', 'Cower', 'Sit'}
PROV = ('Original MM9 clip (PeasantMale library or BJARNI.abc own clips) (LithTech ABC) on the MM9 skeleton fitted to the HD body: local rotations unchanged, '
        'resampled as monotone curves through the original keys; loop seams closed; one-shots eased from and to Standing; '
        'hands rested out of the tunic (hand_rest.py); floor pass applied.')
rev = sys.argv[1]
roles = json.load(open(HERE / 'scripts' / 'roles_bj.json'))['roles']
src = {k: ' + '.join(v['clips']) for k, v in roles.items()}
src['Dead'] = 'die1 end pose'
(V / 'feedback').mkdir(exist_ok=True)
fb = V / 'feedback' / 'user_feedback.json'
if not fb.exists():
    fb.write_text('{"findings": []}\n')
models = []
import shutil
shutil.copyfile(HERE / 'export' / 'mm9_bj.glb', V / 'bj.glb')
for mid, label in (('bj', 'Bjarni Thorvaldssen (row 246, BJARNI)'),):
    data = (V / f'{mid}.glb').read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    models.append({'id': mid, 'label': label, 'revision': rev, 'url': f'{mid}.glb?v={sha[:12]}', 'sha256': sha})
doc = json.loads(data[20:20 + struct.unpack_from('<I', data, 12)[0]])
clips = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
manifest = {'revision': rev, 'model': 'bj.glb', 'default_clip': 'Standing', 'default_model': 'bj',
            'feedback': 'feedback/user_feedback.json', 'models': models,
            'clips': {n: {'label': f'{n} (MM9 {src.get(n, "")})', 'duration': d, 'mode': 'loop' if n in LOOPS else 'once',
                          'provenance': PROV,
                          'anchors': [{'time': 0, 'label': n, 'phase': 'Start',
                                       'source_images': ['../../references_hd/00_three_quarter.png']}]}
                      for n, d in clips.items()}}
(V / 'manifest.json').write_text(json.dumps(manifest, indent=2))
print('manifest', rev, {k: round(v, 3) for k, v in clips.items()})
