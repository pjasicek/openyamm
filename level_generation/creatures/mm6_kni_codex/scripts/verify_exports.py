"""Static export audit; proves the split keeps the animation and attachment transform."""
from pathlib import Path
import json,sys,hashlib,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array,image_of
from split_attachment import split_primitive
D={n:read_glb(P/'export'/n) for n in ['mm6_kni.glb','mm6_kni_sword.glb','mm6_kni_lods_shadowfix.glb']}
def array(d,b,i):return accessor_array(d,b,i)
report={}
for name in ['mm6_kni.glb','mm6_kni_sword.glb']:
 d,b=D[name];meshes=[]
 assert [v['name']for v in d['extensions']['KHR_materials_variants']['variants']]==['kni_a','kni_b','kni_c']
 assert len(d['images'])==4
 for m in d['meshes']:
  for q in m['primitives']:
   a={k:array(d,b,i) for k,i in q['attributes'].items()};ix=array(d,b,q['indices']);assert ix.size%3==0 and ix.max()<len(a['POSITION'])
   assert all(np.isfinite(v).all() and len(v)==len(a['POSITION']) for v in a.values())
   assert np.allclose(np.linalg.norm(a['NORMAL'],axis=1),1,atol=1e-5)
   count=0
   if 'WEIGHTS_0'in a:
    w=np.concatenate([v for k,v in sorted(a.items()) if k.startswith('WEIGHTS')],axis=1);j=np.concatenate([v for k,v in sorted(a.items()) if k.startswith('JOINTS')],axis=1)
    assert (w>=0).all() and np.allclose(w.sum(axis=1),1,atol=1e-5) and j.max()<58;count=int((w>1e-6).sum(axis=1).max());assert count<=8
   meshes.append({'name':m['name'],'triangles':int(ix.size//3),'vertices':len(a['POSITION']),'max_influences':count})
 for mat in d['materials']:
  assert mat['pbrMetallicRoughness']['metallicFactor']==0 and mat['extras']['openyamm_specular_mask']
  assert len(mat['extras']['openyamm_region_ramps'])==2
 images=[{'name':im.get('name'), 'bytes':d['bufferViews'][im['bufferView']]['byteLength']}for im in d['images']]
 report[name]={'sha256':hashlib.sha256((P/'export'/name).read_bytes()).hexdigest(),'bytes':(P/'export'/name).stat().st_size,'meshes':meshes,'images':images}
s,sb=D['mm6_kni_lods_shadowfix.glb'];d,db=D['mm6_kni.glb'];w,wb=D['mm6_kni_sword.glb']
assert s['nodes']==d['nodes'] and s['skins'][0]['joints']==d['skins'][0]['joints']
assert np.array_equal(array(s,sb,s['skins'][0]['inverseBindMatrices']),array(d,db,d['skins'][0]['inverseBindMatrices']))
assert len(d['skins'][0]['joints'])==58
for sa,da in zip(s['animations'],d['animations']):
 assert sa['name']==da['name'] and sa['channels']==da['channels']
 for ss,ds in zip(sa['samplers'],da['samplers']):
  assert ss.get('interpolation')==ds.get('interpolation')
  for k in ['input','output']:assert np.array_equal(array(s,sb,ss[k]),array(d,db,ds[k]))
slot=s['skins'][0]['joints'].index(next(i for i,n in enumerate(s['nodes'])if n.get('name')=='Sword'));inv=array(s,sb,s['skins'][0]['inverseBindMatrices'])[slot].reshape(4,4).T
errors=[]
for i,(sm,dm)in enumerate(zip(s['meshes'],d['meshes'])):
 sp=sm['primitives'][0];dp=dm['primitives'][0];bi,wi=split_primitive(s,sb,sp,slot);used,reindex=np.unique(bi.ravel(),return_inverse=True)
 assert np.array_equal(reindex,array(d,db,dp['indices']).ravel())
 for k,v in sp['attributes'].items():assert np.array_equal(array(s,sb,v)[used],array(d,db,dp['attributes'][k]))
 if i<4:
  used,reindex=np.unique(wi.ravel(),return_inverse=True);wp=w['meshes'][i]['primitives'][0]
  assert np.array_equal(reindex,array(w,wb,wp['indices']).ravel())
  pos=array(s,sb,sp['attributes']['POSITION'])[used];expected=(np.c_[pos,np.ones(len(pos))]@inv.T)[:,:3];actual=array(w,wb,wp['attributes']['POSITION']);error=float(np.max(np.abs(expected-actual)));assert error<1e-6;errors.append(error)
assert {a['name']for a in d['animations']}=={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'}
report['split_equivalence']={'body_geometry_weights_animation':'identical after removing rigid Sword triangles','attachment_max_error_m':max(errors),'levels_checked':4}
report['status']='pass';(P/'review/export_validation.json').write_text(json.dumps(report,indent=2));print('Export audit PASS: all LODs, eight clips, three skins, shared images, split pose equivalence; error',max(errors))
