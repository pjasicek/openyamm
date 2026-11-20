"""Four named variants, one shared texture set, skin-coloured harness and scalar emission."""
from pathlib import Path
import sys,json,copy,shutil
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(P.parent/'claude_shared'))
from merge_head_material import read_glb,write_glb,compact
import region_variants as rv
import kreegan_skin as ks
V=['hhw_a','hhw_b','hhw_c','hhw_boss'];G=[[1,.12,.008],[1,.46,.04],[1,.12,.008],[1,.55,.12]]
T=P/'textures';R=json.loads((P.with_name('hes_kreegan_claude')/'textures/hkr_ramps.json').read_text())
shutil.copy(P.with_name('hes_kreegan_claude')/'textures/hkr_body_region_mask.png',T/'hkr_body_region_mask.png')
body={};arm={}
# Retain the body painting and the harness sculpture; remap both regions to each rank's skin colour (kreegan_skin.py,
# user decision 2026-10-24: dusk red, bone ash, black, Vreth bone white) on the Trooper A skin's spread.
skin=dict(zip(V,[ks.SKIN['harrower']['a'],ks.SKIN['harrower']['b'],ks.SKIN['harrower']['c'],ks.BOSS['vreth']]))
for i,v in enumerate(V):
 src=R['materials'][0]['ramps']['hkr_'+('abc'[min(i,2)])]
 body[v]=copy.deepcopy(src)
 palette=np.array(R['materials'][0]['ramps']['hkr_a'][0]['colors'])
 colours=ks.recolour({'range':src[0]['range'],'colors':(palette**1.08).tolist()},skin[v])['colors']
 body[v][0]['colors']=colours;body[v][1]['colors']=copy.deepcopy(colours)
 arm[v]=copy.deepcopy(R['materials'][1]['ramps']['hkr_'+('abc'[min(i,2)])])
base=rv.load_srgb(T/'hkr_armour_basecolor.png');mask=np.array(Image.open(T/'hkr_armour_region_mask.png')).copy()
x,y,w,h=json.loads((P/'work/armour_layout.json').read_text())['plates']['parts_cloth']['rect']
mask[y:y+h,x:x+w,3]=255;Image.fromarray(mask,'RGBA').save(T/'hkr_armour_region_mask.png')
for i,v in enumerate(V):
 target=base*np.array([(1,1,1),(.85,.75,.9),(1.08,.72,.9),(1.08,.72,.9)][i])
 fitted,_=rv.fit_ramps(base,{v:np.clip(target,0,1)},mask[...,3]/255)
 arm[v].append(fitted[v])
config={'variants':V,'materials':[{'base':'HKR_A','prefix':'HHW_Skin','mask':'hkr_body_region_mask.png','ramps':body}]+[{'base':name,'prefix':name,'mask':'hkr_armour_region_mask.png','ramps':arm} for name in ('HHW_Plate','HHW_Mantle','HHW_Cloth')]}
(T/'hhw_ramps.json').write_text(json.dumps(config,indent=2)+'\n')
for kind in ('family','vreth'):
 src=P/'work'/('assembly_'+kind+'_lod0.glb');out=P/'work'/('assembly_'+kind+'_variants.glb')
 import subprocess
 source_doc,source_bin=read_glb(src);source_bin=bytearray(source_bin)
 from build_actor_lods import accessor_bytes,append_accessor
 native,native_bin=read_glb(P/'source/hes_kreegan.glb');nodes={n.get('name'):i for i,n in enumerate(source_doc['nodes'])};accessors={}
 source_doc['animations']=[a for a in source_doc['animations'] if a['name'].startswith('Harrower_')]
 for original in native['animations']:
  animation=copy.deepcopy(original)
  for channel in animation['channels']:
   name=native['nodes'][channel['target']['node']]['name'];channel['target']['node']=nodes['HHW' if name=='HKR' else name]
  for sampler in animation['samplers']:
   for key in ('input','output'):
    index=sampler[key]
    if index not in accessors:accessors[index]=append_accessor(source_doc,source_bin,native['accessors'][index],accessor_bytes(native,native_bin,index))
    sampler[key]=accessors[index]
  source_doc['animations'].append(animation)
 for mesh in source_doc['meshes']:
  for key in ('openyamm_lods','openyamm_shadow_lods'):mesh.get('extras',{}).pop(key,None)
 for material in source_doc['materials']:material['doubleSided']=False
 write_glb(src,source_doc,source_bin)
 subprocess.run([sys.executable,str(P.parent/'claude_shared/region_variants.py'),str(src),str(out),str(T/'hhw_ramps.json')],check=True)
 doc,b=read_glb(out)
 if 'KHR_materials_emissive_strength' not in doc.setdefault('extensionsUsed',[]):doc['extensionsUsed'].append('KHR_materials_emissive_strength')
 for base_name in ('HHW_Glow','HHW_ClothGlow','HHW_MantleGlow','Demon_Iris'):
  for bi in [i for i,m in enumerate(doc['materials']) if m.get('name','').split('.')[0]==base_name]:
   ids=[]
   for i,v in enumerate(V):
    mat=copy.deepcopy(doc['materials'][bi]);mat['name']=base_name+'_'+v.removeprefix('hhw_').upper();mat['emissiveFactor']=G[i];mat.pop('emissiveTexture',None)
    mat.setdefault('extensions',{})['KHR_materials_emissive_strength']={'emissiveStrength':.65 if base_name in ('HHW_ClothGlow','HHW_MantleGlow') else 3.5}
    mat.setdefault('extras',{})['openyamm_bloom']=base_name=='HHW_Glow'
    mat.setdefault('pbrMetallicRoughness',{}).update(baseColorFactor=[*G[i],1],metallicFactor=0)
    doc['materials'].append(mat);ids.append(len(doc['materials'])-1)
   for me in doc['meshes']:
    for pr in me['primitives']:
     if pr.get('material')==bi:pr['material']=ids[0];pr.setdefault('extensions',{})['KHR_materials_variants']={'mappings':[{'material':j,'variants':[i]} for i,j in enumerate(ids)]}
 for m in doc['materials']:
  m['alphaMode']='OPAQUE'
  assert 'emissiveTexture' not in m
  if m.get('name','').startswith('HHW_Skin'):m.setdefault('extras',{})['openyamm_specular']=0
 doc['animations'].sort(key=lambda a:(not a['name'].startswith('Harrower_'),a['name']!='Harrower_Standing',a['name']))
 write_glb(out,*compact(doc,b))
 print('VARIANTS',out.name,flush=True)
