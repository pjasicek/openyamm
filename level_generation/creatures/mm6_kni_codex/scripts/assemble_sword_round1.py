"""Attach the replacement to the unchanged exported skeleton; body file is never written."""
from pathlib import Path
import sys,copy,json,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,accessor_array,append_accessor,TEXTURE_SLOTS,slot,compact
BODY=P/'export/mm6_kni.glb'
def localize(source,target):
 d,b=read_glb(source);body,bb=read_glb(BODY);joint=next(i for i,n in enumerate(body['nodes'])if n.get('name')=='Sword');js=body['skins'][0]['joints'].index(joint);inv=accessor_array(body,bb,body['skins'][0]['inverseBindMatrices'])[js].reshape(4,4).T
 w=json.loads((P/'work/weapon_fit.json').read_text());ax=np.array(w['axis_rest']);edge=np.array(w['cut_direction_rest']);flat=np.cross(ax,edge);h=np.array([[1,0,0],[0,0,1],[0,-1,0]]);r=h@np.column_stack([ax,-edge,-flat]);t=h@w['centre_rest'];transform=np.eye(4);transform[:3,:3]=r;transform[:3,3]=t;transform=inv@transform
 seen=set()
 for m in d['meshes']:
  for q in m['primitives']:
   for name in ['POSITION','NORMAL']:
    old=q['attributes'][name];key=(old,name)
    if key not in seen:
     a=accessor_array(d,b,old);v=a@transform[:3,:3].T
     if name=='POSITION':v+=transform[:3,3]
     else:v/=np.linalg.norm(v,axis=1,keepdims=True)
     new=append_accessor(d,b,v.astype(np.float32),d['accessors'][old],34962)
     for mm in d['meshes']:
      for qq in mm['primitives']:
       if qq['attributes'].get(name)==old:qq['attributes'][name]=new
     seen.add((new,name))
 # Exported static object transforms are identity, already baked in vertex coordinates.
 assert all(set(n)<= {'name','mesh','extras'}for n in d['nodes']),d['nodes']
 
 for key in ['textures','images','samplers']:d.setdefault(key,[])
 write_glb(target,*compact(d,b));return transform

def attach(base,weapon,target):
 d,b=read_glb(base);w,wb=read_glb(weapon);joint=next(i for i,n in enumerate(d['nodes'])if n.get('name')=='Sword');js=d['skins'][0]['joints'].index(joint);bind=np.linalg.inv(accessor_array(d,b,d['skins'][0]['inverseBindMatrices'])[js].reshape(4,4).T)
 # Copy only weapon images/samplers and material references; preserve all existing body data.
 viewmap={};texmap={}
 for ti,tex in enumerate(w.get('textures',[])):
  im=copy.deepcopy(w['images'][tex['source']]);v=w['bufferViews'][im['bufferView']];data=wb[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];b.extend(b'\0'*(-len(b)%4));im['bufferView']=len(d.setdefault('bufferViews',[]));d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(data)});b.extend(data);ii=len(d.setdefault('images',[]));d['images'].append(im)
  nt={'source':ii}
  if 'sampler'in tex:nt['sampler']=len(d.setdefault('samplers',[]));d['samplers'].append(copy.deepcopy(w['samplers'][tex['sampler']]))
  texmap[ti]=len(d.setdefault('textures',[]));d['textures'].append(nt)
 materials=[]
 for mat in w['materials']:
  mat=copy.deepcopy(mat)
  for path in TEXTURE_SLOTS:
   ref=slot(mat,path)
   if ref is not None:ref['index']=texmap[ref['index']]
  materials.append(len(d['materials']));d['materials'].append(mat)
 for q in w['meshes'][0]['primitives']:
  q=copy.deepcopy(q);a={k:accessor_array(w,wb,v)for k,v in q['attributes'].items()};a['POSITION']=(a['POSITION']@bind[:3,:3].T+bind[:3,3]).astype(np.float32);a['NORMAL']=a['NORMAL']@bind[:3,:3].T;a['NORMAL']=(a['NORMAL']/np.linalg.norm(a['NORMAL'],axis=1,keepdims=True)).astype(np.float32)
  attrs={k:append_accessor(d,b,v,w['accessors'][q['attributes'][k]],34962)for k,v in a.items()};weights=np.zeros((len(a['POSITION']),4),np.float32);weights[:,0]=1;joints=np.zeros(weights.shape,np.uint16);joints[:,0]=js
  attrs['JOINTS_0']=append_accessor(d,b,joints,{'componentType':5123,'type':'VEC4'},34962);attrs['WEIGHTS_0']=append_accessor(d,b,weights,{'componentType':5126,'type':'VEC4'},34962)
  q['attributes']=attrs;q['indices']=append_accessor(d,b,accessor_array(w,wb,q['indices']),w['accessors'][q['indices']],34963);q['material']=materials[q['material']]
  if 'extensions'in q:
   for mapping in q['extensions'].get('KHR_materials_variants',{}).get('mappings',[]):mapping['material']=materials[mapping['material']]
  d['meshes'][0]['primitives'].append(q)
 if 'KHR_materials_variants' in w.get('extensions',{}):
  d.setdefault('extensions',{}).setdefault('KHR_materials_variants',copy.deepcopy(w['extensions']['KHR_materials_variants']));d['extensionsUsed']=list(dict.fromkeys(d.get('extensionsUsed',[])+['KHR_materials_variants']))
 write_glb(target,d,b)
if __name__=='__main__':
 localize(P/'work/round1/sword_upload.glb',P/'work/round1/sword_local_clay.glb');attach(BODY,P/'work/round1/sword_local_clay.glb',P/'work/round1/combined_clay.glb');print('Clay sword assembled on unchanged body and Sword bone')
