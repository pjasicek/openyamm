"""Apply native variants to the separate body/head/wing materials and populate the review viewer."""
from pathlib import Path
import sys,json,shutil,subprocess,io,hashlib
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(Path('tools').resolve()),str(P.parent/'claude_shared')]
from merge_head_material import read_glb,write_glb,image_of
import tier_textures
# Retain the established body-only shadow correction; rubble is already made of closed rigid pieces.
s=(P.parent/'mm6_wdm_claude/scripts/shrink_shadow_lods.py').read_text().replace("== 'Demon'","== 'Gargoyle'")
namespace={'__name__':'gar_shadow'};exec(compile(s,'shared_shadow_correction','exec'),namespace)
sys.argv=['shadow',str(P/'export/mm6_gar_lods.glb'),str(P/'export/mm6_gar_shadow.glb')];namespace['main']()
subprocess.run([sys.executable,str(P.parent/'claude_shared/region_variants.py'),str(P/'export/mm6_gar_shadow.glb'),str(P/'export/mm6_gar_variants.glb'),str(P/'textures/gar_ramps.json')],check=True)
shutil.copyfile(P/'export/mm6_gar_variants.glb',P/'export/mm6_gar.glb')
V=P/'review/viewer';V.mkdir(parents=True,exist_ok=True)
source=P.parent/'mm6_gob_claude/review/viewer'
html=(source/'index.html').read_text().replace('MM6 Goblin 3D Review','MM6 Gargoyle 3D Review').replace('MM6 Goblin · Claude model review (mm6_gob_claude)','MM6 Gargoyle · Stone / Marble / Diamond').replace('Smart Topology base, fitted rig with fingers and sword, eight clips.','7,247 triangles; separate 1K body, wing and head textures; five clips and a shattering death.').replace('Reported problems · eight marked screenshots','Frame feedback').replace('Hands / skirt','Hands / claws')
(V/'index.html').write_text(html)
js=(source/'review.js').read_text().replace('mm6-goblin:review_20261006','mm6-gargoyle:review_20261012').replace('MM6 Goblin','MM6 Gargoyle')
js=js.replace('body:[0,0.82,0,3.6], head:[0,1.42,0,1.25], arms:[0,1.0,0,2.25], shoulders:[0,1.17,0,1.6], skirt:[0,0.67,0,1.65], feet:[0,0.20,0,1.65]','body:[0,1.5,0,5.8], head:[0,1.7,0.05,1.1], arms:[0,1.2,0,2.5], shoulders:[0,1.6,0,1.6], skirt:[0,1.0,0,1.65], feet:[0,0.20,0,1.65]')
(V/'review.js').write_text(js);(V/'feedback').mkdir(exist_ok=True)
if not (V/'feedback/user_feedback.json').exists():(V/'feedback/user_feedback.json').write_text('{"findings": []}\n')
ramps=json.loads((P/'textures/gar_ramps.json').read_text());models=[]
for variant,label in zip(ramps['variants'],['Stone Gargoyle','Marble Gargoyle','Diamond Gargoyle']):
 d,b=read_glb(P/'export/mm6_gar_prepared.glb')
 for mat in d['materials']:
  part='head' if 'Head' in mat['name'] else ('wings' if 'Wings' in mat['name'] else 'body');img=Image.open(P/f'textures/{part}_{variant}.png');data=io.BytesIO();img.save(data,'PNG');b.extend(b'\0'*(-len(b)%4));d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(data.getvalue())});b.extend(data.getvalue());index=d['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source'];d['images'][index]={'bufferView':len(d['bufferViews'])-1,'mimeType':'image/png','name':part+'_'+variant}
 path=V/f'mm6_{variant}.glb';write_glb(path,d,b);models.append({'id':variant,'label':label,'revision':'mm6_gar_codex_v5_separate_textures','url':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
anim=json.loads((P/'work/animation_manifest.json').read_text());clips={}
references={'Flight':'standing','Attack':'attack','Hit':'hit','Death':'death_corpse','Dead':'death_corpse'}
for n,c in anim['clips'].items():clips[n]={'label':n,'duration':c['duration'],'mode':'loop' if c.get('loop') else 'once','provenance':{'Flight':'Native 0.75 s wingbeat; locally authored wing motion with a damped Floating ready pose.','Attack':'Native-informed right claw swipe, forward body sway and left-arm balance; impact at 0.75 s.','Hit':'Native raised-arm recoil, recovery within 0.75 s.','Death':'36 stone fragments collapse, preserving recognizable head, hands and feet.','Dead':'Held final rubble pose.'}[n],'anchors':[{'time':0,'label':'Native','phase':n,'source_images':[f'../../../mm6_gar/references/{references[n]}.png']}]}
manifest={'revision':'mm6_gar_codex_v5_separate_textures','model':models[0]['url'],'model_sha256':models[0]['sha256'],'default_model':'gar_a','default_clip':'Flight','models':models,'clips':clips,'feedback':'feedback/user_feedback.json'};(V/'manifest.json').write_text(json.dumps(manifest,indent=2));print('PACKED',models)
