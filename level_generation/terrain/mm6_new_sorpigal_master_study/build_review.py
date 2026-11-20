"""Build local comparison sheets and a before/after slider page from real game captures."""

import hashlib
import html
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(__file__).resolve().parent
CATALOGUE = PROJECT.parent / 'mm6_new_sorpigal'
MATERIALS = {'grass': '6grastyl', 'dirt': '6dirttyl', 'cobbles': '6drsrew', 'volcano': '6voltyl'}
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)


def main():
    review = PROJECT / 'review'
    sheet = Image.new('RGB', (1040, 4 * 560), '#18202b')
    draw = ImageDraw.Draw(sheet)
    records = []
    cards = []
    decisions = json.loads((PROJECT / 'material_decisions.json').read_text())
    for row, (material, source_name) in enumerate(MATERIALS.items()):
        version = decisions[material]['version']
        native = Image.open(CATALOGUE / 'source_rgb' / (source_name + '.png')).convert('RGB')
        generated_path = PROJECT / 'generated' / version / (material + '_512.png')
        generated = Image.open(generated_path).convert('RGB')
        draw.text((8, row * 560 + 8), f'{material}: original 128px (nearest enlarged)', font=FONT, fill='white')
        draw.text((528, row * 560 + 8), f'Generated master {version}: 512px', font=FONT, fill='white')
        sheet.paste(native.resize((512, 512), Image.Resampling.NEAREST), (8, row * 560 + 40))
        sheet.paste(generated, (528, row * 560 + 40))
        tiled = Image.new('RGB', (1536, 1536))
        for y in range(3):
            for x in range(3):
                tiled.paste(generated, (x * 512, y * 512))
        tiled.save(review / (material + '_repeat_3x3.png'))
        pixels = np.array(generated, dtype=float)
        internal_x = float(np.abs(pixels[:, 1:] - pixels[:, :-1]).mean())
        internal_y = float(np.abs(pixels[1:] - pixels[:-1]).mean())
        records.append({
            'material': material, 'version': version, 'source': source_name, 'size': list(generated.size),
            'sha256': hashlib.sha256(generated_path.read_bytes()).hexdigest(),
            'native_mean_rgb': np.array(native).mean(axis=(0, 1)).tolist(),
            'generated_mean_rgb': pixels.mean(axis=(0, 1)).tolist(),
            'wrap_x_mean_rgb_difference': float(np.abs(pixels[:, 0] - pixels[:, -1]).mean()),
            'wrap_y_mean_rgb_difference': float(np.abs(pixels[0] - pixels[-1]).mean()),
            'internal_x_mean_rgb_difference': internal_x, 'internal_y_mean_rgb_difference': internal_y,
            'note': 'Edge differences are diagnostics only; inspect repeat sheet for structural seams.'
        })
        cards.append(f'<article><h3>{material.title()} {version}</h3><img src="generated/{version}/{material}_512.png" '
                     f'alt="Generated {material} master"><p><a href="generated/{version}/{material}_512.png">512px PNG</a> · '
                     f'<a href="runtime_x2/materials/{material}.png">256px runtime PNG</a> · '
                     f'<a href="generated/{version}/{material}_raw.png">Raw output</a> · '
                     f'<a href="review/{material}_repeat_3x3.png">3×3 repeat</a> · '
                     f'<a href="prompts/{material}_{version}.txt">Prompt</a></p></article>')
    sheet.save(review / 'masters_original_vs_candidates.png')
    (review / 'material_checks.json').write_text(json.dumps(records, indent=2) + '\n')

    sections = []
    sections.append('''<section id="dirt-revision"><h2>Dirt revision: repeat check</h2>
<p class="caption">Left: earlier chunky dirt v1 · Right: selected dirt master v4. Both repeat 3×3.</p>
<p>Dirt v4 is accepted for the master stage. Keep this version for subsequent mask and compositing work.</p>
<div class="comparison"><img src="review/dirt_v4_repeat_3x3.png" alt="Selected dirt v4 repeated nine times">
<img class="before" src="review/dirt_v1_repeat_3x3.png" alt="Earlier dirt with recurring bands">
<div class="divider"></div></div>
<input type="range" min="0" max="100" value="50" aria-label="Earlier dirt coverage">
<p><a href="review/dirt_v1_repeat_3x3.png">Earlier repeat sheet</a> ·
<a href="review/dirt_v4_repeat_3x3.png">Selected dirt repeat sheet</a> · <a href="prompts/dirt_v4.txt">Generation prompt</a> ·
<a href="review/dirt_v3_repeat_3x3.png">Earlier fine-grained revision (not preferred)</a></p>
</section>''')
    poses = json.loads((PROJECT / 'poses.json').read_text())['poses']
    for name, title in [('overview', 'Town overview'), ('cobbles', 'Cobbles and dirt'),
                        ('grass_dirt', 'Grass'), ('volcano', 'Volcanic slopes')]:
        original = f'review/original/terrain_original_fixed_{name}.png'
        version = 'runtime_x2'
        replacement = f'review/{version}/terrain_{version}_fixed_{name}.png'
        assert (PROJECT / original).is_file() and (PROJECT / replacement).is_file(), name
        sections.append(f'''<section><h2>{title}</h2>
<p class="caption">Left: original · Right: selected masters at x2 (256px). Drag to compare.</p>
<div class="comparison"><img src="{replacement}" alt="{title}, x2 runtime materials">
<img class="before" src="{original}" alt="{title}, original"><div class="divider"></div></div>
<input type="range" min="0" max="100" value="50" aria-label="Original image coverage: {title}">
<p><a href="{original}">Original full screenshot</a> · <a href="{replacement}">Trial full screenshot</a> ·
<a href="review/{version}/terrain_{version}_fixed_{name}_pose.png">Trial camera verification</a></p>
<details><summary>Camera coordinates</summary><pre>{html.escape(json.dumps(poses[name], indent=2))}</pre></details></section>''')

    document = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>New Sorpigal — terrain master study</title><style>
body{background:#121921;color:#e9e3d4;font:17px/1.5 system-ui;margin:0 auto;max-width:1600px;padding:24px}
a{color:#a7d9fa}h1,h2,h3{line-height:1.2}.note{border-left:4px solid #d3ad67;background:#29302c;padding:14px 20px}
section{margin:48px 0}.comparison{position:relative;line-height:0}.comparison img{width:100%;display:block}
.before{position:absolute;inset:0;clip-path:inset(0 50% 0 0)}.divider{position:absolute;top:0;bottom:0;left:50%;width:2px;background:#fff}
input[type=range]{width:100%;margin:14px 0;accent-color:#d3ad67}.materials{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px}
article img{width:100%;max-width:512px}pre{white-space:pre-wrap}.caption{color:#c9cbbf}details{font-size:14px}
</style><h1>New Sorpigal — terrain master study</h1>
<p>Selected materials, compared in OpenYAMM at your saved cameras. Built-in image generation;
256×256 runtime tiles from preserved 512×512 authoring masters, original buildings and sprites,
anisotropic terrain filtering at 8×.</p>
<div class="note"><strong>Material study; transitions are pending.</strong> Grass, dirt and rock replace their pure base tiles.
<strong>Cobbles are a masked overlay material over dirt.</strong> The final road tile uses its road mask to expose cobbles,
leaving dirt visible outside it. These x2 captures retain the original road tiles until their masks are ready.
Mixed land tiles remain original. Water uses original imagery.
The supplied grass and dirt cameras are identical and show grass; use the cobbles camera to assess dirt.</div>
<p><a href="README.md">Review notes / reproduction</a> · <a href="review/masters_original_vs_candidates.png">Original/master sheet</a> ·
<a href="runtime_x2/README.md">256px runtime export</a> ·
<a href="references/pose_verification.png">Original camera verification</a> ·
<a href="../mm6_new_sorpigal/index.html">Terrain catalogue</a></p>
<p>Grass v1 and cobbles v1 are accepted. Rock v2 remains tentative: the original was lighter.
Dirt v4 is selected for the master stage and used in the x2 screenshots below. Road masks remain pending.
<a href="#dirt-revision">Compare the dirt revision</a>.</p>
''' + '\n'.join(sections) + '<h2>Material candidates</h2><div class="materials">' + '\n'.join(cards) + '''</div>
<p>Earlier rock trial: <a href="review/v1/terrain_v1_fixed_volcano.png">In-game v1</a> ·
<a href="generated/v1/volcano_512.png">Rock v1 master</a>.</p>
<script>document.querySelectorAll('section').forEach(s=>{const slider=s.querySelector('input');
slider.addEventListener('input',()=>{s.querySelector('.before').style.clipPath=`inset(0 ${100-slider.value}% 0 0)`;
s.querySelector('.divider').style.left=slider.value+'%';});});</script></html>'''
    (PROJECT / 'index.html').write_text(document)
    print('Built master sheets, repeat checks and interactive comparison page')


if __name__ == '__main__':
    main()
