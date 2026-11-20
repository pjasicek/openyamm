"""Validate native animation samples and package the reviewed native-water restoration."""
import json
import zipfile

import cv2
import numpy as np
from PIL import Image

from build import P, PREVIOUS, sha
SOURCE = PREVIOUS / "runtime_x2/worlds/mm6/terrain_x2"


def main():
    native = [np.asarray(Image.open(SOURCE / f'6hdwtr{i:03}.png').convert('RGB')) for i in range(14)]
    restored = [np.asarray(Image.open(P / f'runtime_x2/worlds/mm6/terrain_x2/6hdwtr{i:03}.png')) for i in range(14)]
    yy, xx = np.mgrid[:256, :256].astype(np.float32)
    checks = []
    for i in range(14):
        j = (i + 1) % 14
        errors = []
        for frames in (native, restored):
            flow = cv2.calcOpticalFlowFarneback(cv2.cvtColor(frames[i], cv2.COLOR_RGB2GRAY),
                                               cv2.cvtColor(frames[j], cv2.COLOR_RGB2GRAY), None,
                                               0.5, 3, 21, 5, 7, 1.5, 0)
            warped = cv2.remap(frames[j].astype(float), xx + flow[:, :, 0], yy + flow[:, :, 1],
                               cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            errors.append(float(np.abs(warped - frames[i])[8:-8, 8:-8].mean()))
        checks.append({'frame': i, 'native_error': errors[0], 'restored_error': errors[1], 'ratio': errors[1] / errors[0]})
    assert max(c['ratio'] for c in checks) < 1.2
    (P / 'temporal_validation.json').write_text(json.dumps({'checks': checks, 'passed': True,
        'method': 'Each sequence uses its own wave motion because repaired borders have new connected shapes; residual error must be <1.2x v2'}, indent=2) + '\n')
    paths = sorted((P / 'captures').glob('water_seams_v3_wrapped_anim_*.png'))
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
    for name, label in [('before', 'before'), ('wrapped', 'after')]:
        Image.open(P / 'captures' / ('water_seams_v3_' + name + '.png')).crop((0, 64, 1600, 900)).save(P / (label + '.png'))
    with zipfile.ZipFile(P / 'new_sorpigal_terrain_x2.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in sorted((P / 'runtime_x2').rglob('*')):
            if p.is_file():
                archive.write(p, p.relative_to(P / 'runtime_x2'))
    html = """<!doctype html><meta charset="utf-8"><title>Water seam repair v3</title>
+<style>body{background:#192329;color:#eee7db;font:16px/1.5 system-ui;max-width:1400px;margin:24px auto;padding:0 20px}a{color:#9ad4ff}img{max-width:100%}.compare{position:relative;aspect-ratio:1600/836}.compare img{position:absolute;width:100%}input{width:350px}</style>
+<h1>Water seam repair v3</h1><p>The v2 exports contained local breaks that whole-edge averages missed.
+Imagegen repaired the offset seam crosses. Gradient-based insertion keeps the central 208×208 pixels unchanged
+and avoids blending incompatible wave patterns into blurred strips. Water also uses a repeat sampler in the renderer;
+land and shoreline overlays retain clamp sampling. The two samplers share the same texture array.</p>
+<p>Before ← <input id="split" type="range" min="0" max="100" value="50" aria-label="Comparison split"> → After</p>
+<div class="compare"><img src="after.png" alt="Repaired water with repeat sampling"><img id="before" src="before.png" alt="Previous water with clamp sampling"></div>
+<p>Same flat test map and camera. The after capture includes the renderer correction; executable hashes are retained
+in capture records. Animation and sky phase differ between runs. Test-pad perimeter steps are fixture geometry.</p>
+<h2>Offset seam inspection</h2><p>Tile boundaries are moved to the centre to expose breaks. Before:</p>
+<img src="before_offset.png" alt="Old edge breaks"><p>After:</p><img src="after_offset.png" alt="Repaired edge continuity">
+<img src="all_frames_offset.png" alt="All fourteen repaired frames, offset for inspection">
+<h2>Animation</h2><img src="after_loop.webp" alt="Repaired repeated animation"><img src="native_animation.webp" alt="Native animation samples">
+<h2>Checks and pack</h2><p><a href="local_seams.json">Local seam contrast</a> · <a href="validation.json">332 joins across fourteen frames</a> ·
+<a href="temporal_validation.json">Temporal consistency</a> · <a href="native_animation.json">Native samples</a> ·
+<a href="prompt.txt">Built-in imagegen prompt</a> · <a href="new_sorpigal_terrain_x2.zip">Runtime texture ZIP</a></p>
+<p>Restart <code>./level_generation/creatures/mm6_peasants/play.sh enhanced</code>. The texture ZIP alone does not contain the renderer fix.</p>
+<script>const s=document.querySelector('#split'),b=document.querySelector('#before');function update(){b.style.clipPath='inset(0 '+(100-s.value)+'% 0 0)'}s.oninput=update;update();</script>""".replace('\n+', '\n')
    (P / 'review.html').write_text(html)
    print(json.dumps({'native_samples': len(paths), 'water_min_change': min(water_changes), 'land_max_change': max(land_changes)}, indent=2))


if __name__ == '__main__':
    main()
