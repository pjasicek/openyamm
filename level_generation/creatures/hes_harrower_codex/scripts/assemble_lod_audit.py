"""Audit exact runtime LOD assemblies at actor screen size, including bound attachments."""
from pathlib import Path
import copy,json,subprocess,sys,shutil,yaml,numpy as np
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'))
from merge_head_material import read_glb,write_glb,compact,accessor_array,append_accessor,TEXTURE_SLOTS,slot
PLAN={'hes_harrower':'r40_25','hes_harrower_blade_l':'r40_25','hes_harrower_blade_r':'r40_25','hes_harrower_cap_l':'r35_20','hes_harrower_cap_r':'r35_20','hes_harrower_crest':'r25_12','hes_harrower_trophies':'r25_12','hes_vreth_blade_l':'r40_25','hes_vreth_blade_r':'r40_25','hes_vreth_crest':'r25_12','hes_vreth_trophies':'r25_12'}
for stem,step in PLAN.items():
 candidate=P/'work/lod_repair'/stem/f'{step}.glb';assert candidate.is_file(),candidate
 shutil.copy(candidate,P/'export'/f'{stem}.glb')

def chain(d):
 n=next(n for n in d['nodes'] if 'mesh' in n)
 return [n['mesh'],*d['meshes'][n['mesh']]['extras']['openyamm_lods']]

def assembled(row,folder,out):
 d,b=read_glb(folder/'hes_harrower.glb');b=bytearray(b);levels=chain(d);skin=d['skins'][0]
 for item in row['attachments']:
  a,ab=read_glb(folder/Path(item['model']).name);al=chain(a);assert len(al)==len(levels)==4
  offsets={k:len(d.setdefault(k,[])) for k in ('bufferViews','accessors','images','textures','samplers','materials')}
  b.extend(b'\0'*(-len(b)%4));offset=len(b);b.extend(ab)
  for v in a['bufferViews']:
   v=copy.deepcopy(v);v['buffer']=0;v['byteOffset']=v.get('byteOffset',0)+offset;d['bufferViews'].append(v)
  for ac in a['accessors']:
   ac=copy.deepcopy(ac);ac['bufferView']+=offsets['bufferViews'];d['accessors'].append(ac)
  for im in a.get('images',[]):
   im=copy.deepcopy(im);im['bufferView']+=offsets['bufferViews'];d['images'].append(im)
  d['samplers'].extend(copy.deepcopy(a.get('samplers',[])))
  for tex in a.get('textures',[]):
   tex=copy.deepcopy(tex);tex['source']+=offsets['images']
   if 'sampler' in tex:tex['sampler']+=offsets['samplers']
   d['textures'].append(tex)
  for mat in a.get('materials',[]):
   mat=copy.deepcopy(mat)
   for key in TEXTURE_SLOTS:
    ref=slot(mat,key)
    if ref is not None:ref['index']+=offsets['textures']
   d['materials'].append(mat)
  ji=skin['joints'].index(next(i for i,n in enumerate(d['nodes']) if n.get('name')==item['node']))
  transform=np.linalg.inv(accessor_array(d,b,skin['inverseBindMatrices'])[ji].reshape(4,4).T)
  for dest,src in zip(levels,al):
   for original in a['meshes'][src]['primitives']:
    pr=copy.deepcopy(original);pr['indices']+=offsets['accessors'];pr['attributes']={k:v+offsets['accessors'] for k,v in pr['attributes'].items()};pr['material']+=offsets['materials']
    for mapping in pr.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):mapping['material']+=offsets['materials']
    pos=accessor_array(a,ab,original['attributes']['POSITION']);pos=(np.c_[pos,np.ones(len(pos))]@transform.T)[:,:3].astype(np.float32)
    normal=accessor_array(a,ab,original['attributes']['NORMAL'])@transform[:3,:3].T;normal=(normal/np.linalg.norm(normal,axis=1,keepdims=True)).astype(np.float32)
    joints=np.zeros((len(pos),4),np.uint16);joints[:,0]=ji;weights=np.zeros((len(pos),4),np.float32);weights[:,0]=1
    for key,values,kind,ctype in [('POSITION',pos,'VEC3',5126),('NORMAL',normal,'VEC3',5126),('JOINTS_0',joints,'VEC4',5123),('WEIGHTS_0',weights,'VEC4',5126)]:
     pr['attributes'][key]=append_accessor(d,b,values,{'componentType':ctype,'type':kind},34962)
    d['meshes'][dest]['primitives'].append(pr)
 variant=[v['name'] for v in d['extensions']['KHR_materials_variants']['variants']].index(row['skin'])
 for mi in levels:
  for pr in d['meshes'][mi]['primitives']:
   for mapping in pr.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):
    if variant in mapping['variants']:pr['material']=mapping['material']
 for mat in d['materials']:
  name=mat.get('name','')
  if name.startswith(('HHW_Cloth','HHW_Mantle')):
   mat['alphaMode']='MASK';mat['alphaCutoff']=.5;mat['doubleSided']=True
   if name.startswith('HHW_Mantle'):mat.setdefault('pbrMetallicRoughness',{}).setdefault('baseColorFactor',[1,1,1,1])[3]=int('_BOSS' in name)
 # Workbench does not evaluate runtime alpha factors; omit the hidden boss-only surfaces explicitly.
 for mi in levels:
  d['meshes'][mi]['primitives']=[pr for pr in d['meshes'][mi]['primitives'] if d['materials'][pr['material']].get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1])[3] != 0]
 write_glb(out,*compact(d,b))

for row in yaml.safe_load((P/'integration/actors.yml').read_text()):
 stem='assembly_'+row['skin'].removeprefix('hhw_');work=P/'work/lod_repair'/stem;work.mkdir(exist_ok=True)
 assembled(row,P/'work/lod_originals',work/'installed.glb');assembled(row,P/'export',work/'repaired.glb')
 subprocess.run([sys.executable,str(P.with_name('lod_repair_claude')/'scripts/lod_split.py'),str(work/'audit'),str(work/'installed.glb'),str(work/'repaired.glb')],check=True)
(P/'review/lod_plan.json').write_text(json.dumps({'asset_steps':PLAN,'audit':'assembled actor at engine switch screen sizes; all four bound tiers'},indent=2)+'\n')
