"""Build the atlas diagram, native reference package and local Meshy handoff page."""
import hashlib
import json
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

stage = Path(__file__).resolve().parent
data = np.load(stage/'uv_transfer.npz')
tri_uv = data['uv'].reshape(-1,3,2)
size = 2048
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
colors = dict(body='#6da3ca',head='#e8b367',right_hand='#b18ad3',left_hand='#d695ba',
              feet='#81b78e',skull_clasp='#deded1')
layout = Image.new('RGB',(size,size),'#15191e')
draw = ImageDraw.Draw(layout)
for triangle,region in zip(tri_uv,data['face_regions']):
    points = [(float(v[0]*size),float((1-v[1])*size)) for v in triangle]
    draw.polygon(points,fill=colors[str(region)],outline='#253440')
for name,info in json.loads((stage/'uv_regions.json').read_text())['regions'].items():
    x,y,w,h = info['tile']
    draw.rectangle((x*size,(1-y-h)*size,(x+w)*size,(1-y)*size),outline=colors[name],width=3)
    draw.text((x*size+6,(1-y-h)*size+6),name.replace('_',' '),font=font,fill='#fff',
              stroke_fill='#15191e',stroke_width=2)
layout.save(stage/'uv_layout.png')

prompt = ('Texture this existing MM6 demon faithfully: dark charcoal-grey leathery skin with subtle grain '
          'and wrinkles; a worn green leather chest harness; an ivory bone skull clasp; aged ivory shoulder '
          'spikes, forearm spines, finger claws, toe claws and teeth. Pink-red irises with black pupils. '
          'Dark mouth and dusky inner ears. Keep the big bat ears, existing anatomy and accessories. '
          'Preserve all geometry. Fine surface detail, mostly rough non-metallic materials, restrained wear. '
          'Clean diffuse colour suitable for changing light; avoid painted highlights and cast shadows. '
          'No horns, wings, extra skulls, hanging rings, text or new accessories.')
assert len(prompt)<=800
(stage/'meshy_prompt.txt').write_text(prompt+'\n')
settings = dict(workflow='Retexture / AI Texturing',enable_original_uv=True,enable_pbr=True,
                texture_resolution='4k',target_formats=['glb'],
                primary_reference='references/native_front.png',
                additional_references=['references/native_profile.png','references/native_back.png'],
                reference_note='Use additional views when the selected Meshy workflow supports them.',
                material_return='Apply returned texture maps to mm6_demon_uv_master.blend using Meshy_Atlas.')
(stage/'meshy_settings.json').write_text(json.dumps(settings,indent=2)+'\n')
page = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>MM6 Demon — Meshy texturing upload</title>
<style>:root{color-scheme:dark;font:16px/1.5 system-ui;background:#171b22;color:#ece6df}
body{max-width:1280px;margin:auto;padding:24px}h1{margin:0;font-size:28px}a{color:#edb394}
nav{display:flex;flex-wrap:wrap;gap:20px;margin:20px 0}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
figure{margin:0;background:#272e38;border-radius:7px;overflow:hidden}img{display:block;width:100%;height:auto}
figcaption{padding:10px 14px}.ref img{height:480px;object-fit:contain;background:#3e464f;image-rendering:pixelated}
pre{white-space:pre-wrap;background:#272e38;padding:18px;border-radius:7px}details{margin:20px 0}
@media(max-width:700px){.grid{grid-template-columns:1fr}body{padding:14px}}</style>
<h1>MM6 Demon — Meshy texturing upload</h1>
<p>Revision 7 geometry with one shared UV atlas. The upload contains one static demon in its bind pose.
The separate UV master retains the rig, all nine animations, death effect and ash remains.</p>
<nav><a href="mm6_demon_meshy_upload.glb" download>Download Meshy upload GLB</a>
<a href="mm6_demon_meshy_texturing_bundle.zip" download>Download model + references + settings</a>
<a href="mm6_demon_uv_master.blend">Animated UV master</a>
<a href="README.md">Instructions</a><a href="validation.json">Checks</a></nav>
<p>In Meshy choose <strong>Retexture / AI Texturing</strong>, enable <strong>Use Original UV</strong>
and <strong>PBR</strong>, and select <strong>4K</strong> when available. Use the native front as the main appearance
reference; profile/back provide additional guidance. Return the generated GLB and texture maps for application
to the animated UV master.</p>
<details><summary>Suggested text prompt</summary><pre>__PROMPT__</pre></details>
<div class="grid"><figure><img src="review_frames/upload_front.png" alt="Actual exported static demon front"><figcaption>Actual upload GLB — front</figcaption></figure>
<figure><img src="review_frames/checker_front.png" alt="Numbered UV checker on the exported demon"><figcaption>UV checker — front</figcaption></figure>
<figure><img src="review_frames/checker_head.png" alt="Checker detail on face and ears"><figcaption>Head and ears</figcaption></figure>
<figure><img src="review_frames/checker_right_hand.png" alt="Checker detail on the right hand"><figcaption>Right hand</figcaption></figure>
<figure><img src="review_frames/checker_skull_clasp.png" alt="Checker detail on the skull clasp"><figcaption>Skull clasp</figcaption></figure>
<figure><img src="uv_layout.png" alt="Atlas regions for body, head, hands, feet and skull"><figcaption>UV allocation</figcaption></figure></div>
<details><summary>Profile, rear and opposite hand checker views</summary><div class="grid">
<figure><img src="review_frames/checker_profile.png" alt="UV checker profile"><figcaption>Profile</figcaption></figure>
<figure><img src="review_frames/checker_back.png" alt="UV checker back"><figcaption>Back</figcaption></figure>
<figure><img src="review_frames/checker_left_hand.png" alt="UV checker left hand"><figcaption>Left hand</figcaption></figure>
<figure><img src="review_frames/checker_oblique.png" alt="UV checker oblique"><figcaption>Oblique</figcaption></figure></div></details>
<details><summary>Original native appearance references</summary><div class="grid">
<figure class="ref"><img src="references/native_front.png" alt="Native front"><figcaption>Native front</figcaption></figure>
<figure class="ref"><img src="references/native_profile.png" alt="Native profile"><figcaption>Native profile</figcaption></figure>
<figure class="ref"><img src="references/native_three_quarter.png" alt="Native three quarter"><figcaption>Native three-quarter</figcaption></figure>
<figure class="ref"><img src="references/native_back.png" alt="Native back"><figcaption>Native back</figcaption></figure></div></details>
<p><a href="../animations_native_v7_20261005/index.html">Revision 7 animation review</a></p></html>'''
(stage/'index.html').write_text(page.replace('__PROMPT__',prompt))
files = [stage/'mm6_demon_meshy_upload.glb',stage/'meshy_prompt.txt',stage/'meshy_settings.json',
         stage/'README.md',stage/'uv_layout.png',stage/'validation.json']+list((stage/'references').glob('*.png'))
with zipfile.ZipFile(stage/'mm6_demon_meshy_texturing_bundle.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path,path.relative_to(stage))
manifest = dict(source_revision=7,uv_set='Meshy_Atlas',texture_generation_status='Prepared for user upload',
                geometry_triangles=16474,static_upload='mm6_demon_meshy_upload.glb',
                animated_master='mm6_demon_uv_master.blend',settings=settings,
                exports={name:dict(bytes=(stage/name).stat().st_size,sha256=hashlib.sha256((stage/name).read_bytes()).hexdigest())
                         for name in ('mm6_demon_meshy_upload.glb','mm6_demon_uv_master.blend','mm6_demon_meshy_texturing_bundle.zip')})
(stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Built Meshy texturing bundle and review page.')
