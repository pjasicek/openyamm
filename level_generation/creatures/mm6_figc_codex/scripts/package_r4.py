"""Package the two revised GLBs; preserve body motion/geometry and the shield byte-for-byte."""
import sys,json,copy,hashlib,io,shutil
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];R=P/'review/round4';E=P/'export';V=P/'review/viewer'
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,compact,accessor_array,append_accessor,add_image,image_of,slot,TEXTURE_SLOTS
KINDS=['basecolor','metal_rough','normal','region_mask']
def maps(d,b,folder):
 base=copy.deepcopy(d['materials'][:3]);indices=[]
 for kind in KINDS:indices.append(add_image(d,b,Image.open(folder/f'{kind}.png'),folder.name+'_'+kind,0))
 for mat in base:
  for path,index in zip(TEXTURE_SLOTS,indices):slot(mat,path)['index']=index
 d['materials'][:3]=base

def rebuild(d,b,prim,arrays,triangles):
 prim['attributes']={sem:append_accessor(d,b,values.astype(np.float32 if values.dtype.kind=='f' else np.uint16),{'componentType':5126 if values.dtype.kind=='f' else 5123,'type':{2:'VEC2',3:'VEC3',4:'VEC4'}[values.shape[1]]},34962) for sem,values in arrays.items()}
 prim['indices']=append_accessor(d,b,triangles.astype(np.uint32).reshape(-1,1),{'componentType':5125,'type':'SCALAR'},34963)

def body():
 d,b=read_glb(R/'before/mm6_figc.glb');base=copy.deepcopy(d['meshes'][0]['primitives'][0]);uvs=np.load(R/'body_uvs.npz')
 for level,mesh in enumerate(d['meshes']):
  for pr in mesh['primitives']:
   if level<4:
    indices=accessor_array(d,b,pr['indices']).ravel();uv=uvs[str(level)].reshape(-1,2).astype(np.float32);assert len(uv)==len(indices) and uv.min()>0 and uv.max()<1
    arrays={sem:accessor_array(d,b,index)[indices] for sem,index in pr['attributes'].items()};arrays['TEXCOORD_0']=uv
    # Weld only exactly identical corner attributes, retaining weights, positions and normals bit-for-bit.
    packed=np.concatenate([np.ascontiguousarray(value).view(np.uint8).reshape(len(value),-1) for value in arrays.values()],axis=1);_,first,inverse=np.unique(packed,axis=0,return_index=True,return_inverse=True);arrays={sem:values[first] for sem,values in arrays.items()};rebuild(d,b,pr,arrays,inverse)
   pr['material']=base['material'];pr['extensions']=copy.deepcopy(base['extensions'])
 maps(d,b,P/'textures/round4_body');write_glb(E/'mm6_figc.glb',*compact(d,b))

def axe():
 d,b=read_glb(R/'before/mm6_figc_axe.glb')
 for level,mesh in enumerate(d['meshes']):
  nd,nb=read_glb(R/f'axe_lod{level}.glb');pr=nd['meshes'][0]['primitives'][0];arrays={sem:accessor_array(nd,nb,i) for sem,i in pr['attributes'].items()};rebuild(d,b,mesh['primitives'][0],arrays,accessor_array(nd,nb,pr['indices']).ravel())
 maps(d,b,P/'textures/round4_axe');write_glb(E/'mm6_figc_axe.glb',*compact(d,b))

def bake_tier(d,b,tier):
 for mat in d['materials']:
  extra=mat.get('extras',{});regs=extra.get('openyamm_region_ramps')
  if not regs:continue
  pixels=np.array(image_of(d,b,mat['pbrMetallicRoughness']['baseColorTexture']['index'])[0].convert('RGB'),np.float32)/255
  mask=np.array(image_of(d,b,extra['openyamm_region_mask']['index'])[0].convert('RGBA'),np.float32)/255
  linear=np.where(pixels<=.04045,pixels/12.92,((pixels+.055)/1.055)**2.4);lum=linear@np.array([.2126,.7152,.0722]);out=linear.copy()
  for k,reg in enumerate(regs):
   lo,hi=reg['range'];ramp=np.array(reg['colors']);t=np.clip((lum-lo)/(hi-lo),0,1)*(len(ramp)-1);i=np.minimum(t.astype(int),len(ramp)-2);frac=(t-i)[...,None];colour=ramp[i]*(1-frac)+ramp[i+1]*frac;out=out*(1-mask[...,k:k+1])+colour*mask[...,k:k+1]
  out=np.where(out<=.0031308,out*12.92,1.055*np.maximum(out,0)**(1/2.4)-.055);im=Image.fromarray(np.uint8(np.clip(out,0,1)*255+.5));mat['pbrMetallicRoughness']['baseColorTexture']['index']=add_image(d,b,im,mat['name']+'_'+tier,0);mat.pop('extras',None)

def combine(tier=0,before=False,level=0,raw_only=False):
 base=R/'before' if before else E;d,b=read_glb(base/'mm6_figc.glb');d['meshes']=[d['meshes'][level]];body_material=d['meshes'][0]['primitives'][0]['material']+tier;d['meshes'][0].pop('extras',None)
 for name in ['axe','shield']:
  src,payload=read_glb(base/f'mm6_figc_{name}.glb');pr=copy.deepcopy(src['meshes'][level]['primitives'][0]);mi=len(d['materials']);texture_offset=len(d['textures']);image_offset=len(d['images']);sampler_offset=len(d['samplers'])
  for im in src['images']:
   im=copy.deepcopy(im);view=src['bufferViews'][im['bufferView']];start=view.get('byteOffset',0);data=payload[start:start+view['byteLength']];b.extend(b'\0'*(-len(b)%4));im['bufferView']=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(data)});b.extend(data);d['images'].append(im)
  d['samplers'].extend(copy.deepcopy(src['samplers']))
  for tex in src['textures']:
   tex=copy.deepcopy(tex);tex['source']+=image_offset
   if 'sampler' in tex:tex['sampler']+=sampler_offset
   d['textures'].append(tex)
  for mat in src['materials']:
   mat=copy.deepcopy(mat)
   for path in TEXTURE_SLOTS:
    info=slot(mat,path)
    if info:info['index']+=texture_offset
   d['materials'].append(mat)
  arrays={sem:accessor_array(src,payload,i) for sem,i in pr['attributes'].items()};rebuild(d,b,pr,arrays,accessor_array(src,payload,pr['indices']).ravel());pr['material']=mi+tier;pr.pop('extensions',None);mesh=len(d['meshes']);d['meshes'].append({'name':name.title(),'primitives':[pr]});node=len(d['nodes']);d['nodes'].append({'name':name.title()+'_visual','mesh':mesh});joint=next(n for n in d['nodes'] if n.get('name')==name.title());joint.setdefault('children',[]).append(node)
 d['meshes'][0]['primitives'][0]['material']=body_material;d['meshes'][0]['primitives'][0].pop('extensions',None)
 d,b=compact(d,b)
 if not raw_only:bake_tier(d,b,['figc_a','figc_b','figc_c'][tier]);d,b=compact(d,b)
 out=R/'accepted_combined.glb' if before else V/f'mm6_figc_{"abc"[tier]}.glb';
 if level:out=R/f'{"accepted" if before else "reduced"}_lod{level}.glb'
 if raw_only:out=R/'combined_unbaked.glb'
 write_glb(out,d,b)

def verify():
 before,bb=read_glb(R/'before/mm6_figc.glb');after,ab=read_glb(E/'mm6_figc.glb');counts=[]
 for bm,am in zip(before['meshes'],after['meshes']):
  for bp,ap in zip(bm['primitives'],am['primitives']):
   bi=accessor_array(before,bb,bp['indices']).ravel();ai=accessor_array(after,ab,ap['indices']).ravel();assert len(bi)==len(ai);counts.append(len(ai)//3)
   for sem in bp['attributes']:
    if sem=='TEXCOORD_0':continue
    assert np.array_equal(accessor_array(before,bb,bp['attributes'][sem])[bi],accessor_array(after,ab,ap['attributes'][sem])[ai]),sem
 assert before['nodes']==after['nodes'] and len(before['animations'])==len(after['animations'])
 for ba,aa in zip(before['animations'],after['animations']):
  assert ba['channels']==aa['channels']
  for bs,as_ in zip(ba['samplers'],aa['samplers']):
   for k in ['input','output']:assert np.array_equal(accessor_array(before,bb,bs[k]),accessor_array(after,ab,as_[k]))
 assert (E/'mm6_figc_shield.glb').read_bytes()==(R/'before/mm6_figc_shield.glb').read_bytes()
 assert (P/'integration/actors.yml').read_bytes()==(R/'before/actors.yml').read_bytes()
 report={'body_all_lod_geometry_weights_normals_identical':True,'animations_nodes_identical':True,'shield_file_identical':True,'actors_yml_identical':True,'body_triangles':counts}
 (R/'invariance.json').write_text(json.dumps(report,indent=2));print('INVARIANCE',report,flush=True)
def main():
 body();axe();verify();combine(before=True)
 for tier in range(3):combine(tier)
 combine(raw_only=True)
 for level in [1,2,3]:combine(level=level)
 shutil.copy2(V/'mm6_figc_a.glb',E/'mm6_figc_portable.glb')
 manifest=json.loads((V/'manifest.json').read_text());manifest['revision']='mm6_figc_codex_review4'
 for m in manifest['models']:
  f=V/f'mm6_{m["id"]}.glb';m['sha256']=hashlib.sha256(f.read_bytes()).hexdigest();m['url']=f.name+'?v='+m['sha256'][:12];m['revision']=manifest['revision']
 manifest['model_sha256']=manifest['models'][0]['sha256'];(V/'manifest.json').write_text(json.dumps(manifest,indent=2))
 summary={}
 for name in ['mm6_figc.glb','mm6_figc_axe.glb','mm6_figc_shield.glb']:
  summary[name]={}
  for label,folder in [('before',R/'before'),('after',E)]:
   path=folder/name;d,b=read_glb(path);dimensions=[image_of(d,b,i)[0].size for i in range(len(d['textures']))];summary[name][label]={'bytes':path.stat().st_size,'images':len(d['images']),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'texture_dimensions':dimensions,'rgba8_pixels_bytes':sum(w*h*4 for w,h in dimensions)}
 (R/'storage.json').write_text(json.dumps(summary,indent=2));print('PACKAGED_ROUND4',summary,flush=True)

if __name__=="__main__":main()
