"""Stage LODs, region palettes, split axe and merged head atlas with repository tools."""
import subprocess,sys,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2];E=P/'export';py=sys.executable
jobs=[['scripts/shrink_shadow_lods.py','export/mm6_min1_lods.glb','export/mm6_min1_lods_shadowfix.glb'],[str(P.parent/'claude_shared/region_variants.py'),str(E/'mm6_min1_lods_shadowfix.glb'),str(E/'mm6_min1_variants.glb'),str(P/'textures/min1_ramps.json'),'--extra','Minotaur','openyamm_specular=1','--extra','Minotaur','openyamm_specular_mask=true','--extra','Minotaur','pbr.metallicFactor=0'],[str(R/'tools/split_attachment.py'),str(E/'mm6_min1_variants.glb'),'--joint','Axe','--body',str(E/'mm6_min1.glb'),'--attachment',str(E/'mm6_min1_axe.glb')],[str(R/'tools/merge_head_material.py'),str(E/'mm6_min1.glb'),str(E/'mm6_min1.glb')],['scripts/viewer_tiers.py']]
for args in jobs:subprocess.run([py,*args],cwd=P,check=True)
M=json.loads((P/'review/runtime_metrics.json').read_text());revision='mm6_min1_codex_review_round3';models=[]
for suffix,label in [('a','Minotaur — blue'),('b','Minotaur Mage — gold'),('c','Minotaur King — red')]:
 f=P/f'review/viewer/mm6_min1_{suffix}.glb';h=hashlib.sha256(f.read_bytes()).hexdigest();models.append({'id':'min1_'+suffix,'label':label,'revision':revision,'url':f.name+'?v='+h[:12],'sha256':h})
clips={};sources={'Standing':['wkc'],'Walking':['wk'+x for x in 'abcdef'],'Running':['wk'+x for x in 'abcdef'],'Attack':['at'+x for x in 'abcde'],'Cast':['at'+x for x in 'abcde'],'Hit':['wi'+x for x in 'abcde'],'Death':['de'+x for x in 'abcde'],'Dead':['dee'],'Fidget':['fi'+x for x in 'abcdef']}
provenance={'Standing':'Local 2HandAxeIdle, native loose two-hand carry, flat soles.','Walking':'Local 2HandAxeWalk, fitted to native bull body and axe.','Running':'Fitted walk retimed to the native heavy trot.','Attack':'Mixamo Great Sword Slash (2), fixed two-hand grip, left preparation step and fitted heavy swing.','Cast':'Great Sword Slash (2) with an additional chamber hold before the spell release.','Hit':'Local 2HandAxeGetHitF1, damped upper-body recoil with both hands on shaft.','Death':'Mixamo Two Handed Sword Death; continuous backward fall, gravity-driven axe release and grounded corpse.','Dead':'Final Death pose held.','Fidget':'Local IdleAlert1 damped to native relaxed stance with both flat soles.'}
for role,m in M['clips'].items():
 src=sources[role];anchors=[]
 for i,prefix in enumerate(src):
  images=[f'../../../mm6_min1/native/min1{prefix}{v}.png' for v in range(5) if (P.parent/f'mm6_min1/native/min1{prefix}{v}.png').exists()]
  anchors.append({'time':m['duration']*i/max(1,len(src)-1),'label':prefix,'phase':'Native A palette; normalized timeline, approximate pose correspondence.','source_images':images})
 clips[role]={'label':role,'duration':m['duration'],'mode':'loop' if role in ['Standing','Walking','Running','Dead'] else 'once','provenance':provenance[role],'anchors':anchors}
manifest={'revision':revision,'model':models[0]['url'],'model_sha256':models[0]['sha256'],'default_clip':'Standing','default_model':'min1_a','feedback':'feedback/user_feedback.json','models':models,'clips':clips}
(P/'review/viewer/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
