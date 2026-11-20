"""Gate the MM7 terrain export on source integrity, seam checks and fresh native review evidence."""
import json,zipfile,html,collections
from PIL import Image,ImageDraw
from common import *
from check import metrics

def main():
 inv=json.loads((P/'inventory.json').read_text());validation=json.loads((P/'reports/validation.json').read_text());stage=json.loads((P/'reports/review_stage.json').read_text())
 files={p.name:sha(p) for p in sorted(OUT.glob('*.png'))}
 assert len(files)==116 and files==validation['files']==stage['files']
 assert validation['complete_inventory_coverage'] and not validation['failures']
 road_masks=json.loads((P/'reports/road_masks.json').read_text())
 fitted=json.loads((P/'roads_v4/review.json').read_text())
 joins=json.loads((P/'roads_v5/review.json').read_text())
 assert joins['passed'] and all(files[n]==h for n,h in joins['files'].items())
 assert fitted['passed'] and fitted['unchanged_runtime_files']==97
 assert fitted['build_sha256']==sha(P/'roads_v4/build.json')
 assert all(files[n+'.png']==r['runtime_sha256'] for n,r in fitted['tiles'].items())
 assert road_masks['passed'] and all(files[n]==h for n,h in road_masks['files'].items())
 assert all(sha(P/'transitions/fields'/f'{n}.npz')==h for n,h in road_masks['masks'].items())
 assert all(Image.open(OUT/n).size==(256,256) for n in files)
 assert all(sha(ROOT/r['source'])==r['sha256'] for r in inv['tiles']+inv['maps'])
 assert sha(ROOT/inv['table'])==inv['table_sha256']
 frozen=json.loads((T/'MM6_TERRAIN_HANDOFF_STATE.json').read_text());mm6_checks={}
 for key in ('source_records','masters','implementation_records'):
  for name,h in frozen[key].items():mm6_checks[name]=sha(T/name)==h
 for name,h in frozen['runtime_files'].items():mm6_checks[name]=sha(T/'mm6_remaining/transitions/runtime_x2'/name)==h
 assert all(mm6_checks.values())
 masters={}
 for g in ('dirt','grass','sand','snow','swamp','waste','roads'):
  a=read(M/'runtime'/f'{g}.png');masters[g]={side:metrics(a,a,side)[0] for side in ('E','S')}
 assert all(r['passed'] for m in masters.values() for r in m.values()),masters
 water=json.loads((P/'water/report.json').read_text());animation=json.loads((P/'water/native_animation.json').read_text())
 assert animation['passed']
 assert min(c['broad_correlation'] for c in water['checks'])>.995
 assert max(abs(v) for c in water['checks'] for v in c['mean_rgb_shift'])<1
 assert all(.85<a/b<1.15 for a,b in zip(water['restored_steps'],water['native_steps']))
 assert all(c['seams']['boundary_p95']<1.25*c['seams']['interior_p95'] and c['seams']['boundary_max']<1.25*c['seams']['interior_p999'] for c in water['checks'])
 capture_names=list(stage['poses'])+['emerald']+['real_'+m for m in ('7out06','out10','7out05','7out13','7out15')]
 captures={}
 for name in capture_names:
  for quality in ('x1','x2'):
   base='mm7_'+name+'_'+quality;meta=P/'captures'/f'{base}.json';im=P/'captures'/f'{base}.png';r=json.loads(meta.read_text())
   assert r['binary_sha256']==stage['binary_sha256']
   map_source=P/'fixture'/stage['poses'][name]['mode']/'7out01.odm' if name in stage['poses'] else ROOT/'assets_dev/worlds/mm7/maps'/r['map']
   assert r['native_sha256']==sha(map_source),(name,'map changed')
   if quality=='x2':assert im.stat().st_mtime_ns>stage.get('assets_updated_ns',(P/'reports/review_stage.json').stat().st_mtime_ns),(name,'stale capture')
   captures[base]=dict(metadata_sha256=sha(meta),image_sha256=sha(im),map=r['map'],pose=r['pose'])
   # A full-screen death/movie/menu is not accepted as terrain evidence.
   pixels=np.asarray(Image.open(im).convert('RGB'))
   assert pixels[1080:1180,450:750].std()>20,(name,'missing party HUD')
  pair=Image.new('RGB',(1600,640),'#202933');draw=ImageDraw.Draw(pair)
  for i,q in enumerate(('x1','x2')):
   view=Image.open(P/'captures'/f'mm7_{name}_{q}.png').resize((800,600));pair.paste(view,(i*800,32));draw.text((i*800+8,8),name+' '+['original','restored'][i],fill='white')
  pair.save(P/'contexts'/f'native_{name}_comparison.png')
 # Final compact all-tile comparison sheets, regenerated from the packaged bytes.
 for g in inv['groups']:
  rs=[r for r in inv['tiles'] if r['family']==g and r['kind']!='animation'];im=Image.new('RGB',(1024,((len(rs)+3)//4)*152),'#202933');draw=ImageDraw.Draw(im)
  for i,r in enumerate(rs):
   x,y=i%4*256,i//4*152;draw.text((x+4,y+4),r['name']+' original / x2',fill='white')
   for j,src in enumerate([P/'references'/f"{r['name']}.png",OUT/f"{r['name']}.png"]):
    a=Image.open(src).convert('RGBA').resize((128,128));bg=Image.open(OUT/'7wtrtyl.png').convert('RGBA').resize((128,128));bg.alpha_composite(a);im.paste(bg.convert('RGB'),(x+j*128,y+24))
  im.save(P/'sheets'/f'{g}_comparison.png')
 manifest=dict(iteration='mm7_complete_terrain_v5_road_joins',world='mm7',runtime_size=[256,256],static_names=102,animation_frames=14,outdoor_maps=13,files={'worlds/mm7/terrain_x2/'+n:h for n,h in files.items()})
 (P/'runtime_x2/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 provenance={str(p.relative_to(P)):sha(p) for folder in (M/'raw',M/'prompts',P/'water') for p in folder.glob('*') if p.is_file() and (folder!=P/'water' or p.name in ('prompt.txt','repair_prompt.txt','restored_atlas_raw.png','seam_repair_raw.png','native_atlas.png','offset_atlas.png'))}
 review=dict(iteration=manifest['iteration'],binary_sha256=stage['binary_sha256'],files=files,master_seams=masters,captures=captures,water_animation_passed=True,water_animation_report_sha256=sha(P/'water/native_animation.json'),mm6_checkpoint_unchanged=all(mm6_checks.values()),mm6_checked_records=len(mm6_checks),original_mm7_sources_unchanged=True,provenance=provenance,visual_review='Masters/repeats/offsets, original-vs-restored material and transition sheets, native flat fixtures and representative real-map views reviewed by the agent. Includes native animation states and movement views.',limitations=['1189 original map placements violate edge topology contracts; map geometry/layouts not changed.','Not every outdoor cell/camera angle/mip level has been viewed.','Software Xvfb captures do not establish GPU performance.','Separate native water captures can differ in phase because the water clock uses runtime elapsed time.'])
 review['road_join_report_sha256']=sha(P/'roads_v5/review.json')
 review['road_join_implementation_sha256']=sha(P/'roads_v5/collars.py')
 review['road_mask_report_sha256']=sha(P/'reports/road_masks.json')
 review['road_edge_report_sha256']=sha(P/'roads_v4/build.json')
 review['road_edge_review_sha256']=sha(P/'roads_v4/review.json')
 review['road_mask_sources_sha256']=sha(P/'roads_v4/mask_sources.json')
 review['road_prompts']={p.name:sha(p) for p in (P/'roads_v4/prompts').glob('*.txt')}
 review['visual_review']+=' Road-edge v4: 15 accepted MM6 mask adaptations, four MM7 diagonal routes, 19 individual built-in imagegen contact-border edits. Only the local border band is imported; master materials preserved. Reviewed generated art, final runtime sheets, native junctions and ground-level repeats.'
 review['visual_review']+=' Road v5 continues finished two-dimensional border artwork through shared openings; repeated EW strips and both ground-level road orientations checked for the fragments reported in 1288.png.'
 (P/'reports/review.json').write_text(json.dumps(review,indent=2)+'\n')
 with zipfile.ZipFile(P/'mm7_complete_terrain_x2.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  z.write(P/'runtime_x2/manifest.json','manifest.json')
  z.writestr('README.txt','MM7 restored terrain v5 (MM6 masks, generated road borders and corrected joins): 116 PNGs (102 static names and 14 water frames), 256px runtime.\nExtract worlds/ into an OpenYAMM development asset root and select x2 terrain quality.\nOriginal maps and gameplay assets are required. Original map layouts are unchanged.\nSource, review gallery and rebuild notes: level_generation/terrain/mm7/ in the source checkout.\n')
  for name in manifest['files']:z.write(P/'runtime_x2'/name,name)
 css='body{background:#202933;color:#eee;font:16px/1.5 system-ui;max-width:1280px;margin:24px auto}a{color:#9cf}img{max-width:100%;height:auto}.compare{position:relative;aspect-ratio:4/3}.compare img{position:absolute;width:100%;height:100%;object-fit:contain}.compare .new{clip-path:inset(0 0 0 50%)}input{width:100%}summary{cursor:pointer;padding:12px;background:#303c49}section{margin:30px 0}'
 page=f'<!doctype html><meta charset="utf-8"><title>MM7 restored terrain</title><style>{css}</style><h1>MM7 restored terrain</h1><p>13 maps · 102 static tiles · 14 water frames · 256px runtime. {validation["compatible_join_checks"]:,} compatible join checks pass.</p><p><a href="README.md">Readme / launch</a> · <a href="HANDOFF.md">Handoff</a> · <a href="mm7_complete_terrain_x2.zip">Runtime ZIP</a> · <a href="reports/validation.json">Validation</a></p><p>Original map-layout conflicts remain documented separately: <a href="reports/native_layout_mismatches.csv">1,189 placements</a>.</p>'
 page+='<section><h2>Road join correction (1288.png)</h2><img src="roads_v5/straight_join_comparison.png"><p><a href="roads_v5/README.md">Cause, correction and regression checks</a></p></section>'
 page+='<section><h2>Current roads: MM6 masks and generated border detail</h2><p>Rounded, restrained irregular edges fitted to MM7 stones.</p><img src="roads_v4/reviews/mm6_comparison.png"><img src="roads_v4/reviews/final_comparison.png"><p><a href="roads_v4/README.md">Workflow and prompts</a></p></section>'
 for name in capture_names:
  page+=f'<details><summary>Native comparison: {html.escape(name)}</summary><p>Original left / restored right. Drag to compare the same view. Moving actors and water phase may differ.</p><div class="compare"><img src="captures/mm7_{name}_x1.png"><img class="new" src="captures/mm7_{name}_x2.png"></div><input type="range" min="0" max="100" value="50" oninput="this.previousElementSibling.lastElementChild.style.clipPath=`inset(0 0 0 ${{this.value}}%)`"></details>'
 page+='<section><h2>Water motion</h2><img src="water/native_animation.webp"><p>Native timed capture. <a href="water/native_animation.json">Animation evidence</a></p><img src="water/native_animation_states.png"></section>'
 for g in inv['groups']:
  page+=f'<details><summary>{g}: every original and restored tile</summary><img src="sheets/{g}_comparison.png">'
  if (P/'contexts'/f'{g}_flat.png').exists():page+=f'<img src="contexts/{g}_flat.png">'
  page+=f'<p><a href="contexts/{g}_native.png">All native map contexts</a></p></details>'
 page+='<details><summary>Master comparisons and worst compatible joins</summary><img src="masters/v1/reviews/comparison.png"><img src="reports/worst_joins.png"></details>'
 (P/'index.html').write_text(page)
 print(json.dumps(dict(files=len(files),compatible_checks=validation['compatible_join_checks'],native_pairs=len(capture_names),mm6_unchanged=True,zip_bytes=(P/'mm7_complete_terrain_x2.zip').stat().st_size),indent=2))
if __name__=='__main__':main()
