"""Check every exported LOD and prove attachment and animation parity."""
from pathlib import Path
import sys,json,hashlib,subprocess,yaml,numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array,image_of
from split_attachment import split_primitive
E=P/'export';names=['mm6_jak1.glb','mm6_jak1_staff.glb','mm6_jak1_body_unmerged.glb','mm6_jak1_combined.glb']
D={n:read_glb(E/n)for n in names};report={}
def arr(d,b,i):return accessor_array(d,b,i)
for name in names[:2]:
 d,b=D[name];rows=[]
 assert [v['name']for v in d['extensions']['KHR_materials_variants']['variants']]==['jak1_a','jak1_b','jak1_c']
 for m in d['meshes']:
  assert len(m['primitives'])==1
  q=m['primitives'][0];a={k:arr(d,b,i)for k,i in q['attributes'].items()};ix=arr(d,b,q['indices']).reshape(-1,3)
  assert ix.max()<len(a['POSITION']) and all(np.isfinite(v).all()for v in a.values())
  assert np.allclose(np.linalg.norm(a['NORMAL'],axis=1),1,atol=1e-5)
  count=0
  if 'WEIGHTS_0'in a:
   w=np.concatenate([v for k,v in sorted(a.items())if k.startswith('WEIGHTS')],1);j=np.concatenate([v for k,v in sorted(a.items())if k.startswith('JOINTS')],1)
   assert np.allclose(w.sum(1),1,atol=1e-5) and (w>=0).all() and j.max()<58
   count=int((w>1e-6).sum(1).max());assert count<=8  # Shared LOD builder combines influences; runtime supports eight.
  pos=a['POSITION'][ix];area2=np.linalg.norm(np.cross(pos[:,1]-pos[:,0],pos[:,2]-pos[:,0]),axis=1)
  rows.append({'name':m['name'],'triangles':len(ix),'vertices':len(a['POSITION']),'max_influences':count,'degenerate_triangles':int((area2<1e-12).sum())})
 for mat in d['materials']:
  assert mat['pbrMetallicRoughness']['metallicFactor']==0 and mat['extras']['openyamm_specular_mask']
  if name=='mm6_jak1_staff.glb':
   assert not {'openyamm_region_mask','openyamm_region_ramps'} & mat.get('extras',{}).keys()
  im,_=image_of(d,b,mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index']);red=np.asarray(im)[:,:,0];assert red.min()<30 and red.max()>120
 images=[]
 for i,im in enumerate(d['images']):
  assert 'bufferView'in im and 'uri'not in im
  ti=next(k for k,t in enumerate(d['textures'])if t['source']==i);image,_=image_of(d,b,ti);images.append({'name':im.get('name'),'size':image.size})
 report[name]={'sha256':hashlib.sha256((E/name).read_bytes()).hexdigest(),'bytes':(E/name).stat().st_size,'meshes':rows,'images':images}
s,sb=D['mm6_jak1_combined.glb'];u,ub=D['mm6_jak1_body_unmerged.glb'];d,db=D['mm6_jak1.glb'];w,wb=D['mm6_jak1_staff.glb']
assert s['nodes']==u['nodes']==d['nodes'] and s['skins'][0]['joints']==u['skins'][0]['joints']==d['skins'][0]['joints']
assert len(d['skins'][0]['joints'])==58
assert np.array_equal(arr(s,sb,s['skins'][0]['inverseBindMatrices']),arr(d,db,d['skins'][0]['inverseBindMatrices']))
clips={}
for sa,da in zip(s['animations'],d['animations']):
 assert sa['name']==da['name'] and sa['channels']==da['channels']
 for ss,ds in zip(sa['samplers'],da['samplers']):
  assert ss.get('interpolation')==ds.get('interpolation')
  for k in ['input','output']:assert np.array_equal(arr(s,sb,ss[k]),arr(d,db,ds[k]))
 clips[da['name']]=float(max(arr(d,db,ds['input']).max()for ds in da['samplers']))
assert set(clips)=={'Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget'}
slot=s['skins'][0]['joints'].index(next(i for i,n in enumerate(s['nodes'])if n.get('name')=='Staff'));inv=arr(s,sb,s['skins'][0]['inverseBindMatrices'])[slot].reshape(4,4).T;errors=[]
for mi,sm in enumerate(s['meshes']):
 out_i=0
 for sp in sm['primitives']:
  bi,wi=split_primitive(s,sb,sp,slot)
  if len(bi):
   used,reindex=np.unique(bi.ravel(),return_inverse=True);up=u['meshes'][mi]['primitives'][out_i];out_i+=1
   assert np.array_equal(reindex,arr(u,ub,up['indices']).ravel())
   for k,ai in sp['attributes'].items():assert np.array_equal(arr(s,sb,ai)[used],arr(u,ub,up['attributes'][k]))
  if len(wi) and mi<4:
   used,reindex=np.unique(wi.ravel(),return_inverse=True);wp=w['meshes'][mi]['primitives'][0];assert np.array_equal(reindex,arr(w,wb,wp['indices']).ravel())
   pos=arr(s,sb,sp['attributes']['POSITION'])[used];expected=(np.c_[pos,np.ones(len(pos))]@inv.T)[:,:3];error=float(np.max(np.abs(expected-arr(w,wb,wp['attributes']['POSITION']))));assert error<1e-6;errors.append(error)
 # Head merging concatenates the same vertex arrays; only UVs/material images change.
 for k in ['POSITION','NORMAL','JOINTS_0','WEIGHTS_0']:
  expected=np.concatenate([arr(u,ub,p['attributes'][k])for p in u['meshes'][mi]['primitives']])
  actual=arr(d,db,d['meshes'][mi]['primitives'][0]['attributes'][k]);assert np.array_equal(expected,actual),(mi,k)
report['split_equivalence']={'attachment_error_m':max(errors),'levels':len(errors),'body_geometry_skin_animation':'unchanged; head/body UVs atlased'};report['clips']=clips
# The engine rejects the complete registry for invalid materials or a spell sharing an attack clip.
result=subprocess.run([sys.executable,str(P.parents[2]/'output/codex_batch/check_weights.py'),
                       str(E/'mm6_jak1.glb'),str(E/'mm6_jak1_staff.glb')],capture_output=True,text=True,check=True)
assert 'BAD ' not in result.stdout
(P/'review/weights_check.txt').write_text(result.stdout)
blow=round(json.loads((P/'review/blow_gate.json').read_text())[0]['impact_s'],9);cast=round(json.loads((P/'review/cast_gate.json').read_text())['launch_seconds'],9)
bindings=yaml.safe_load((P/'integration/actors.yml').read_text())
assert len(bindings)==3
for binding in bindings:
 animation=binding['animation'];clips_=binding['clips'];events=animation['events']
 assert animation['cast'] not in {clips_['attack_melee'],clips_['attack_ranged']}
 assert clips_['attack_ranged']=='Attack' and events['attack_ranged']=={'impact':blow}
 assert animation['cast']=='Cast' and events['cast']=={'impact':cast,'launch_socket':'StaffTip'}
report['material_contract']='shared loader-rule validator passed; staff has no colour-region metadata'
report['bindings']='all three tiers: ranged aliases Attack; distinct Cast with StaffTip socket'
report['status']='pass';(P/'review/export_validation.json').write_text(json.dumps(report,indent=2));print('EXPORT VALIDATION PASS',report['split_equivalence'])

