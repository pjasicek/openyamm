"""review/viewer/manifest.json for the dragonfly tiers and clips, with native anchors from the MM7 sprite timing."""
import hashlib, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
V = P / 'review/viewer'
labels = {'a': 'Dragonfly', 'b': 'Fire Dragonfly', 'c': 'Queen Dragonfly'}
models = []
for t in 'abc':
    f = f'mm7_m186_{t}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
    models.append({'id': f'm186_{t}', 'label': labels[t], 'revision': 'mm7_m186_v1', 'url': f'{f}?v={h[:12]}', 'sha256': h})
NATIVE = {'Fly': ('w', 'abcdefgh', [2] * 8), 'Attack': ('a', 'abcdefg', [2] * 7), 'Cast': ('a', 'abcdefg', [2] * 7),
          'Hit': ('n', 'abcdefg', [2] * 7)}
DUR = {'Fly': 1.0, 'Attack': 21 / 24, 'Cast': 21 / 24, 'Hit': 21 / 24, 'Death': 27 / 24, 'Dead': 1.0}
clips = {}
for name, dur in DUR.items():
    anchors = []
    if name in NATIVE:
        g, frames, ticks = NATIVE[name]; total = sum(ticks); t = 0
        for fr, k in zip(frames, ticks):
            anchors.append({'time': round(t / total * dur, 4), 'label': fr, 'phase': f'Native m186{g}{fr}0',
                            'source_images': [f'../../references/m186{g}{fr}{v}.png' for v in range(5)]})
            t += k
    if name == 'Death':
        for i, fr in enumerate(['na0', 'nb0', 'nc0', 'da0', 'db0', 'dc0', 'dd0', 'de0', 'df0']):
            anchors.append({'time': round(i * 2 / 18 * dur, 4), 'label': fr, 'phase': f'Native m186{fr}',
                            'source_images': [f'../../references/m186{fr}.png']})
    if name == 'Dead':
        anchors.append({'time': 0, 'label': 'xa', 'phase': 'Native corpse m186xa0', 'source_images': ['../../references/m186xa0.png']})
    clips[name] = {'label': name, 'duration': dur, 'mode': 'loop' if name == 'Fly' else 'once',
                   'provenance': 'Procedural dragonfly motion from the native MM7 m186 frames and timing' + (' (no native cast frames: own design)' if name == 'Cast' else ''), 'anchors': anchors}
m = {'revision': 'mm7_m186_v1', 'default_model': 'm186_a', 'default_clip': 'Fly', 'model': models[0]['url'].split('?')[0],
     'feedback': 'feedback/user_feedback.json', 'models': models, 'model_sha256': models[0]['sha256'], 'fps': 24, 'clips': clips}
(V / 'manifest.json').write_text(json.dumps(m, indent=1))
print('MANIFEST', len(models), list(clips))
