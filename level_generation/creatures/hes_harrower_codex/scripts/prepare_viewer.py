from pathlib import Path
import json,shutil,hashlib,sys
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'))
from merge_head_material import read_glb,accessor_array
from run_creature_review import command
V=P/'review/viewer';V.mkdir(parents=True,exist_ok=True)
(V/'feedback').mkdir(exist_ok=True)
if not (V/'feedback/user_feedback.json').exists():(V/'feedback/user_feedback.json').write_text('{"findings": []}\n')
for name in ('index.html','review.js'):shutil.copy(P.with_name('hes_kreegan_claude')/'review/viewer'/name,V/name)
f=V/'index.html';f.write_text(f.read_text().replace('BlasterGuy','Harrowers').replace('hes_kreegan_claude','hes_harrower_codex'))
(P/'references_hd').mkdir(exist_ok=True)
for src,dest in [('fam_harrowers.png','concept.png'),('boss_vreth.png','boss.png')]:shutil.copy(ROOT/'design/kreegan_world/concepts/monsters'/src,P/'references_hd'/dest)
labels=['A: Harrower (10240, x1.0)','B: Blooded Harrower (10241, x1.05)','C: Crown Harrower (10242, x1.1)','Huntmaster Vreth (10147, x1.35)']
revision='harrowers_attacks_20261024';models=[]
for suffix,label in zip(('a','b','c','boss'),labels):
 f=V/f'hes_harrower_{suffix}.glb';h=hashlib.sha256(f.read_bytes()).hexdigest();models.append({'id':'hhw_'+suffix,'label':label,'revision':revision,'url':f.name+'?v='+h[:12],'sha256':h})
d,b=read_glb(V/'hes_harrower_a.glb')
provenance={'Standing':'UnarmedIdle, local library; fitted crescent grip','Walking':'Native Demon_Walking; fitted arms and claw-foot floor contact','Running':'Local Mixamo Standard Run; retargeted, fitted grip and floor contact','Attack':'Armed-Attack-Dual2, full library body and arms; twin cut into a turning cross','Attack2':'Armed-Attack-Dual3 from frame 4, full library body and arms; cross cut, both blades','ChargeStrike':'Armed-Run-Attack-Dual, full library body and arms; charge strike (script clip)','Hit':'Shared Carbine_Hit, fitted grip','Death':'Shared Carbine_Death, fitted arms, tail and cloth','Dead':'Held final Death pose','Fidget':'ArmedSpecial1, fitted grip','Roar':'Local Mixamo Standing Taunt Battlecry, fitted grip','Spent':'ArmedIdleInjured1, fitted grip'}
clips={}
for a in d['animations']:
 name=a['name'];duration=max(float(accessor_array(d,b,s['input']).max()) for s in a['samplers'])
 clips[name]={'label':name,'duration':duration,'mode':'loop' if name in ('Standing','Walking','Running','Dead','Spent') else 'once','provenance':provenance[name],'anchors':[{'time':0,'label':name,'phase':provenance[name],'source_images':['../../references_hd/concept.png','../../references_hd/boss.png']}]}
manifest={'revision':revision,'model':'hes_harrower_a.glb','default_model':'hhw_a','default_clip':'Standing','feedback':'feedback/user_feedback.json','models':models,'clips':clips}
(V/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for model in models:command(P,'check',8912,[],model['id'])
print('Viewer manifest and wrapper arguments validated for four tiers; browser not opened.')
