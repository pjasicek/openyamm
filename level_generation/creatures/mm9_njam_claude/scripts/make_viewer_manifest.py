#!/usr/bin/env python3
"""Write review/viewer/manifest.json for the given viewer GLBs (copied into review/viewer/).

Usage: make_viewer_manifest.py <revision> <id>=<label>=<glb> [...]
Clip durations come from each GLB's animation samplers (max input time).
"""
import hashlib, json, shutil, struct, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
import os
VIEWER = HERE / 'review' / os.environ.get('VIEWER', 'viewer')
MODES = {k: 'loop' for k in ('Standing', 'Walking', 'Running', 'Dead', 'NjamPose', 'Twitch', 'Frozen', 'Statue', 'Run2', 'Lean', 'BarStand', 'Backpedal', 'BackpedalRun', 'CowerLoop')}
PROVENANCE = ('MM9 NJAM.abc / PEASANTMALE.abc clip, true handedness, on the MM9 skeleton, resampled as smooth monotone curves through the original keys; loop seams closed; floor pass applied.')
SOURCES = {'Standing': 'stand1', 'Walking': 'walk3', 'Running': 'run', 'Fidget': 'fidget1', 'AttackMelee': 'Njam_Hattack1', 'AttackRanged': 'Njam_Spell1', 'Cast': 'Njam_Spell2', 'Hit': 'wince1', 'Death': 'die1', 'NjamPose': 'Njam', 'SpellAttack': 'spell_attack', 'WinGame': 'njam_wingame', 'Twitch': 'njam_twitch', 'Frozen': 'njam_frozen', 'Statue': 'statue', 'Kick': 'Njam_kick', 'AttackMelee2': 'Njam_Hattack2', 'Run2': 'run2', 'Lean': 'lean', 'LeanFidget': 'leanfidget', 'BarDrink': 'bardrink', 'BarFidget': 'barfig', 'BarStand': 'barstand', 'Bless': 'bless', 'Pray': 'pray', 'Bow': 'bow', 'Conv': 'conv', 'Conv1': 'conv1', 'Conv2': 'conv2', 'Conv3': 'conv3', 'Conv4': 'conv4', 'Conv5': 'conv5', 'Fidget2': 'fidget2', 'Fidget3': 'fidget3', 'Fidget4': 'fidget4', 'Fidget5': 'fidget5', 'Fidget8': 'fidget8', 'PeasantAttack': 'hattack1', 'PeasantAttack2': 'hattack2', 'Hit2': 'wince2', 'Backpedal': 'backpedal', 'BackpedalRun': 'backpedalrun', 'CowerStart': 'cowerstart', 'CowerLoop': 'cower', 'CowerEnd': 'cowerend', 'Sc07Shot1': 'Sc07_shot1', 'PlayDeath': 'play_death', 'PlayGetup': 'play_getup', 'Dead': 'die1 end pose'}


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
