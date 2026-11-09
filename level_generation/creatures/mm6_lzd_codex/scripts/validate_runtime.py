"""Final schema, tier, rig and geometry retention checks for the two runtime files."""
import sys,json,hashlib,io,yaml
from pathlib import Path
import numpy as np
from PIL import Image
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.path.insert(0,str(R/'tools'))
from merge_head_material import read_glb,accessor_array
from build_actor_lods import accessor_bytes
before,original=read_glb(P/'export/mm6_lzd_lod0.glb');after,binary=read_glb(P/'export/mm6_lzd.glb');bow,bowbin=read_glb(P/'export/mm6_lzd_bow.glb')
assert before['nodes']==after['nodes']
assert before['skins'][0]['joints']==after['skins'][0]['joints']
assert accessor_bytes(before,original,before['skins'][0]['inverseBindMatrices'])==accessor_bytes(after,binary,after['skins'][0]['inverseBindMatrices'])
assert [a['name']for a in before['animations']]==[a['name']for a in after['animations']]
for a,b in zip(before['animations'],after['animations']):
 assert a['channels']==b['channels']
 for x,y in zip(a['samplers'],b['samplers']):
  assert x.get('interpolation','LINEAR')==y.get('interpolation','LINEAR')
  assert y.get('interpolation','LINEAR')in ('LINEAR','STEP')
  for k in ['input','output']:assert accessor_bytes(before,original,x[k])==accessor_bytes(after,binary,y[k])
slot=before['skins'][0]['joints'].index(next(i for i,n in enumerate(before['nodes'])if n.get('name')=='Bow'))
def triangles(doc,blob,skip_bow=False):
 result=[];held=[]
 for p in doc['meshes'][0]['primitives']:
  attrs=p['attributes'];xyz=accessor_array(doc,blob,attrs['POSITION']);normal=accessor_array(doc,blob,attrs['NORMAL']);ids=accessor_array(doc,blob,p['indices']).reshape(-1,3);j=[];w=[]
  for i in [0,1]:
   j.append(accessor_array(doc,blob,attrs[f'JOINTS_{i}'])if f'JOINTS_{i}'in attrs else np.zeros((len(xyz),4)))
   w.append(accessor_array(doc,blob,attrs[f'WEIGHTS_{i}'])if f'WEIGHTS_{i}'in attrs else np.zeros((len(xyz),4)))
  j=np.concatenate(j,axis=1);w=np.concatenate(w,axis=1);v=np.concatenate([xyz,normal,j,w],axis=1)
  item=((j==slot)&(w>.999)).any(1);ismesh=item[ids].all(1)if skip_bow else np.zeros(len(ids),bool)
  held.extend(xyz[ids[ismesh]])
  result.extend(np.round(v[tri],6).astype('<f8').tobytes()for tri in ids[~ismesh])
 return sorted(result),np.array(held)
a,held=triangles(before,original,True);b,_=triangles(after,binary);assert a==b,'Body triangle attributes changed'
ibm=accessor_array(before,original,before['skins'][0]['inverseBindMatrices'])[slot].reshape(4,4).T;expected=(ibm@np.c_[held.reshape(-1,3),np.ones(held.size//3)].T).T[:,:3].reshape(-1,3,3)
actual=[]
for p in bow['meshes'][0]['primitives']:
 xyz=accessor_array(bow,bowbin,p['attributes']['POSITION']);actual.extend(xyz[accessor_array(bow,bowbin,p['indices']).reshape(-1,3)])
actual=np.array(actual);assert expected.shape==actual.shape;attachment_error=float(np.max(np.abs(expected-actual)));assert attachment_error<2e-6,attachment_error
clips={a['name']:a for a in after['animations']};assert set(clips)=={'Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'}
nodes={n['name']:i for i,n in enumerate(after['nodes'])if 'name'in n};assert nodes['Socket_Palm_R']in after['nodes'][nodes['B_R_Hand']].get('children',[])
bindings=yaml.safe_load((P/'integration/actors.yml').read_text());assert len(bindings)==3
for binding in bindings:
 animation=binding['animation'];assert animation['cast']=='Cast'and animation['cast']not in [binding['clips']['attack_melee'],binding['clips']['attack_ranged']]
 assert 'palm_right' not in animation.get('sockets',{})
 event=animation['events']['cast'];assert event['launch_socket']=='Socket_Arrow'
 duration=max(float(accessor_array(after,binary,s['input']).max())for s in clips['Cast']['samplers']);assert 0<event['impact']<=duration
 assert abs(event['impact']-json.loads((P/'review/cast_gate.json').read_text())['cast']['impact_seconds'])<1e-7
report={'distinct_cast_binding_validated':True,'clip_count':len(clips),'material_extensions_compatible':True,'rig_and_animation_bytes_preserved':True,'lod0_body_position_normal_joint_weight_triangles_identical':True,'attachment_bind_space_max_error_m':attachment_error,'files':{}}
for name,doc,blob in [('mm6_lzd.glb',after,binary),('mm6_lzd_bow.glb',bow,bowbin)]:
 assert [v['name']for v in doc['extensions']['KHR_materials_variants']['variants']]==['lzd_a','lzd_b','lzd_c']
 chain=[0]+doc['meshes'][0]['extras']['openyamm_lods'];counts=[];weights_max=0
 for k in chain:
  count=0
  for p in doc['meshes'][k]['primitives']:
   count+=doc['accessors'][p['indices']]['count']//3;xyz=accessor_array(doc,blob,p['attributes']['POSITION']);assert np.isfinite(xyz).all();ids=accessor_array(doc,blob,p['indices']);assert ids.max()<len(xyz)
   if 'WEIGHTS_0'in p['attributes']:
    w=np.concatenate([accessor_array(doc,blob,p['attributes'][s])for s in ['WEIGHTS_0','WEIGHTS_1']if s in p['attributes']],axis=1);assert np.max(abs(w.sum(1)-1))<1e-5;weights_max=max(weights_max,int((w>1e-7).sum(1).max()));assert weights_max<=8
   maps=p['extensions']['KHR_materials_variants']['mappings'];assert sorted(v for m in maps for v in m['variants'])==[0,1,2]
  counts.append(count)
 selected=json.loads((P/'review/reduction/selected.json').read_text());part='body' if name=='mm6_lzd.glb' else 'bow';assert counts==[selected[part][str(i)]['triangles']for i in range(4)]
 assert all(a>b for a,b in zip(counts,counts[1:])),counts
 caps=[12987,6485,2317,756]if part=='body'else[2236,1112,396,116]
 assert all(a<=b for a,b in zip(counts,caps)),(counts,caps)
 images=[]
 for im in doc['images']:
  assert im['mimeType']=='image/png';v=doc['bufferViews'][im['bufferView']];imdata=Image.open(io.BytesIO(blob[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]));images.append(list(imdata.size))
 for m in doc['materials']:
  assert set(m.get('extensions',{}))<={'KHR_materials_variants','KHR_materials_emissive_strength','KHR_texture_transform'},(name,m.get('name'),m.get('extensions'))
  assert m['extras']['openyamm_specular_mask']is True;assert m['extras']['openyamm_specular']==1
  assert abs(m['normalTexture'].get('scale',1)-1)<1e-6
  assert 'metallicRoughnessTexture'in m['pbrMetallicRoughness'];assert 'openyamm_region_ramps'in m['extras']
 report['files'][name]={'bytes':(P/'export'/name).stat().st_size,'sha256':hashlib.sha256((P/'export'/name).read_bytes()).hexdigest(),'triangles':counts,'max_influences':weights_max,'image_dimensions':images,'materials':len(doc['materials'])}
report['combined_triangles']=[a+b for a,b in zip(report['files']['mm6_lzd.glb']['triangles'],report['files']['mm6_lzd_bow.glb']['triangles'])]
assert all(a>b for a,b in zip(report['combined_triangles'],report['combined_triangles'][1:]))
(P/'review/runtime_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
