"""Export audit: the accepted body, clips, tiers and binding must remain exact."""
import io,json,sys,hashlib,copy,numpy as np
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array,TEXTURE_SLOTS,slot as material_slot
from split_attachment import split_primitive
from normal_map_convention import measure
baseline=json.loads((P/'review/round1/baseline.json').read_text());report={'unchanged':{}}
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for path in ['export/mm6_kni.glb','integration/actors.yml','work/runtime_master.blend','work/textured_master.blend','work/production_body.blend']:
 assert digest(P/path)==baseline[path]['sha256'],path
 report['unchanged'][path]=digest(P/path)
def image_bytes(d,b,i):
 v=d['bufferViews'][d['images'][i]['bufferView']];start=v.get('byteOffset',0);return bytes(b[start:start+v['byteLength']])
def same_clips(d,b,n,nb):
 assert d['nodes']==n['nodes']
 assert d['skins'][0]['joints']==n['skins'][0]['joints']
 assert np.array_equal(accessor_array(d,b,d['skins'][0]['inverseBindMatrices']),accessor_array(n,nb,n['skins'][0]['inverseBindMatrices']))
 assert len(d['animations'])==len(n['animations'])==8
 for a,c in zip(d['animations'],n['animations']):
  assert a['name']==c['name'] and a['channels']==c['channels'] and len(a['samplers'])==len(c['samplers'])
  for s,t in zip(a['samplers'],c['samplers']):
   assert s.get('interpolation')==t.get('interpolation')
   for k in ['input','output']:assert np.array_equal(accessor_array(d,b,s[k]),accessor_array(n,nb,t[k]))
for tier in 'abc':
 d,b=read_glb(P/f'work/round1/baseline_viewer_{tier}.glb');n,nb=read_glb(P/f'review/viewer/mm6_kni_{tier}.glb');same_clips(d,b,n,nb)
 slot=d['skins'][0]['joints'].index(next(i for i,x in enumerate(d['nodes'])if x.get('name')=='Sword'))
 for old,new in zip(d['meshes'],n['meshes']):
  op=old['primitives'][0];np_=new['primitives'][0];body,_=split_primitive(d,b,op,slot);indices=accessor_array(n,nb,np_['indices']).ravel()
  assert op['attributes'].keys()==np_['attributes'].keys()
  for k,v in op['attributes'].items():assert np.array_equal(accessor_array(d,b,v)[body.ravel()],accessor_array(n,nb,np_['attributes'][k])[indices]),(tier,k)
 for old,new in zip(d['materials'],n['materials']):
  old=copy.deepcopy(old);new=copy.deepcopy(new)
  for path in TEXTURE_SLOTS:
   a=material_slot(old,path);c=material_slot(new,path)
   assert (a is None)==(c is None)
   if a is not None:
    ta=d['textures'][a['index']];tc=n['textures'][c['index']]
    assert image_bytes(d,b,ta['source'])==image_bytes(n,nb,tc['source']),(tier,path)
    assert d['samplers'][ta['sampler']]==n['samplers'][tc['sampler']]
    a['index']=c['index']=0
  assert old==new
report['viewer_body_geometry_weights_clips_tier_materials_images']='identical to baseline for all three tiers'
d,b=read_glb(P/'export/mm6_kni_sword.glb');tri=[]
assert not d.get('skins') and not d.get('animations')
assert d['meshes'][0]['extras']['openyamm_lods']==[1,2,3]
assert [v['name']for v in d['extensions']['KHR_materials_variants']['variants']]==['kni_a','kni_b','kni_c']
assert len(d['images'])==3 and len(d['materials'])==1
for m in d['meshes']:
 for q in m['primitives']:
  a={k:accessor_array(d,b,i)for k,i in q['attributes'].items()};ix=accessor_array(d,b,q['indices']).ravel()
  assert ix.size%3==0 and ix.max()<len(a['POSITION'])
  assert all(np.isfinite(v).all() and len(v)==len(a['POSITION'])for v in a.values())
  assert np.allclose(np.linalg.norm(a['NORMAL'],axis=1),1,atol=1e-5)
  assert (a['TEXCOORD_0']>=0).all() and (a['TEXCOORD_0']<=1).all()
  assert q['extensions']['KHR_materials_variants']['mappings']==[{'material':0,'variants':[0,1,2]}]
  tri.append(int(ix.size//3))
assert tri==[2292,1146,457,180]
mat=d['materials'][0];assert mat['pbrMetallicRoughness']['metallicFactor']==0 and mat['extras']['openyamm_specular_mask']
ni=d['textures'][mat['normalTexture']['index']]['source'];normal=np.array(Image.open(io.BytesIO(image_bytes(d,b,ni))).convert('RGB'));normal_corr=measure(normal);assert normal_corr>.5
mi=d['textures'][mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index']]['source'];mr=np.array(Image.open(io.BytesIO(image_bytes(d,b,mi))).convert('RGB'));assert np.array_equal(mr,np.array(Image.open(P/'textures/sword_round1/metal_rough_1k.png')))
base=d['meshes'][0]['primitives'][0];pos=accessor_array(d,b,base['attributes']['POSITION']);tip=pos[np.argmax(pos[:,1])];error=float(np.max(np.abs(tip-np.array([.18,.85,0]))));assert error<1e-6
report.update(status='pass',sword={'path':'export/mm6_kni_sword.glb','sha256':digest(P/'export/mm6_kni_sword.glb'),'bytes':(P/'export/mm6_kni_sword.glb').stat().st_size,'triangles':tri,'images':3,'materials':1,'variants':['kni_a','kni_b','kni_c'],'normal_correlation':normal_corr,'MR_specular_red_preserved':True,'native_tip_error_m':error,'static_attachment':True})
(P/'review/round1/export_validation.json').write_text(json.dumps(report,indent=2)+'\n')
(P/'review/round1/lods.json').write_text(json.dumps({'triangles':tri,'note':'Final glTF counts; Blender source LOD3 had two degenerate triangles removed at export.'},indent=2)+'\n')
print(json.dumps(report,indent=2))
