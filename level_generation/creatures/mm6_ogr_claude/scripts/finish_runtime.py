"""Existing runtime post-processes: shadow fit, shared palette ramps, sword split and head atlas merge."""
from pathlib import Path
import subprocess,sys,json,hashlib
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
def run(script,*args):subprocess.run([sys.executable,str(script),*[str(a) for a in args]],check=True)
e=p/'export';t=p/'textures'
run(p/'scripts/shrink_shadow_lods.py',e/'mm6_ogr_lods.glb',e/'mm6_ogr_shadow.glb')
run(p.parent/'claude_shared/region_variants.py',e/'mm6_ogr_shadow.glb',e/'mm6_ogr.glb',t/'ogr_ramps.json','--extra','Ogre','openyamm_specular=1','--extra','Ogre','openyamm_specular_mask=true')
run(repo/'tools/split_attachment.py',e/'mm6_ogr.glb','--joint','Sword','--body',e/'mm6_ogr.glb','--attachment',e/'mm6_ogr_sword.glb')
run(repo/'tools/merge_head_material.py',e/'mm6_ogr.glb',e/'mm6_ogr.glb')
run(p/'scripts/viewer_tiers.py')
f=p/'review/viewer/manifest.json';d=json.loads(f.read_text());d['revision']='ogr_revision_03';d['default_model']='ogr_a';d['model']='mm6_ogr_a.glb';d['models']=[]
for tier,label in zip('abc',['Ogre','Ogre Raider','Ogre Chieftain']):
 name=f'mm6_ogr_{tier}.glb';h=hashlib.sha256((p/'review/viewer'/name).read_bytes()).hexdigest()
 d['models'].append({'id':f'ogr_{tier}','label':label,'revision':d['revision'],'url':name+'?v='+h[:12],'sha256':h})
d['model_sha256']=d['models'][0]['sha256'];f.write_text(json.dumps(d,indent=1)+'\n')
