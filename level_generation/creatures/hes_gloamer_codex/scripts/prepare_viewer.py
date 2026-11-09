"""Build review-only baked tiers from the actual runtime body and elder attachment."""
import json,sys,subprocess,shutil,hashlib
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];V=P/'review/viewer';V.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'tools'))
from build_actor_lods import read_glb,accessor_bytes
shared=P.parent/'hes_kreegan_claude/review/viewer'
for name in ('index.html','review.js'):
 s=(shared/name).read_text().replace('Blaster Guy','Hesper Gloamers').replace('Kreegan Troopers','Hesper Gloamers');(V/name).write_text(s)
models=[];clips={}
for tier,label in [('a','Gloamling'),('b','Gloamer'),('c','Gloam Elder')]:
 ident='gloamer_'+tier;out=V/f'{ident}.glb'
 cmd=[sys.executable,str(P.parent/'hes_custodian_claude/scripts/viewer_glb.py'),str(P/'export/hes_gloamer.glb'),str(out),'--variant',ident]
 if tier=='c':cmd+=['--attach',f'{P}/export/hes_gloamer_sac.glb:ThroatSac']
 subprocess.run(cmd,check=True);d,b=read_glb(out)
 for a in d['animations']:
  times=np.frombuffer(accessor_bytes(d,b,a['samplers'][0]['input']),np.float32);role=a['name']
  clips[role]={'label':role,'duration':float(times.max()-times.min()),'mode':'loop' if role in ('Standing','Walking','Running','Dead') else 'once','provenance':'Local Mixamo Mutant source-rate motion, fitted source-frame rig and contact correction. Cast is a trimmed Roaring excerpt; Dead holds Death endpoint.','anchors':[{'time':0,'label':role,'phase':'Start','source_images':['../../references_hd/00_three_quarter.png']}]}
 sha=hashlib.sha256(out.read_bytes()).hexdigest();models.append({'id':ident,'label':label,'revision':'r5_gloamer_20261026','url':out.name+'?v='+sha[:12],'sha256':sha})
# Keep the approved pre-reduction body available for an identical-camera comparison.
before=P/'reduction_20261026/before/viewer/gloamer_b.glb'
sha=hashlib.sha256(before.read_bytes()).hexdigest()
models.append({'id':'gloamer_b_before_reduction','label':'Before reduction (11,342 tris)',
               'revision':'approved_colour_before_reduction',
               'url':'../../reduction_20261026/before/viewer/gloamer_b.glb?v='+sha[:12],'sha256':sha})
(V/'manifest.json').write_text(json.dumps({'revision':'r5_gloamer_20261026','model':'gloamer_b.glb','default_clip':'Standing','default_model':'gloamer_b','feedback':'feedback/user_feedback.json','models':models,'clips':clips},indent=2)+'\n')
assert len(models)==4 and len(clips)==9
print('VIEWER_READY',len(models),len(clips))
