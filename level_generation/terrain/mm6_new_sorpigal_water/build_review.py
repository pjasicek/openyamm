"""Assemble water review page, capture provenance and a portable water overlay."""
import hashlib,json,shutil,zipfile
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((P/'reports/validation_v1.json').read_text());assert not r['failures'] and not r['authoring_checks']['failures']
assert r['animation']['all_frame_opposite_edges_equal']
records=[]
for f in sorted((P/'captures/v1_flight').glob('*.json')):
 c=json.loads(f.read_text());settings=f.with_name(f.stem+'_settings.ini')
 if not settings.exists():shutil.copy2(Path('/tmp/openyamm-levelgen-captures')/c['name']/'settings.ini',settings)
 assert digest(settings)==c['settings_sha256']
 records.append({'record':str(f.relative_to(P)),'screenshot_sha256':digest(f.parent/c['screenshot']),'settings_sha256':c['settings_sha256'],'binary_sha256':c['binary_sha256'],'native_sha256':c['native_sha256']})
assert len(records)==5 and len({c['binary_sha256'] for c in records})==1
(P/'reports/capture_manifest.json').write_text(json.dumps(records,indent=2)+'\n')
review={'status':'prepared_and_reviewed_candidate','user_artistic_approval':'not assumed','tool':'built-in imagegen',
 'water':'Blue/turquoise painted ripples; fewer yellow highlights than original; deliberately retains MM6 vocabulary',
 'shore':'Accepted dirt master, no independently generated bank earth',
 'visual_checks':['12 native shore contexts','3x3 water repetition','14 frame sheet','native pool and island','matched original/new coastline','close oblique shoreline','sampled native animation'],
 'structural_report':'validation_v1.json','animation_report':'native_animation_check.json','capture_manifest':'capture_manifest.json',
 'limits':['Single-master repetition remains possible','Sampled animation is not full-frame-rate certification','The optional12-cell map correction resolves source material-layout conflicts; geometry and gameplay state are unchanged']}
(P/'reports/review.json').write_text(json.dumps(review,indent=2)+'\n')
# Compact before/after screenshot, retaining the same native camera and crop.
a=Image.open(P/'captures/v1_flight/water_flight_original.png').crop((0,64,1600,900))
b=Image.open(P/'captures/v1_flight/water_flight_lake.png').crop((0,64,1600,900))
sheet=Image.new('RGB',(1600,836));sheet.paste(a.resize((800,418)),(0,0));sheet.paste(b.resize((800,418)),(800,0));sheet=sheet.crop((0,0,1600,418));sheet.save(P/'reports/before_after.png')
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>New Sorpigal water review</title><style>body{background:#192329;color:#eee7db;font:16px/1.5 system-ui;max-width:1500px;margin:24px auto;padding:0 20px}a{color:#9ad4ff}img{max-width:100%}.compare{position:relative;aspect-ratio:4/3}.compare img{position:absolute;width:100%}.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:24px}figure{margin:0}input{width:300px}select{font:inherit}</style>
<h1>New Sorpigal water and shoreline</h1><p>V1 candidate:27 textures at256px. One generated water master,14 coherent animation frames,
and12 shoreline overlays built from the accepted dirt. No separate shoreline earth material.</p>
<p><a href="new_sorpigal_water_x2.zip">Water overlay ZIP</a> · <a href="README.md">Build notes and test launcher</a> · <a href="reports/review.json">Review record</a> · <a href="prompts/water_v1.txt">Imagegen prompt</a></p>
<label>Reveal new water <input id="reveal" type="range" min="0" max="100" value="50"></label>
<p>Left: original water/shore artwork with restored land. Right: current water/shore artwork. Same frozen engine, camera and corrected map.</p>
<div class="compare"><img src="captures/v1_flight/water_flight_original.png" alt="Original water"><img id="new" src="captures/v1_flight/water_flight_lake.png" alt="New water"></div>
<h2>Loop and shoreline review</h2>
<p>The baked loop below runs at approximately native speed. Each frame lasts15/128 seconds;14 frames form a1.640625-second cycle.</p>
<div class="gallery">
<figure><img src="reports/water_loop_v1.webp" alt="Looping3x3 water tiles"><figcaption>Baked water animation, repeated3x3.</figcaption></figure>
<figure><img src="reports/shore_contexts_v1.webp" alt="Animated shore contexts"><figcaption>All12 source shoreline contexts, with matching dirt and animated water.</figcaption></figure>
<figure><img src="captures/v1_flight/water_flight_pool.png" alt="Native pool"><figcaption>Native flat pool; internal joins checked.</figcaption></figure>
<figure><img src="captures/v1_flight/water_flight_island.png" alt="Native island"><figcaption>Native flat island; outer pad boundary excluded.</figcaption></figure>
<figure><img src="captures/v1_flight/water_flight_near.png" alt="Close coast"><figcaption>Close oblique coastline.</figcaption></figure>
<figure><img src="reports/native_animation.webp" alt="Sampled native animation"><figcaption>28 native samples over22.8 seconds, at measured sample spacing. This is a sampled check, not smooth video.</figcaption></figure>
</div><p><a href="reports/animation_frames_v1.png">All14 baked frames</a> · <a href="reports/native_animation_samples.png">Native frame details</a> · <a href="reports/validation_v1.json">131 joins across14 frames, at256 and512</a> · <a href="map_correction/patch.json">12-cell map correction</a></p>
<p>All four land masters remain unchanged. Border repairs affect under1.3% of each native shoreline silhouette. Fine texture can still repeat. Discrete animation checks do not certify temporal shimmer on every GPU.</p>
<script>const slider=document.getElementById('reveal'),after=document.getElementById('new');function update(){after.style.clipPath=`inset(0 0 0 ${100-slider.value}%)`;}slider.addEventListener('input',update);update();</script></html>'''
(P/'review.html').write_text(html)
manifest={'version':'water_v1_candidate','runtime_size':256,'files':r['files'],'requires':'Existing accepted land pack for matching dirt','animation_frame_ticks':15,'frame_count':14}
(P/'runtime_x2/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(P/'new_sorpigal_water_x2.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n,h in r['files'].items():
  f=P/'runtime_x2/worlds/mm6/terrain_x2'/n;assert digest(f)==h;z.write(f,'worlds/mm6/terrain_x2/'+n)
 z.write(P/'runtime_x2/manifest.json','manifest.json')
 z.write(P/'map_correction/oute3.odm','optional_map_correction/oute3.odm');z.write(P/'map_correction/patch.json','optional_map_correction/patch.json')
 z.write(P/'README.md','README.md');z.write(P/'reports/review.json','review.json')
with zipfile.ZipFile(P/'new_sorpigal_water_x2.zip') as z:assert z.testzip() is None
print('Prepared review page, capture manifest and ZIP.')
