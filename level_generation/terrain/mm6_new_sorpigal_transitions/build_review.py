"""Assemble the local review gallery, capture provenance and portable land overlay."""
import hashlib
import html
import json
from pathlib import Path
import shutil
import zipfile

from PIL import Image, ImageDraw

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
S = P.parent / 'mm6_new_sorpigal_master_study'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contact(paths, output):
    sheet = Image.new('RGB', (1280, 400 * ((len(paths) + 1) // 2)), '#202933')
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(paths):
        image = Image.open(path).crop((0, 64, 1600, 964)).resize((640, 360))
        x, y = i % 2 * 640, i // 2 * 400
        sheet.paste(image, (x, y + 30))
        draw.text((x + 6, y + 6), path.stem, fill='white')
    sheet.save(output)


def main():
    masks = json.loads((P / 'reports/mask_check_v5.json').read_text())
    assert masks['status'] == 'structural_pass_visual_review_required'
    rgb = json.loads((P / 'reports/rgb_join_check_v5.json').read_text())
    assert not rgb['failures']
    assert rgb['authoring']['checks']==211 and not rgb['authoring']['failures']
    bake=json.loads((P/'edge_treatment/bake_v5.json').read_text())
    assert not bake['pilot'] and bake['generated_count']==33
    assert all(r['protected_interior_unchanged'] for r in bake['tiles'])
    patch = json.loads((P / 'map_corrections/patch.json').read_text())
    assert digest(ROOT / patch['source']) == patch['source_sha256']
    assert digest(P / 'map_corrections/oute3.odm') == patch['output_sha256']
    runtime = sorted((P / 'runtime_x2/worlds/mm6/terrain_x2').glob('*.png'))
    assert len(runtime) == 36
    assert all(digest(f) == digest(P / "edge_treatment/runtime/v5" / f.name) for f in runtime)
    manifest = {'iteration': 'connected_v5', 'dirt_master': 'v6', 'size': [256, 256],
                'edge_treatment': 'edge_treatment/bake_v5.json', 'coverage_masks': 'connected_v4 unchanged',
                'water': 'excluded', 'files': {str(f.relative_to(P / 'runtime_x2')): digest(f) for f in runtime}}
    (P / 'runtime_x2/manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

    captures = []
    for folder in ['v5', 'v5_motion', 'v5_linear', 'v5_original', 'v5_before_edges']:
        for path in sorted((P / 'captures' / folder).glob('*.json')):
            record = json.loads(path.read_text())
            shot = path.parent / record['screenshot']
            assert shot.exists()
            settings = path.with_name(path.stem + '_settings.ini')
            if not settings.exists():
                source = Path('/tmp/openyamm-levelgen-captures') / record['name'] / 'settings.ini'
                assert digest(source) == record['settings_sha256']
                shutil.copy2(source, settings)
            assert digest(settings) == record['settings_sha256']
            captures.append({'report': str(path.relative_to(P)), 'screenshot': str(shot.relative_to(P)),
                             'screenshot_sha256': digest(shot), 'settings': str(settings.relative_to(P)),
                             'native_sha256': record['native_sha256'], 'binary_sha256': record['binary_sha256']})
    assert len(captures)==33, 'Expected22 final views,3 sampling trials and8 baseline comparisons'
    assert len({c['binary_sha256'] for c in captures})==1, 'Comparison executable changed'
    (P / 'reports/capture_manifest_v5.json').write_text(json.dumps(captures, indent=2) + '\n')
    for stem, paths in [
        ('flat_v5', sorted((P / 'captures/v5').glob('flat_*_top.png'))),
        ('oblique_v5', [P / 'captures/v5' / f'flat_road_{a}_{b}.png'
                        for a in ['east', 'north', 'west', 'south'] for b in ['near', 'far']]),
        ('corrected_v5', sorted((P / 'captures/v5').glob('map_corrected_?.png'))),
        ('motion_v5', sorted((P / 'captures/v5_motion').glob('*motion_*.png'))),
        ('linear_motion_v5', sorted((P / 'captures/v5_linear').glob('*motion_*.png'))),
    ]:
        assert paths and all(path.exists() for path in paths), stem
        contact(paths, P / 'reports' / (stem + '.png'))

    views = {name: {'original': f'captures/v5_original/map_{name}.png',
                    'previous': f'captures/v5_before_edges/map_{name}.png',
                    'current': f'captures/v5/map_{name}.png'}
             for name in ['overview', 'cobbles', 'grass_dirt', 'volcano']}
    gallery = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>New Sorpigal terrain review</title>
<style>body{background:#192329;color:#e9e4dc;font:16px/1.55 system-ui;margin:24px auto;max-width:1500px;padding:0 20px}
a{color:#a6d5ff}select,input,button{font:inherit}.controls{display:flex;gap:20px;flex-wrap:wrap;margin:16px 0}
.compare{position:relative;width:100%;aspect-ratio:4/3;background:#111}.compare img{position:absolute;width:100%;height:100%}
.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:20px}.gallery img{width:100%;height:auto}
figure{margin:0}figcaption{padding:8px 0}summary{cursor:pointer}h2{margin-top:32px}</style>
<h1>New Sorpigal terrain</h1><p>Painted contact edges for roads, a soft irregular grass fringe, and subtle rock-to-dirt blending.
Accepted masters and coverage masks retained.
36 runtime tiles at 256×256. Water remains original.</p>
<p><a href="new_sorpigal_land_x2.zip">Download land overlay + optional map correction</a> ·
<a href="index.html">Inspect tiles and masks</a> · <a href="README.md">Build notes and validation</a></p>
<div class="controls"><label>View <select id="pose"><option>overview</option><option>cobbles</option>
<option>grass_dirt</option><option>volcano</option></select></label>
<label>Compare against <select id="reference"><option value="original">Original</option>
<option value="previous">Before edge treatment</option></select></label>
<label>Reveal new terrain <input id="slider" type="range" min="0" max="100" value="50"></label></div>
<p>Left: comparison reference. Right: current terrain. All three versions use the same frozen executable,
saved viewpoint and corrected map layout. Drag to compare.</p>
<div class="compare"><img id="before" alt="Comparison reference"><img id="after" alt="Current terrain"></div>
<h2>Accepted dirt master</h2><a href="reports/dirt_original_previous_new.png"><img style="width:100%"
src="reports/dirt_original_previous_new.png" alt="Original, previous dirt v4, and new dirt v6 repeated three by three"></a>
<p>The new dirt removes the conspicuous diagonal clump bands. Fine texture still repeats when a single tile is reused.</p>
<h2>Flat terrain and game checks</h2><div class="gallery">__FIGURES__</div>
<p><a href="reports/review_v5.json">Review record</a> · <a href="reports/rgb_join_check_v5.json">211 RGB join checks</a> ·
<a href="reports/capture_manifest_v5.json">Capture hashes and settings</a> ·
<a href="map_corrections/patch.json">Seven-cell map correction</a></p>
<p>Flat-pad outer borders and unchanged water edges are excluded. Motion sheets show sampled camera movement;
they are not a GPU benchmark or a guarantee against shimmer on every renderer.</p>
<script>const views=__VIEWS__, $=id=>document.getElementById(id);
function render(){const v=views[$('pose').value];$('before').src=v[$('reference').value];$('after').src=v.current;
$('after').style.clipPath=`inset(0 0 0 ${100-Number($('slider').value)}%)`;}
for(const id of ['pose','reference','slider'])$(id).addEventListener('input',render);render();</script></html>'''
    figures = [f'<figure><a href="edge_treatment/{family}_v5.png"><img loading="lazy" src="edge_treatment/{family}_v5.png" alt="{family} original, before, new edge treatment"></a><figcaption>{family}: original / before / new</figcaption></figure>' for family in ['roads', 'grass_dirt', 'rock_dirt']]
    for file, label in [('flat_v5', 'Six native flat layouts'), ('oblique_v5', 'Four directions, near and far'),
                         ('corrected_v5', 'Corrected New Sorpigal land contexts'),
                         ('motion_v5', 'Anisotropic: sampled movement'),
                         ('linear_motion_v5', 'Bilinear: sampled movement')]:
        figures.append(f'<figure><a href="reports/{file}.png"><img loading="lazy" src="reports/{file}.png" '
                       f'alt="{html.escape(label)}"></a><figcaption>{label}</figcaption></figure>')
    (P / 'review.html').write_text(gallery.replace('__FIGURES__', ''.join(figures)).replace('__VIEWS__', json.dumps(views)))
    review = json.loads((P / 'reports/review_v5.json').read_text())
    if review['status'] != 'prepared_and_reviewed':
        print('Gallery prepared; packaging waits for the recorded visual review.')
        return
    with zipfile.ZipFile(P / 'new_sorpigal_land_x2.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in runtime:
            archive.write(file, str(file.relative_to(P / 'runtime_x2')))
        archive.write(P / 'runtime_x2/manifest.json', 'manifest.json')
        archive.write(P / 'map_corrections/oute3.odm', 'optional_map_correction/oute3.odm')
        archive.write(P / 'map_corrections/patch.json', 'optional_map_correction/patch.json')
        archive.write(P / 'reports/review_v5.json', 'review.json')
        archive.writestr('README.txt', 'New Sorpigal land overlay: connected v5, dirt master v6.\n'
                        'Merge worlds/ into an isolated OpenYAMM assets_dev root and select terrain quality x2.\n'
                        '36 opaque256px tiles with baked AI boundary detail; no full-tile cobble override. Water/shore excluded.\n'
                        'The optional map correction fixes seven tile choices. Its source SHA256 is in patch.json.\n'
                        'To use it, place the corrected oute3.odm in worlds/mm6/maps after verifying that source.\n'
                        'Keep your original map; this archive does not install itself.\n')
    with zipfile.ZipFile(P / 'new_sorpigal_land_x2.zip') as archive:
        assert archive.testzip() is None
    print('Prepared gallery, capture manifest and', (P / 'new_sorpigal_land_x2.zip').stat().st_size, 'byte ZIP.')


if __name__ == '__main__':
    main()
