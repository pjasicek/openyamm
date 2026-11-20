"""Build review-only baked variants and the shared eight-clip viewer from the actual runtime exports."""
import json,sys,subprocess,shutil,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];V=P/'review/viewer';V.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(ROOT/'tools'));from build_actor_lods import read_glb,write_glb,accessor_bytes
import numpy as np
shared=P.parent/'hes_kreegan_claude/review/viewer'
for name in ('index.html','review.js'):
 s=(shared/name).read_text().replace('Blaster Guy','Hesper Kept').replace('Kreegan Troopers','Hesper Kept');(V/name).write_text(s)
models=[];roles=('Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget');clips={}
for ident,label,stem,variant,props in [('kept_a','Kept Labourer','m_ragged','kept_a',['collar']),('kept_b','Kept Miner','m_ragged','kept_b',['collar','pick']),('kept_c','Kept Enforcer','m_enforcer','kept_c',['collar','club']),('freed_m','Freed Kept — male','m_freed',None,[]),('freed_f','Freed Kept — female','f_freed',None,[])]:
 out=V/f'{ident}.glb';cmd=[sys.executable,str(P.parent/'hes_custodian_claude/scripts/viewer_glb.py'),str(P/'export'/f'hes_kept_{stem}.glb'),str(out)]
 if variant:cmd+=['--variant',variant]
 if props:cmd+=['--attach']+[f'{P}/export/hes_kept_{p}.glb:Kept_{p.capitalize()}' for p in props]
 subprocess.run(cmd,check=True);d,b=read_glb(out);armed=ident in ('kept_b','kept_c');anims=[]
 for role in roles:
  src='Kept_ClubAttack' if ident=='kept_c' and role=='Attack' else 'Kept_'+('MaceAttack' if role=='Attack' else 'Armed'+role) if armed else 'Kept_'+role
  a=next(a for a in d['animations'] if a['name']==src);a['name']=role;anims.append(a)
  times=np.frombuffer(accessor_bytes(d,b,a['samplers'][0]['input']),np.float32);dur=float(times.max()-times.min())
  clips[role]={'label':role,'duration':round(dur,6),'mode':'loop' if role in ('Standing','Walking','Running','Dead') else 'once','provenance':'Local source-rate humanoid/Mixamo clips, fitted Kept rig; Miner Attack uses MaceAttackR3; Enforcer uses fitted MaceAttackR1 overhead.','anchors':[{'time':0,'label':role,'phase':'Start','source_images':['../../references_head/female/00_front.png' if ident=='freed_f' else '../../references_head/male/00_front.png']}]}
 d['animations']=anims;write_glb(out,d,b);sha=hashlib.sha256(out.read_bytes()).hexdigest();models.append({'id':ident,'label':label,'revision':'kept_addons_20261024','url':out.name+'?v='+sha[:12],'sha256':sha})
manifest={'revision':'kept_addons_20261024','model':'kept_a.glb','default_clip':'Standing','default_model':'kept_a','feedback':'feedback/user_feedback.json','models':models,'clips':clips}
(V/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('VIEWER_READY',len(models),len(clips))
