"""Bind native review and sampled animation evidence to the combined terrain export."""
import json
import zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from build import P, sha


def main():
    files = json.loads((P / 'report.json').read_text())['files']
    stage = json.loads((P / 'review_stage.json').read_text())
    assert stage['files'] == files
    assert sha(Path(stage['stage']) / 'openyamm') == stage['binary_sha256']
    for mode in ('map', 'flat'):
        for name, digest in files.items():
            assert sha(Path(stage['stage']) / mode / 'assets_dev/worlds/mm6/terrain_x2' / name) == digest
    for name in ('coast', 'island', 'pool', 'near', 'dirt'):
        capture = json.loads((P / 'captures' / f'new_dirt_shores_{name}.json').read_text())
        assert capture['binary_sha256'] == stage['binary_sha256']
        assert capture['native_sha256'] == stage['flat_sha256' if name in ('island', 'pool') else 'map_sha256']
    paths = sorted((P / 'captures').glob('new_dirt_shores_pool_anim_*.png'))
    assert len(paths) == 28
    first = np.asarray(Image.open(paths[0]).convert('RGB'), dtype=float)
    water = (first[:, :, 2] > first[:, :, 0] * 1.5) & (first[:, :, 2] > first[:, :, 1] * 1.15)
    land = (first[:, :, 0] > first[:, :, 1] * 1.2) & (first[:, :, 0] > first[:, :, 2] * 1.5)
    for mask in (water, land):
        mask[:70] = False
        mask[850:] = False
    assert min(water.sum(), land.sum()) > 10000
    changes = [np.abs(np.asarray(Image.open(path).convert('RGB'), dtype=float) - first) for path in paths[1:]]
    wc = [float(a[water].mean()) for a in changes]
    lc = [float(a[land].mean()) for a in changes]
    print({'water_min': min(wc), 'land_max': max(lc)})
    assert min(wc) > .2 and max(lc) < .2
    durations = [max(1, round((b.stat().st_mtime - a.stat().st_mtime) * 1000)) for a, b in zip(paths, paths[1:])]
    previews = [Image.open(p).crop((0, 64, 1600, 900)).resize((1000, 523)) for p in paths]
    previews[0].save(P / 'native_animation.webp', save_all=True, append_images=previews[1:],
                     duration=durations + [durations[-1]], loop=0, lossless=True)
    report = dict(fixture='empty pool; coastline frames contain monster spell effects', samples=28, water_changes=wc, land_changes=lc, water_animated=True, stationary_land=True,
                  asset_hashes=files, binary_sha256=stage['binary_sha256'], sample_span_seconds=sum(durations)/1000,
                  limitation='Discrete native samples; not full-frame-rate shimmer or hardware performance certification.')
    (P / 'native_animation.json').write_text(json.dumps(report, indent=2) + '\n')
    with zipfile.ZipFile(P / 'new_sorpigal_terrain_x2.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((P / 'runtime_x2').rglob('*')):
            if path.is_file(): archive.write(path, path.relative_to(P / 'runtime_x2'))
    html = '''<!doctype html><meta charset="utf-8"><title>New dirt shorelines</title>
<style>body{background:#202322;color:#eee;font:16px/1.5 system-ui;max-width:1400px;margin:24px auto}img{max-width:100%}a{color:#a8dbff}</style>
<h1>New Sorpigal: accepted dirt shoreline integration</h1>
<p>36 accepted land tiles and 15 accepted water tiles are byte-identical. Twelve RGBA shore overlays use the same repeating dirt phase and retained alpha/contact shading. No new AI painting or border averaging.</p>
<h2>Complete shoreline contexts across fourteen water frames</h2><img src="shore_contexts.webp">
<h2>Worst local join windows</h2><img src="worst_join_windows.png">
<h2>Native sampled animation</h2><img src="native_animation.webp">
<p>Fixture perimeter steps are geometry. Animation checks use discrete captures, not a performance benchmark.</p>'''
    for name in ('coast', 'island', 'pool', 'near', 'dirt'):
        html += f'<h2>{name}</h2><img src="captures/new_dirt_shores_{name}.png">'
    html += '<p>' + ' · '.join(f'<a href="{path}">{label}</a>' for path,label in [
        ('validation.json','Combined joins'),('local_seams.json','Border detail'),('native_animation.json','Animation checks'),
        ('report.json','Provenance'),('integration.json','Preservation audit'),('new_sorpigal_terrain_x2.zip','63-tile ZIP')]) + '</p>'
    (P / 'review.html').write_text(html)

if __name__ == '__main__': main()
