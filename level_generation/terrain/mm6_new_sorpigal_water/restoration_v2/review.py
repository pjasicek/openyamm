"""Validate native animation samples and package the reviewed native-water restoration."""
import json
import zipfile

import cv2
import numpy as np
from PIL import Image

from build import P, SOURCE, digest


def main():
    native = [np.asarray(Image.open(SOURCE / f'6hdwtr{i:03}.png').convert('RGB')) for i in range(14)]
    restored = [np.asarray(Image.open(P / f'runtime_x2/worlds/mm6/terrain_x2/6hdwtr{i:03}.png')) for i in range(14)]
    yy, xx = np.mgrid[:256, :256].astype(np.float32)
    checks = []
    for i in range(14):
        j = (i + 1) % 14
        flow = cv2.calcOpticalFlowFarneback(cv2.cvtColor(native[i], cv2.COLOR_RGB2GRAY),
                                           cv2.cvtColor(native[j], cv2.COLOR_RGB2GRAY), None,
                                           0.5, 3, 21, 5, 7, 1.5, 0)
        errors = []
        for frames in (native, restored):
            warped = cv2.remap(frames[j].astype(float), xx + flow[:, :, 0], yy + flow[:, :, 1],
                               cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            errors.append(float(np.abs(warped - frames[i])[8:-8, 8:-8].mean()))
        checks.append({'frame': i, 'native_error': errors[0], 'restored_error': errors[1], 'ratio': errors[1] / errors[0]})
    assert max(c['ratio'] for c in checks) < 1.2
    (P / 'temporal_validation.json').write_text(json.dumps({'checks': checks, 'passed': True,
        'method': 'Native optical flow applied to both sequences; restored residual error must be <1.2x native'}, indent=2) + '\n')
    paths = sorted((P / 'captures').glob('native_water_v2_restored_anim_*.png'))
    assert len(paths) == 28
    first = np.asarray(Image.open(paths[0]).convert('RGB'), dtype=float)
    water = (first[:, :, 2] > first[:, :, 0] * 1.5) & (first[:, :, 2] > first[:, :, 1] * 1.15)
    land = (first[:, :, 0] > first[:, :, 1] * 1.2) & (first[:, :, 0] > first[:, :, 2] * 1.5)
    for mask in (water, land):
        mask[:70] = False
        mask[850:] = False
    assert min(water.sum(), land.sum()) > 10000
    changes = [np.abs(np.asarray(Image.open(path).convert('RGB'), dtype=float) - first) for path in paths[1:]]
    water_changes = [float(a[water].mean()) for a in changes]
    land_changes = [float(a[land].mean()) for a in changes]
    assert min(water_changes) > 0.2
    assert max(land_changes) < 0.2
    durations = [max(1, round((b.stat().st_mtime - a.stat().st_mtime) * 1000)) for a, b in zip(paths, paths[1:])]
    previews = [Image.open(p).crop((0, 64, 1600, 900)).resize((1000, 523)) for p in paths]
    previews[0].save(P / 'native_animation.webp', save_all=True, append_images=previews[1:],
                     duration=durations + [durations[-1]], loop=0, lossless=True)
    report = {'samples': 28, 'water_changes': water_changes, 'land_changes': land_changes,
              'sample_span_seconds': sum(durations) / 1000, 'water_animated': True, 'stationary_land': True,
              'asset_hashes': json.loads((P / 'report.json').read_text())['files'],
              'limitation': 'Sampled native frames, not full-frame-rate shimmer or hardware performance certification.'}
    (P / 'native_animation.json').write_text(json.dumps(report, indent=2) + '\n')
    for name in ('original', 'restored'):
        Image.open(P / 'captures' / ('native_water_v2_' + name + '.png')).crop((0, 64, 1600, 900)).save(P / (name + '.png'))
    with zipfile.ZipFile(P / 'new_sorpigal_terrain_x2.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in sorted((P / 'runtime_x2').rglob('*')):
            if p.is_file():
                archive.write(p, p.relative_to(P / 'runtime_x2'))
    html = '''<!doctype html><meta charset="utf-8"><title>New Sorpigal: faithful water restoration</title>
<style>body{background:#192329;color:#eee7db;font:16px/1.5 system-ui;max-width:1400px;margin:24px auto;padding:0 20px}
a{color:#9ad4ff}img{max-width:100%}.compare{position:relative;aspect-ratio:1600/836}.compare img{position:absolute;width:100%}
input{width:350px}.loops{display:flex;gap:12px}.loops img{width:49%}</style>
<h1>Original water, with more definition</h1>
<p>Restoration v2 follows the original fourteen frames: dark navy troughs, warm green-yellow ridges and the original
large irregular ripple pattern. Built-in imagegen supplied a detail restoration; the export retains native broad
colour and shading and adds only registered fine detail. The land and shared-dirt shore overlays are unchanged.</p>
<p>Original water ← <input id="split" type="range" min="0" max="100" value="50" aria-label="Before after split"> → Restored water</p>
<div class="compare"><img src="restored.png" alt="Restored water"><img id="before" src="original.png" alt="Original water"></div>
<p>Both runs use the same saved pose: (1717.875, −8219.900, 838.091), yaw 0.302, pitch −27.932°.
The baseline uses the original 128px runtime water; the restoration uses 256px. Both use identical enhanced land and shoreline
assets so water is the only asset difference. Animation phase can differ between captures.</p>
<h2>Native source and restored frames</h2><img src="comparison.png" alt="Repeated native and restored water tiles">
<div class="loops"><img src="native_loop.webp" alt="Original fourteen-frame animation"><img src="restored_loop.webp" alt="Restored fourteen-frame animation"></div>
<p>14 frames × 15/128 seconds = 1.640625 seconds per loop. No replacement deformation animation.</p>
<h2>In-game animation</h2><img src="native_animation.webp" alt="Sampled in-game animation">
<h2>Shoreline contexts</h2><img src="shore_contexts.png" alt="All twelve shoreline contexts">
<p><a href="validation.json">332 joins across 14 frames</a> · <a href="report.json">Colour and source checks</a> ·
<a href="temporal_validation.json">Motion consistency checks</a> · <a href="native_animation.json">Native samples</a> ·
<a href="prompt.txt">Imagegen prompt</a> · <a href="new_sorpigal_terrain_x2.zip">Combined runtime ZIP</a></p>
<p>Restart <code>./level_generation/creatures/mm6_peasants/play.sh enhanced</code> and load your usual save.</p>
<script>const s=document.querySelector('#split'),b=document.querySelector('#before');
function update(){b.style.clipPath='inset(0 '+(100-s.value)+'% 0 0)'}s.oninput=update;update();</script>'''
    (P / 'review.html').write_text(html)
    print(json.dumps({'native_samples': len(paths), 'water_min_change': min(water_changes), 'land_max_change': max(land_changes)}, indent=2))


if __name__ == '__main__':
    main()
