"""Shared texture ramps and emissive factors on candidate LOD0; split rigid gear for the actual-mesh gates."""
import sys,json,copy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'claude_shared'))
import region_variants as rv
from embed_burn import embed_burn
src=P/'work/overseer_assembled_lod0.glb';dst=P/'work/overseer_variants_lod0.glb'
burned=P/'work/overseer_burn_lod0.glb'
embed_burn(src,burned)
rv.apply_variants(burned,dst,P/'textures/overseer_ramps.json')
d,b=rv.read_glb(dst);variants=[v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]
for mi in [i for i,m in enumerate(d['materials']) if m['name'].split('.')[0].startswith('OV_Glow')]:
 ids=[]
 for name in variants:
  m=copy.deepcopy(d['materials'][mi]);c=[1,.84,.48] if name=='ov_c' else [1,.36,.045]
  m.update(name=d['materials'][mi]['name']+'_'+name,emissiveFactor=c);m['pbrMetallicRoughness']['baseColorFactor']=[*c,1];m['pbrMetallicRoughness']['metallicFactor']=0
  assert 'emissiveTexture' not in m;ids.append(len(d['materials']));d['materials'].append(m)
 for mesh in d['meshes']:
  for prim in mesh['primitives']:
   if prim.get('material')==mi:
    prim['material']=ids[0];prim.setdefault('extensions',{})['KHR_materials_variants']={'mappings':[{'material':x,'variants':[i]} for i,x in enumerate(ids)]}
d['meshes'][0].setdefault('extras',{})['openyamm_lods']=[]
rv.write_glb(dst,d,b)
subprocess.run([sys.executable,str(P/'scripts/split_attachments.py'),str(dst),'--body',str(P/'work/overseer_body_lod0.glb'),'--items',str(P/'scripts/attachments.json'),'--outdir',str(P/'work/attachments')],check=True)
print('MATERIALS_AND_SPLIT_DONE')
