"""Verify the attack-only revision preserves all geometry, materials and unrelated motion."""
from pathlib import Path
import hashlib,json,struct
import numpy as np
P=Path(__file__).resolve().parents[1]
def read(path):
 b=path.read_bytes();size=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+size]),b[28+size:]
def arr(g,b,i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];off=v.get('byteOffset',0)+a.get('byteOffset',0)
 return np.ndarray((a['count'],dim),dtype=dt,buffer=b,offset=off,strides=(v.get('byteStride',dim*dt.itemsize),dt.itemsize)).copy()
def blob(g,b,i):
 v=g['bufferViews'][i];return b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
a,ab=read(P/'work/attack_revision_03_before/export/mm8_m592.glb');z,zb=read(P/'export/mm8_m592.glb')
assert a['nodes']==z['nodes']
assert a['materials']==z['materials'] and a['textures']==z['textures'] and a['extensions']==z['extensions']
for ia,iz in zip(a['images'],z['images']):assert blob(a,ab,ia['bufferView'])==blob(z,zb,iz['bufferView'])
for sa,sz in zip(a['skins'],z['skins']):
 assert sa['joints']==sz['joints'];assert np.array_equal(arr(a,ab,sa['inverseBindMatrices']),arr(z,zb,sz['inverseBindMatrices']))
geometry={}
for ma,mz in zip(a['meshes'],z['meshes']):
 assert ma['name']==mz['name'];errors={}
 for pa,pz in zip(ma['primitives'],mz['primitives']):
  assert pa['material']==pz['material'] and pa.get('extensions')==pz.get('extensions')
  for key in pa['attributes']:
   aa=arr(a,ab,pa['attributes'][key]);za=arr(z,zb,pz['attributes'][key]);assert aa.shape==za.shape;errors[key]=float(np.max(abs(aa.astype(float)-za.astype(float))));assert errors[key]==0,(ma['name'],key)
  assert np.array_equal(arr(a,ab,pa['indices']),arr(z,zb,pz['indices']))
 geometry[ma['name']]=errors
animations={};changed={}
for aa,za in zip(a['animations'],z['animations']):
 assert aa['name']==za['name'];n=aa['name'];assert aa['channels']==za['channels'];err=0
 for ch in za['channels']:
  sa=aa['samplers'][ch['sampler']];sz=za['samplers'][ch['sampler']];node=z['nodes'][ch['target']['node']]['name'];path=ch['target']['path']
  old_t=arr(a,ab,sa['input'])[:,0];new_t=arr(z,zb,sz['input'])[:,0]
  assert np.array_equal(old_t[[0,-1]],new_t[[0,-1]]),(n,'duration changed')
  old=arr(a,ab,sa['output']);new=arr(z,zb,sz['output'])
  if n in ['Attack','Cast']:
   old=np.column_stack([np.interp(new_t,old_t,old[:,i]) for i in range(old.shape[1])])
  else:
   assert np.array_equal(old_t,new_t) and old.shape==new.shape
  diff=float(np.max(abs(old-new)));err=max(err,diff)
  if n in ['Attack','Cast'] and diff>1e-5:changed.setdefault(n,{})[node+':'+path]=diff
 if n not in ['Attack','Cast']:animations[n]=err;assert err==0,(n,err)
for n in ['Attack','Cast']:
 for bone in ['B_Pelvis:translation','B_Spine1:rotation','B_L_Thigh:rotation','B_R_Thigh:rotation','B_L_Calf:rotation','B_R_Calf:rotation']:
  assert changed[n].get(bone,0)>1e-4,(n,bone,'body contribution missing')
sha=hashlib.sha256((P/'export/mm8_m592.glb').read_bytes()).hexdigest()
r={'source_sha256':sha,'geometry_uv_weights_all_lods_exactly_preserved':True,'materials_textures_bind_pose_exactly_preserved':True,'unchanged_animation_max_errors':animations,'changed_channels':changed,'all_clip_durations_preserved':True,'unchanged_clip_sample_times_preserved':True}
(P/'review/attack_revision_03/preservation.json').write_text(json.dumps(r,indent=2)+'\n')
print('PRESERVED: all geometry, materials, bind pose and seven other clips. Both attack aliases move hips, spine, thighs and knees.')
