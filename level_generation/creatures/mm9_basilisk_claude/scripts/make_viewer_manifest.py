#!/usr/bin/env python3
"""Write review/viewer/manifest.json for the given viewer GLBs (copied into review/viewer/).

Usage: make_viewer_manifest.py <revision> <id>=<label>=<glb> [...]
Clip durations come from each GLB's animation samplers (max input time).
"""
import hashlib, json, shutil, struct, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
import os
VIEWER = HERE / 'review' / 'viewer'
MODES = {'Standing': 'loop', 'Walking': 'loop', 'Running': 'loop', 'Dead': 'loop'}
PROVENANCE = ('MM9 Basilisk clip (LithTech ABC, BASILISK.abc) on the MM9 skeleton, resampled as smooth monotone '
              'curves through the original keys; loop seams closed; floor pass applied.')
SOURCES = {'Standing': 'Stand', 'Walking': 'Walk', 'Running': 'Run', 'Fidget': 'Fidget1',
           'AttackMelee': 'HAttack1 (bite 0.666 s)', 'AttackRanged': 'RAttack1 (rangeattack 0.694 s)',
           'Hit': 'Wince1', 'Death': 'Die1', 'Dead': 'Death end pose'}


def gltf_json(path):
    data = path.read_bytes()
    length = struct.unpack_from('<I', data, 12)[0]
    return json.loads(data[20:20 + length]), data


def clip_durations(path):
    doc, data = gltf_json(path)
    out = {}
    for anim in doc.get('animations', []):
        t = 0.0
        for s in anim['samplers']:
            acc = doc['accessors'][s['input']]
            t = max(t, acc['max'][0])
        out[anim['name']] = t
    return out


def main():
    revision = sys.argv[1]
    models = []
    clips = None
    for spec in sys.argv[2:]:
        mid, label, glb = spec.split('=', 2)
        src = Path(glb)
        dst = VIEWER / f'{mid}.glb'
        if src.resolve() != dst.resolve():
            shutil.copyfile(src, dst)
        sha = hashlib.sha256(dst.read_bytes()).hexdigest()
        models.append({'id': mid, 'label': label, 'revision': revision, 'url': f'{mid}.glb?v={sha[:12]}',
                       'sha256': sha})
        if clips is None:
            clips = clip_durations(dst)
    manifest = {'revision': revision, 'model': models[0]['url'].split('?')[0], 'default_clip': 'Standing',
                'default_model': models[0]['id'], 'feedback': 'feedback/user_feedback.json', 'models': models,
                'clips': {name: {'label': f'{name} ({SOURCES.get(name, "")})', 'duration': d,
                                 'mode': MODES.get(name, 'once'), 'provenance': PROVENANCE,
                                 'anchors': [{'time': 0, 'label': name, 'phase': 'Start',
                                              'source_images': ['../../references_hd/00_three_quarter.png']}]}
                          for name, d in clips.items()}}
    (VIEWER / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print('manifest', {k: round(v, 4) for k, v in clips.items()})


if __name__ == '__main__':
    main()
