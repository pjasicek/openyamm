#!/usr/bin/env python3
"""Copy the runtime GLB into review/viewer/ and write manifest.json (clip labels name their MM9 source clips).

Usage: make_viewer_manifest.py <revision> <prefix> <label>
"""
import hashlib, json, shutil, struct, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
VIEWER = HERE / 'review' / 'viewer'
MODES = {'Standing': 'loop', 'Walking': 'loop', 'Running': 'loop', 'Dead': 'loop'}
PROVENANCE = ('Original MM9 clip (LithTech ABC) played on the MM9 skeleton fitted to the HD body: local rotations '
              'unchanged, resampled as monotone curves through the original keys; loop seams closed; one-shots eased '
              'from and to Standing; floor pass applied.')


def main():
    revision, prefix, label = sys.argv[1:4]
    roles = json.load(open(HERE / 'scripts' / f'roles_{prefix}.json'))['roles']
    VIEWER.mkdir(parents=True, exist_ok=True)
    (VIEWER / 'feedback').mkdir(exist_ok=True)
    fb = VIEWER / 'feedback' / 'user_feedback.json'
    if not fb.exists():
        fb.write_text('{"findings": []}\n')
    dst = VIEWER / f'{prefix}.glb'
    shutil.copyfile(HERE / 'export' / f'mm9_{prefix}.glb', dst)
    data = dst.read_bytes()
    doc = json.loads(data[20:20 + struct.unpack_from('<I', data, 12)[0]])
    clips = {a['name']: max(doc['accessors'][s['input']]['max'][0] for s in a['samplers'])
             for a in doc['animations']}
    sha = hashlib.sha256(data).hexdigest()
    src = {k: ' + '.join(v['clips']) + (f" x{v['rate']}" if v.get('rate') else '') for k, v in roles.items()}
    src['Dead'] = 'Death end pose'
    manifest = {'revision': revision, 'model': dst.name, 'default_clip': 'Standing', 'default_model': prefix,
                'feedback': 'feedback/user_feedback.json',
                'models': [{'id': prefix, 'label': label, 'revision': revision, 'url': f'{dst.name}?v={sha[:12]}',
                            'sha256': sha}],
                'clips': {name: {'label': f'{name} (MM9 {src.get(name, "")})', 'duration': d,
                                 'mode': MODES.get(name, 'once'), 'provenance': PROVENANCE,
                                 'anchors': [{'time': 0, 'label': name, 'phase': 'Start',
                                              'source_images': ['../../references_hd/00_three_quarter.png']}]}
                          for name, d in clips.items()}}
    (VIEWER / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print('manifest', {k: round(v, 3) for k, v in clips.items()})


if __name__ == '__main__':
    main()
