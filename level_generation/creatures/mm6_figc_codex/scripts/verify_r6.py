"""Artifact parity, hashes and existing geometry counts; no new rig gate implementation."""
import sys,json,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round6';sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array,image_of
report={}
for name in ['mm6_figc.glb','mm6_figc_axe.glb','mm6_figc_shield.glb']:
 old,ob=read_glb(R/'before/export'/name);new,nb=read_glb(P/'export'/name);counts=[]
 for om,nm in zip(old['meshes'],new['meshes']):
  for op,np_ in zip(om['primitives'],nm['primitives']):
   for k,oi in op['attributes'].items():assert np.array_equal(accessor_array(old,ob,oi),accessor_array(new,nb,np_['attributes'][k])),(name,k)
   assert np.array_equal(accessor_array(old,ob,op['indices']),accessor_array(new,nb,np_['indices']))
  counts.append(sum(new['accessors'][p['indices']]['count']//3 for p in nm['primitives']))
 assert old['nodes']==new['nodes']
 roles=[]
 for oa,na in zip(old.get('animations',[]),new.get('animations',[])):
  assert oa['name']==na['name']
  if oa['name']=='Running':
   for s in na['samplers']:
    arr=accessor_array(new,nb,s['output']);assert np.array_equal(arr[0],arr[-1]);assert abs(accessor_array(new,nb,s['input']).max()-22/30)<1e-6
   continue
  assert oa['channels']==na['channels']
  for os,ns in zip(oa['samplers'],na['samplers']):
   for k in ['input','output']:assert np.array_equal(accessor_array(old,ob,os[k]),accessor_array(new,nb,ns[k])),(name,oa['name'],k)
  roles.append(oa['name'])
 unchanged_maps=[]
 if name!='mm6_figc_shield.glb':
  for path in [('pbrMetallicRoughness','baseColorTexture'),('normalTexture',),('extras','openyamm_region_mask')]:
   def slot(d):
    x=d['materials'][0]
    for k in path:x=x[k]
    return x['index']
   assert np.array_equal(np.array(image_of(old,ob,slot(old))[0]),np.array(image_of(new,nb,slot(new))[0]));unchanged_maps.append('/'.join(path))
  for om,nm in zip(old['materials'],new['materials']):
   if 'openyamm_region_ramps' in om.get('extras',{}):assert om['extras']['openyamm_region_ramps'][:2]==nm['extras']['openyamm_region_ramps'][:2]
 entry={'triangles':counts,'all_mesh_attributes_indices_identical':True,'nodes_identical':True,'non_running_clips_byte_identical':roles,'unchanged_images':unchanged_maps}
 for label,path,d in [('before',R/'before/export'/name,old),('after',P/'export'/name,new)]:entry[label]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'images':len(d['images'])}
 report[name]=entry
for path in ['integration/actors.yml','export/mm6_figc_shield.glb']:
 assert (R/'before'/path).read_bytes()==(P/path).read_bytes();report[path]={'byte_identical':True,'sha256':hashlib.sha256((P/path).read_bytes()).hexdigest()}
for path in ['export/mm6_figc_lod0.glb','export/mm6_figc_portable.glb','export/mm6_figc_authoring.blend','review/viewer/mm6_figc_a.glb','review/viewer/mm6_figc_b.glb','review/viewer/mm6_figc_c.glb']:
 report[path]={'sha256':hashlib.sha256((P/path).read_bytes()).hexdigest(),'bytes':(P/path).stat().st_size}
(R/'artifact_parity.json').write_text(json.dumps(report,indent=2));print('PARITY PASS',json.dumps({k:v.get('triangles')for k,v in report.items()if v.get('triangles')}))
