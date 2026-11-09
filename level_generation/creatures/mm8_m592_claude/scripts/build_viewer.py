"""Build portable previews with the exact runtime region-ramp formula."""
from pathlib import Path
import subprocess,json,hashlib,runpy
p=Path(__file__).resolve().parents[1];v=p/'review/viewer'
subprocess.run(['python3','tools/prepare_actor_glb.py',str(p/'export/mm8_m592_lod0.glb'),str(p/'export/mm8_m592_runtime_lod0.glb')],check=True)
runpy.run_path(str(p/'scripts/viewer_tiers.py'),run_name='__main__')
info=json.loads((p/'export/export_info.json').read_text())
source={'Standing':'Authored low Guardian guard and breathing','Walking':'Completed MM6 Ogre Walking, fitted to Guardian anatomy','Running':'Completed MM6 Ogre Running, fitted to Guardian anatomy','Attack':'Adapted MM6 wolfman double-claw rake: hips load back, knees bend, torso drives through both claws with a subtle side-to-side lean','Cast':'Whole-body Attack alias for the native Paralyze spell role','Hit':'Completed MM6 Ogre recoil around Guardian guard','Death':'Measured Ogre fall timing reoriented backward to the native Guardian fall; fitted arms and feet','Dead':'Exact final Death pose held','Fidget':'Native shoulder lift and jaw roar'}
native={'Standing':'s','Walking':'w','Running':'w','Attack':'a','Cast':'a','Hit':'n','Death':'d','Dead':'x','Fidget':'f'}
m={'revision':'mm8_m592_attack_v3','default_model':'m592_a','default_clip':'Standing','model':'mm8_m592_a.glb','feedback':'feedback/user_feedback.json','models':[],'clips':{}}
for tier,label in zip('abc',['Plane Guardian — gold mane','Plane Protector — green mane','Plane Overlord — red mane']):
 f=v/f'mm8_m592_{tier}.glb';sha=hashlib.sha256(f.read_bytes()).hexdigest();m['models'].append({'id':f'm592_{tier}','label':label,'revision':m['revision'],'url':f.name+'?v='+sha[:12],'sha256':sha})
m['model_sha256']=m['models'][0]['sha256']
for name,duration in info['clips'].items():
 frames=sorted((p/'native').glob('m592'+native[name]+'*0_593.png'))
 times=[duration*i/max(1,len(frames)-1) for i in range(len(frames))]
 if name in ('Attack','Cast') and len(frames)==8:times=[0,.5,.75,.875,1,1.125,1.25,1.375]
 m['clips'][name]={'label':name,'duration':duration,'mode':'loop' if name in ('Standing','Walking','Running','Dead') else 'once','provenance':source[name],'reference_note':'Native action evidence; adapted motion is not a frame trace.','anchors':[{'time':t,'label':f.name,'phase':source[name],'source_images':['../../native/'+f.name]} for t,f in zip(times,frames)]}
(v/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
f=v/'review.js';s=f.read_text().replace('MM8 Ogre Mage','MM8 Plane Guardian').replace('openyamm:mm6-ogr-claude:notes','openyamm:mm8-m592-claude:notes').replace('body:[0,0.9,0,4.8]','body:[0,1.05,0,5.8]').replace('head:[0,1.57,0,1.15]','head:[0,1.31,0.40,1.0]');f.write_text(s)
print('VIEWER',info['clips'])
