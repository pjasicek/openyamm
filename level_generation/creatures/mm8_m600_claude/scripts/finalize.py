from pathlib import Path
import subprocess,sys,json,hashlib,shutil
P=Path(__file__).resolve().parents[1];E=P/'export';repo=P.parents[2]
def run(*args):subprocess.run([sys.executable,*map(str,args)],check=True)
run(P/'scripts/shrink_shadow_lods.py',E/'mm8_m600_lods.glb',E/'mm8_m600_shadow.glb')
run(P.parent/'claude_shared/region_variants.py',E/'mm8_m600_shadow.glb',E/'mm8_m600.glb',P/'textures/nightmare_ramps.json','--extra','NightmareSkin','openyamm_specular=1','--extra','NightmareSkin','openyamm_specular_mask=true','--extra','NightmareSkin','pbr.metallicFactor=0')
# Viewer copies are previews only; the runtime retains one skin and per-tier ramps.
run(P/'scripts/viewer_tiers.py')
shutil.copy2(P/'work/nightmare_final.blend',E/'nightmare.blend')
v=P/'review/viewer';manifest=json.loads((v/'manifest.json').read_text());manifest['revision']='nightmare_v3_subtle_attack_eyes';manifest['model']='mm8_nightmare_a.glb';models=[]
for tier,label in zip('abc',['Fear · olive','Terror · violet','Nightmare · red']):
 f=v/f'mm8_nightmare_{tier}.glb';sha=hashlib.sha256(f.read_bytes()).hexdigest();models.append({'id':'nightmare_'+tier,'label':label,'revision':'nightmare_v3_subtle_attack_eyes','url':f.name+'?v='+sha[:12],'sha256':sha})
manifest['models']=models;manifest['model_sha256']=models[0]['sha256']
for name,d,f in [('Standing',3.,'standing_stored_views.png'),('Walking',1.,'walk_side.png'),('Attack',1.,'attack_front.png'),('Hit',.625,'hit_front.png'),('Death',.75,'death_front.png'),('Dead',1.,'corpse_front.png'),('Fidget',.625,'fidget_front.png')]:
 manifest['clips'][name]={'label':name,'duration':d,'mode':'hold' if name=='Dead' else ('loop' if name in ['Standing','Walking'] else 'once'),'provenance':'Local segmented rig; native timing. Authored slime compression on collapse.','anchors':[{'time':0,'label':'Native','phase':'Original source','source_images':['../../references_native/'+f]}]}
manifest['clips']['Attack']['provenance']='Native one-second timing; subtle irregular eye-stalk movement, no baked FX.'
(v/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
