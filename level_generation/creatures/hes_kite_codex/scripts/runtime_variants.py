import sys,json,copy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
g,b=R.read_glb(P/'work/ashkite_variants.glb')
idx=next(i for i,m in enumerate(g['materials']) if m.get('name')=='Static');base=g['materials'][idx];ids=[]
for k in range(3):
 m=copy.deepcopy(base);m['name']='Static_'+str(k);m['pbrMetallicRoughness']={'baseColorFactor':[.13,.09,.18,1 if k==2 else 0],'metallicFactor':0,'roughnessFactor':1};m['alphaMode']='MASK';m['alphaCutoff']=.5;m['doubleSided']=True;m['emissiveFactor']=[.68,.48,.95] if k==2 else [0,0,0];m.pop('emissiveTexture',None);m['extras']={'openyamm_bloom':True,'openyamm_specular':0};ids.append(len(g['materials']));g['materials'].append(m)
for mesh in g['meshes']:
 for prim in mesh['primitives']:
  if prim.get('material')==idx:
   prim['material']=ids[0];prim.setdefault('extensions',{})['KHR_materials_variants']={'mappings':[{'material':i,'variants':[k]} for k,i in enumerate(ids)]}
for m in g['materials']:
 if m.get('name','').startswith('Ashkite'):m['doubleSided']=True
R.write_glb(P/'work/lod_original.glb',g,b)
assert len(g['animations'])==8,len(g['animations'])
print('RUNTIME variants',len(g['animations']),'clips')
