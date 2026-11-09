from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).resolve().parents[1]
subprocess.run(['python3','tools/prepare_actor_glb.py',str(p/'export/mm8_m540_lod0.glb'),str(p/'export/mm8_m540_runtime_lod0.glb')],check=True)
subprocess.run(['python3',str(p/'scripts/viewer_tiers.py')],check=True)
info=json.loads((p/'export/export_info.json').read_text());V=p/'review/viewer'
source={'Standing':'Local RelaxIdle, fitted upright wand carry','Walking':'Completed MM6 Ogre Walking, fitted to Mage anatomy','Running':'Completed MM6 Ogre Running, fitted to Mage anatomy','Attack':'Native waist charge and wand release over ArmedCastRAttack1 body motion; impact 1.10 s','Hit':'MM6 Ogre recoil applied relative to Mage ready stance','Death':'MM6 Ogre backward fall, fitted arms and cape','Dead':'Exact final Death pose held','Fidget':'Native bend and wand inspection, fitted Mage IK'}
source['Cast']='Native alias of Attack: waist charge and wand release, separately named for the runtime spell role'
native={'Standing':'s','Walking':'w','Running':'w','Attack':'a','Cast':'a','Hit':'n','Death':'d','Dead':'x','Fidget':'f'}
m={'revision':'mm8_m540_textured_v1','default_model':'m540_a','default_clip':'Standing','model':'mm8_m540_a.glb','feedback':'feedback/user_feedback.json','models':[],'clips':{}}
for tier,label in zip('abc',['Green apprentice','Ochre mage','Crimson magi']):
 f=V/f'mm8_m540_{tier}.glb';sha=hashlib.sha256(f.read_bytes()).hexdigest();m['models'].append({'id':f'm540_{tier}','label':label,'revision':m['revision'],'url':f.name+'?v='+sha[:12],'sha256':sha})
m['model_sha256']=m['models'][0]['sha256']
for name,duration in info['clips'].items():
 frames=sorted((p/'native').glob('m540'+native[name]+'*0_541.png'))
 m['clips'][name]={'label':name,'duration':duration,'mode':'loop' if name in ['Standing','Walking','Running','Dead'] else 'once','provenance':source[name],'reference_note':'Native frames show intent; the adapted motion is not a frame trace.','anchors':[{'time':duration*i/max(1,len(frames)-1),'label':f.name,'source_images':['../../native/'+f.name]} for i,f in enumerate(frames)]}
(V/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print('VIEWER_MANIFEST',info['clips'])
