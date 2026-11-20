"""Check stationary native animation, package the candidate, and build local visual review."""
import json
import zipfile

import numpy as np
from PIL import Image

from build import P


def main():
    paths = sorted((P / 'captures').glob('seam_coast_after_anim_*.png'))
    assert len(paths) == 28
    frames = [np.asarray(Image.open(p).convert('RGB'), dtype=float) for p in paths]
    a = frames[0]
    water = (a[:, :, 2] > a[:, :, 0] * 1.5) & (a[:, :, 2] > a[:, :, 1] * 1.15)
    land = (a[:, :, 0] > a[:, :, 1] * 1.2) & (a[:, :, 0] > a[:, :, 2] * 1.5)
    for mask in (water, land):
        mask[:70] = False
        mask[850:] = False
    assert water.sum() > 10000 and land.sum() > 10000
    water_changes = [float(np.abs(b - a)[water].mean()) for b in frames[1:]]
    land_changes = [float(np.abs(b - a)[land].mean()) for b in frames[1:]]
    assert min(water_changes) > 0.2
    assert max(land_changes) < 0.2
    durations = [max(1, round((b.stat().st_mtime - a.stat().st_mtime) * 1000)) for a, b in zip(paths, paths[1:])]
    previews = [Image.open(p).crop((0, 64, 1600, 900)).resize((1000, 523)) for p in paths]
    previews[0].save(P / 'native_animation.webp', save_all=True, append_images=previews[1:],
                     duration=durations + [durations[-1]], loop=0, lossless=True)
    report = {'samples': len(paths), 'span_seconds': sum(durations) / 1000,
              'water_changes': water_changes, 'land_changes': land_changes,
              'water_animated': True, 'stationary_land': True,
              'limitation': 'Discrete native screenshots; not a full-frame-rate shimmer or GPU performance test.'}
    (P / 'native_animation.json').write_text(json.dumps(report, indent=2) + '\n')
    for name in ('water_before', 'water_after', 'land_before', 'land_after'):
        Image.open(P / 'captures' / ('seam_' + name + '.png')).crop((0, 64, 1600, 900)).save(P / (name + '.png'))
    with zipfile.ZipFile(P / 'new_sorpigal_terrain_x2.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((P / 'runtime_x2').rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(P / 'runtime_x2'))
    html = '''<!doctype html><meta charset="utf-8"><title>New Sorpigal terrain border repair</title>
<style>body{background:#192329;color:#eee7db;font:16px/1.5 system-ui;max-width:1400px;margin:24px auto;padding:0 20px}
a{color:#9ad4ff}img{max-width:100%}.compare{position:relative;aspect-ratio:1600/836}.compare img{position:absolute;width:100%}
input{width:350px}select{font:inherit}</style>
<h1>New Sorpigal: repaired terrain borders</h1>
<p>Existing accepted artwork, 256×256 runtime tiles. No new AI generation. The shared materials now continue across
tile boundaries without wide averaged strips. Existing land coverage, dark transition artwork and shoreline alpha are reused.
Shore earth comes from the same dirt material as inland terrain.</p>
<p><select id="view"><option value="water">Low-angle water</option><option value="land">Grass reference</option></select>
Before ← <input id="split" type="range" min="0" max="100" value="50" aria-label="Comparison split"> → After</p>
<div class="compare"><img id="after" src="water_after.png" alt="Repaired borders"><img id="before" src="water_before.png" alt="Previous borders"></div>
<p>Same saved camera and executable for each pair. Water animation phase differs between captures.
Broad blurred border bands are substantially reduced; ordinary texture repetition and terrain slope/triangle shading remain visible.</p>
<h2>Materials and transitions</h2><img src="comparison.png" alt="Five before and after repeat tests">
<img src="shore_contexts.png" alt="All twelve shoreline contexts">
<h2>Native map views</h2><img src="captures/seam_town_after.png" alt="Town overview">
<img src="captures/seam_volcano_after.png" alt="Volcano reference">
<h2>Animation</h2><p>Fourteen baked frames at 15/128 seconds each. The closing step is comparable to the other steps.</p>
<img src="water_loop.webp" alt="Baked water loop"><p>28 native samples, displayed at measured screenshot spacing:</p>
<img src="native_animation.webp" alt="Native shoreline animation">
<p><a href="validation.json">332 unique map joins × 14 frames</a> · <a href="report.json">Sources and detail measurements</a> ·
<a href="native_animation.json">Native animation check</a> · <a href="new_sorpigal_terrain_x2.zip">63-tile runtime ZIP</a></p>
<p>Restart <code>./level_generation/creatures/mm6_peasants/play.sh enhanced</code> and load your usual save.</p>
<script>const split=document.querySelector('#split'),view=document.querySelector('#view'),before=document.querySelector('#before'),after=document.querySelector('#after');
function update(){before.src=view.value+'_before.png';after.src=view.value+'_after.png';before.style.clipPath='inset(0 '+(100-split.value)+'% 0 0)'}
split.oninput=update;view.onchange=update;update();</script>'''
    (P / 'review.html').write_text(html)
    print(json.dumps({'samples': len(paths), 'water_min_change': min(water_changes), 'land_max_change': max(land_changes)}, indent=2))


if __name__ == '__main__':
    main()
