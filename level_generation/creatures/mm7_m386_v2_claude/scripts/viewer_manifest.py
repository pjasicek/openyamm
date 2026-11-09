"""review/viewer/manifest.json for the robot tiers and clips, with native anchors from the MM7 m386 timing."""
import hashlib, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
V = P / 'review/viewer'
labels = {'a': 'Seeker Droid', 'b': 'Sentinel Droid (tint)', 'c': 'Assassin Droid (tint)'}
models = []
for t in 'abc':
    f = f'mm7_m386_{t}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
    models.append({'id': f'm386_{t}', 'label': labels[t], 'revision': 'mm7_m386_v2', 'url': f'{f}?v={h[:12]}', 'sha256': h})
DUR = {'Standing': 36 / 24, 'Walking': 30 / 24, 'Attack': 21 / 24, 'Hit': 21 / 24, 'Death': 18 / 24, 'Dead': 1.0,
       'Fidget': 18 / 24, 'Walk2': 18 / 24, 'Run2': 14 / 24}
SEQ = {'Standing': ['sa'], 'Walking': [f'w{c}' for c in 'abcdefghij'], 'Attack': [f'a{c}' for c in 'abcdefg'],
       'Hit': [f'n{c}' for c in 'abcdefg'], 'Death': ['na0', 'nb0', 'da0', 'db0', 'dc0', 'dd0'], 'Dead': ['xa0'],
       'Fidget': ['fa0', 'fb0', 'fc0', 'fd0', 'fe0', 'ff0'],
       'Walk2': [f'w{c}' for c in 'abcdefghij'], 'Run2': [f'w{c}' for c in 'abcdefghij']}  # gait pass: walk frames
clips = {}
for name, dur in DUR.items():
    seq = SEQ[name]; anchors = []
    for i, fr in enumerate(seq):
        imgs = [f'../../references/m386{fr}.png'] if fr[-1].isdigit() else [f'../../references/m386{fr}{v}.png' for v in range(5)]
        anchors.append({'time': round(i / len(seq) * dur, 4), 'label': fr, 'phase': f'Native m386{fr}', 'source_images': imgs})
    clips[name] = {'label': name, 'duration': dur, 'mode': 'loop' if name in ('Standing', 'Walking', 'Walk2', 'Run2') else 'once',
                   'provenance': 'Procedural rigid robot motion (all-metal v2) from the native MM7 m386 frames and timing', 'anchors': anchors}
m = {'revision': 'mm7_m386_v2', 'default_model': 'm386_a', 'default_clip': 'Walking', 'model': models[0]['url'].split('?')[0],
     'feedback': 'feedback/user_feedback.json', 'models': models, 'model_sha256': models[0]['sha256'], 'fps': 24, 'clips': clips}
(V / 'manifest.json').write_text(json.dumps(m, indent=1))
print('MANIFEST', len(models), list(clips))
