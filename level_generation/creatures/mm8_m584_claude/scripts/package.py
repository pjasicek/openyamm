"""Pack three shared native tiers, split the rigid polearm and merge the head atlas."""
import hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];R=P.parents[2]
sys.path[:0]=[str(R/'tools'),str(P.parent/'claude_shared')]
import region_variants as rv,material_classes_to_orm as orm
from merge_head_material import accessor_array
orm.TABLE[2]=(0,.72,(.65,.80),.3)
def run(*args):subprocess.run([sys.executable,*map(str,args)],cwd=R,check=True)
e=P/'export';t=P/'textures'
rv.apply_variants(e/'raven_lods.glb',e/'raven_variants.glb',t/'raven_ramps.json',[('Raven','openyamm_specular',1.0),('Raven','openyamm_specular_mask',True)])
report=orm.convert(e/'raven_variants.glb',e/'raven_materials.glb',[
 ('RavenHead',None,t/'raven_head_material_classes.png'),('RavenPolearm',t/'raven_polearm_material_classes.png',None),('Raven',t/'raven_material_classes.png',None)])
(P/'work/material_report.json').write_text(json.dumps(report,indent=2)+'\n')
run(R/'tools/split_attachment.py',e/'raven_materials.glb','--joint','Polearm','--body',e/'raven_body.glb','--attachment',e/'mm8_m584_polearm.glb')
run(R/'tools/merge_head_material.py',e/'raven_body.glb',e/'mm8_m584.glb')
checks={}
for filename,skinned in [('mm8_m584.glb',True),('mm8_m584_polearm.glb',False)]:
 d,b=rv.read_glb(e/filename);nodes={n.get('name'):i for i,n in enumerate(d['nodes'])}
 assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['raven_a','raven_b','raven_c']
 mesh=next(m for m in d['meshes'] if 'openyamm_lods' in m.get('extras',{}));assert len(mesh['extras']['openyamm_lods'])==3
 levels=[d['meshes'].index(mesh)]+mesh['extras']['openyamm_lods'];triangles=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives']) for i in levels]
 if skinned:
  assert len(d['skins'][0]['joints'])==101
  assert all(n in nodes for n in ['Body','Polearm','Wing_L_Root','Wing_R_Root','Feather_L_P00','Feather_R_P00'])
  assert len(mesh['extras']['openyamm_shadow_lods'])==4
  for m in d['meshes']:
   assert len(m['primitives'])==1
   attrs=m['primitives'][0]['attributes'];w=accessor_array(d,b,attrs['WEIGHTS_0']).sum(1)
   if 'WEIGHTS_1' in attrs:w+=accessor_array(d,b,attrs['WEIGHTS_1']).sum(1)
   assert np.max(abs(w-1))<1e-5
  durations={a['name']:max(float(accessor_array(d,b,s['input']).max()) for s in a['samplers']) for a in d['animations']}
  assert len(durations)==6 and abs(durations['Attack']-35/30)<1e-5
  assert abs(durations['Death']-1.5)<1e-5
  checks['clips']=durations
 checks[filename]={'triangles':triangles,'materials':len(d['materials']),'images':len(d['images']),'sha256':hashlib.sha256((e/filename).read_bytes()).hexdigest()}
v=P/'review/viewer';manifest=v/'manifest.json';m=json.loads(manifest.read_text());m['models']=[]
for tier,label in zip('abc',('Rook','Corbie','Raven')):
 path=v/f'raven_{tier}.glb';h=hashlib.sha256(path.read_bytes()).hexdigest()
 m['models'].append({'id':f'raven_{tier}','label':label,'revision':m['revision'],'url':f'raven_{tier}.glb?v={h[:12]}','sha256':h})
manifest.write_text(json.dumps(m,indent=2)+'\n');(P/'work/package_check.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
